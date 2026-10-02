// End-to-end smoke test of the production build — the checks run by hand
// before every release, now versioned so they can't drift or be skipped.
//
//   cd frontend && npm run build && npm run test:smoke
//   SMOKE_BASE_URL=https://underlaid.vercel.app npm run test:smoke   # live site
//   SMOKE_SOFTWARE_GL=1 npm run test:smoke   # force software WebGL, as on a GPU-less CI runner
//
// Exits non-zero on any FAIL or browser console error. Checks that depend
// on the external address API (BAN) are reported as SKIP — visibly, never
// as a silent pass — if that API doesn't answer.
//
// Rendering: Chromium is launched with its default flags, so it uses the
// GPU when there is one (share card in ~0.3 s). On a machine without a GPU
// (CI runners) it falls back to software WebGL, where generating the share
// card while the map keeps repainting takes 15-20 s — hence the generous
// SHARE_CARD_TIMEOUT_MS rather than a test that fails "normally" and ends
// up being ignored.
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { preview } from 'vite'
import { chromium } from 'playwright'

const SHARE_CARD_TIMEOUT_MS = 60_000
const EXPORT_TIMEOUT_MS = 30_000
const ROOT = fileURLToPath(new URL('..', import.meta.url))

// Expected /ranking length, derived from the published data with the same
// rule as RankingView.vue (score 3 or 4 out of 4, >= 50 residents) — never hardcoded.
const published = JSON.parse(readFileSync(`${ROOT}/public/data/vulnerability_score_iris.geojson`, 'utf-8'))
const EXPECTED_RANKING_ROWS = published.features.filter(
  (f) => (f.properties.cumulative_vulnerability_score ?? 0) >= 3 && (f.properties.population ?? 0) >= 50
).length

const MAP_TIMEOUT_MS = 60_000
// Same 0-4 ramp as MapView.vue's CUMULATIVE_RAMP (= DATA_RAMP_5).
const CUMULATIVE_RAMP = ['#e09ab7', '#d2668f', '#bf336a', '#980f48', '#5f002d']

// Share of map pixels whose colour is close to one of the ramp colours,
// read back from both canvases (MapLibre keeps its drawing buffer; the
// deck.gl overlay is read right after a fresh frame, as the PNG export does).
async function choroplethPixelShare(page) {
  return page.evaluate(async (ramp) => {
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
    const canvases = [...document.querySelectorAll('#map canvas')]
    const w = 200
    const h = 150
    const out = document.createElement('canvas')
    out.width = w
    out.height = h
    const ctx = out.getContext('2d', { willReadFrequently: true })
    for (const c of canvases) ctx.drawImage(c, 0, 0, w, h)
    const data = ctx.getImageData(0, 0, w, h).data
    const rgb = ramp.map((hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)))
    let hits = 0
    for (let i = 0; i < data.length; i += 4) {
      // The overlay is drawn at alpha 225/255 over the basemap: allow some blending.
      if (rgb.some(([r, g, b]) => Math.abs(data[i] - r) + Math.abs(data[i + 1] - g) + Math.abs(data[i + 2] - b) < 60)) hits++
    }
    return hits / (w * h)
  }, CUMULATIVE_RAMP)
}

const results = []
const errors = []
const record = (status, name, detail = '') => results.push({ status, name, detail })
const check = (name, condition, detail = '') => record(condition ? 'PASS' : 'FAIL', name, detail)

let server = null
let base = process.env.SMOKE_BASE_URL
if (!base) {
  server = await preview({ root: ROOT, preview: { port: 4321, strictPort: false }, logLevel: 'error' })
  base = server.resolvedUrls.local[0].replace(/\/$/, '')
}

const browser = await chromium.launch({
  args: process.env.SMOKE_SOFTWARE_GL ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [],
})
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true })
  const page = await context.newPage()
  page.on('pageerror', (e) => errors.push(`${page.url()}: ${e.message}`))
  page.on('console', (m) => m.type() === 'error' && errors.push(`${page.url()}: ${m.text()}`))

  // Home page, both languages: four findings with figures from
  // key_figures.json, the metro question answered in a live region.
  for (const [path, lang] of [['/', 'en'], ['/fr', 'fr']]) {
    await page.goto(base + path, { waitUntil: 'networkidle' })
    const findings = await page.locator('.finding').count()
    const bars = await page.locator('.finding .bars li').count()
    check(`${path} home: 4 findings, 8 bars, html lang=${lang}`, findings === 4 && bars === 8 && (await page.getAttribute('html', 'lang')) === lang, `${findings} findings, ${bars} bars`)
    await page.locator('.choices button').nth(1).click()
    check(`${path} home: question answered`, (await page.locator('.verdict').count()) === 1)
  }

  // Quiz, keyboard only: answer each question (Tab to an option, Enter),
  // the verdict appears in the live region, "next" moves focus to the
  // next question's heading; the last screen gives the result.
  await page.goto(base + '/fr/quiz', { waitUntil: 'networkidle' })
  let quizOk = true
  for (let i = 0; i < 4; i++) {
    await page.locator('.option').first().focus()
    await page.keyboard.press('Enter')
    const verdict = await page.locator('[aria-live="polite"] .verdict').count()
    await page.locator('button.next').focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(100)
    const focused = await page.evaluate(() => document.activeElement?.tagName)
    if (verdict !== 1 || focused !== 'H1') quizOk = false
  }
  const result = await page.locator('h1').innerText()
  check('quiz by keyboard: 4 verdicts, focus on each heading, result', quizOk && /sur 4/.test(result), result)

  // Home address field (combobox, keyboard only) -> map with that neighbourhood
  await page.goto(base + '/fr', { waitUntil: 'networkidle' })
  await page.locator('#home-address').fill('1 rue Marie Louise Drancy')
  const homeOption = await page.locator('#home-address-list [role="option"]').first().waitFor({ timeout: 10_000 }).then(() => true, () => false)
  if (!homeOption) {
    record('SKIP', 'home address field', 'address API (BAN) did not answer within 10 s')
  } else {
    await page.locator('#home-address').press('ArrowDown')
    const activeId = await page.locator('#home-address').getAttribute('aria-activedescendant')
    await page.locator('#home-address').press('Enter')
    await page.waitForURL(/\/fr\/address\?/)
    const rowsShown = await page.waitForSelector('.criterion-row', { timeout: 30_000 }).then(() => true, () => false)
    const rowCount = await page.locator('.criterion-row').count()
    const scoreLine = rowsShown ? await page.locator('.score-line').innerText() : ''
    check('home address -> address page: score line and 6 rows', !!activeId && rowCount === 6 && /sur 4/.test(scoreLine), `${rowCount} rows, "${scoreLine.slice(0, 60)}"`)
    // Travel mode: only access to care and transport change.
    const before = await page.locator('.criterion-row').allInnerTexts()
    await page.locator('.segmented button').nth(1).click()
    const after = await page.locator('.criterion-row').allInnerTexts()
    const changed = before.map((txt, i) => txt !== after[i])
    check('address page: step-free mode changes access to care only among scored rows', changed[4] && !changed[0] && !changed[1] && !changed[2] && !changed[3], JSON.stringify(changed))
    // Comparison with a second address.
    await page.locator('.compare .pill-btn').click()
    await page.locator('#address-other').fill('10 rue de Rivoli Paris')
    const otherOption = await page.locator('#address-other-list [role="option"]').first().waitFor({ timeout: 10_000 }).then(() => true, () => false)
    if (otherOption) {
      await page.locator('#address-other').press('ArrowDown')
      await page.locator('#address-other').press('Enter')
      await page.waitForTimeout(300)
      check('address page: comparison marker on every row with data', (await page.locator('.marker.other').count()) >= 5 && /cmp_lon/.test(page.url()))
    } else {
      record('SKIP', 'address page comparison', 'address API (BAN) did not answer within 10 s')
    }
  }

  // Map, both languages
  for (const [path, lang] of [['/map', 'en'], ['/fr/map', 'fr']]) {
    await page.goto(base + path, { waitUntil: 'networkidle' })
    // Wait for the choropleth's data, then check it is actually drawn — a
    // canvas that merely exists passed this test once while the map was
    // blank under hardware WebGL.
    const loaded = await page.waitForSelector('#map[data-choropleth-loaded="true"]', { timeout: MAP_TIMEOUT_MS }).then(() => true, () => false)
    check(`${path} choropleth data loaded`, loaded)
    const painted = await choroplethPixelShare(page)
    check(`${path} choropleth drawn`, painted > 0.05, `${(painted * 100).toFixed(1)}% of map pixels in the score ramp`)
    // Score + heat, air/noise, housing, access to care (v0.2): 5, the maximum.
    check(`${path} 5 metric pills`, (await page.locator('.toolbar .pill').count()) === 5)
    check(`${path} html lang=${lang}`, (await page.getAttribute('html', 'lang')) === lang)
    check(`${path} data date in footer`, (await page.locator('.footer-updated').count()) === 1)
  }

  // Address search -> detail panel -> share card (needs the BAN API)
  await page.fill('.search-input', '1 rue Marie Louise Drancy')
  const suggestion = page.locator('.search-suggestions button', { hasText: '93700 Drancy' }).first()
  const banAnswered = await suggestion.waitFor({ timeout: 10_000 }).then(() => true, () => false)
  if (!banAnswered) {
    record('SKIP', 'address search + panel + share card', 'address API (BAN) did not answer within 10 s')
  } else {
    await suggestion.click()
    await page.waitForSelector('.cumul-box .n', { timeout: 10_000 })
    check('search opens the detail panel, score out of 4', (await page.locator('.cumul-box .n').innerText()).endsWith('/4'))
    // Inclusive mobility (information) + other access figures, then the means block.
    check('panel: mobility + access context + means blocks', (await page.locator('.access-context').count()) === 2 && (await page.locator('.capacity-box').count()) === 1)
    const started = Date.now()
    const card = page.waitForEvent('download', { timeout: SHARE_CARD_TIMEOUT_MS }).catch(() => null)
    // Click via the DOM: under software WebGL the main thread is busy
    // repainting the map, and Playwright's actionability wait would itself
    // time out before the click is even dispatched.
    await page.evaluate(() => document.querySelector('.share-btn').click())
    const download = await card
    check('share card generated', !!download, download ? `${Date.now() - started} ms` : `none within ${SHARE_CARD_TIMEOUT_MS} ms`)
  }

  // PNG export, both map views
  for (const view of ['exposure', 'bivariate']) {
    if (view === 'bivariate') {
      await page.locator('.view-switch button').nth(1).click()
      await page.waitForSelector('.bv-cell')
      check('bivariate view: 3x3 legend, pills hidden', (await page.locator('.bv-cell').count()) === 9 && (await page.locator('.toolbar .pill').count()) === 0)
    }
    const exported = page.waitForEvent('download', { timeout: EXPORT_TIMEOUT_MS }).catch(() => null)
    await page.evaluate(() => [...document.querySelectorAll('.ghost-link')][0].click())
    check(`PNG export (${view})`, !!(await exported))
  }

  // Language switch, both directions (the FR->EN bounce was a real bug)
  await page.goto(base + '/', { waitUntil: 'networkidle' })
  await page.locator('.lang-toggle button', { hasText: 'FR' }).click()
  await page.waitForURL(/\/fr$/)
  check('EN -> FR', new URL(page.url()).pathname === '/fr')
  await page.locator('.lang-toggle button', { hasText: 'EN' }).click()
  await page.waitForURL((url) => url.pathname === '/')
  check('FR -> EN', new URL(page.url()).pathname === '/')

  // Every route by direct access
  for (const path of ['/quiz', '/fr/quiz', '/address', '/fr/address', '/methodology', '/fr/methodology', '/methodology/details', '/fr/methodology/details', '/ranking', '/fr/ranking', '/press', '/fr/press']) {
    const response = await page.goto(base + path, { waitUntil: 'networkidle' })
    check(`direct ${path}`, response.status() === 200 && (await page.locator('h1').count()) === 1)
    if (path.endsWith('ranking')) {
      const rows = await page.locator('.ranking-row').count()
      check(`${path} lists ${EXPECTED_RANKING_ROWS} neighborhoods`, rows === EXPECTED_RANKING_ROWS, `${rows} rows`)
      // Department filter, keyboard only: focus the select, pick the 3rd
      // option (93) with the arrow keys; the list shrinks and the live
      // region announces the new count.
      await page.locator('#dep-filter').focus()
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('ArrowDown')
      await page.keyboard.press('ArrowDown')
      await page.waitForTimeout(200)
      const value = await page.locator('#dep-filter').inputValue()
      const filtered = await page.locator('.ranking-row').count()
      const announced = await page.locator('#filter-count').innerText()
      const live = await page.locator('#filter-count').getAttribute('aria-live')
      check(`${path} department filter by keyboard`, value === '93' && filtered > 0 && filtered < rows && announced.includes(String(filtered)) && live === 'polite',
        `${value}: ${filtered} rows, "${announced}"`)
    }
    if (path.endsWith('methodology')) {
      // Short method page (redesign): its four sections, the worked
      // example and the distribution, all from key_figures.json.
      const sections = await page.locator('#sources, #calcul, #limites, #corrections').count()
      const distRows = await page.locator('.dist tbody tr').count()
      check(`${path} four sections, example and distribution`, sections === 4 && (await page.locator('.example .chip').count()) === 4 && distRows === 5, `${sections} sections, ${distRows} rows`)
    }
    if (path.endsWith('details')) {
      check(`${path} access + licences sections`, (await page.locator('#access').count()) === 1 && (await page.locator('#data-licences').count()) === 1)
    }
  }

  // Phone width: no sideways scroll
  const phone = await (await browser.newContext({ viewport: { width: 400, height: 860 }, isMobile: true, hasTouch: true })).newPage()
  phone.on('pageerror', (e) => errors.push(`phone ${phone.url()}: ${e.message}`))
  for (const path of ['/fr', '/fr/quiz', '/fr/address?lon=2.4431&lat=48.9248&label=Drancy', '/fr/map', '/fr/ranking', '/fr/methodology', '/fr/methodology/details']) {
    await phone.goto(base + path, { waitUntil: 'networkidle' })
    const overflow = await phone.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    check(`phone ${path}: no horizontal scroll`, overflow <= 0, overflow > 0 ? `${overflow}px` : '')
  }
} finally {
  await browser.close()
  server?.httpServer.close()
}

for (const r of results) console.log(`${r.status.padEnd(4)}  ${r.name}${r.detail ? ` — ${r.detail}` : ''}`)
console.log(errors.length ? `console errors:\n  ${errors.join('\n  ')}` : 'console errors: none')
const failed = results.filter((r) => r.status === 'FAIL').length + errors.length
console.log(`\n${results.filter((r) => r.status === 'PASS').length} passed, ${results.filter((r) => r.status === 'SKIP').length} skipped, ${failed} failed`)
process.exit(failed ? 1 : 0)
