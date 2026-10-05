// End-to-end smoke test of the production build — the checks run by hand
// before every release, now versioned so they can't drift or be skipped.
//
//   cd frontend && npm run build && npm run test:smoke
//   SMOKE_BASE_URL=https://underlaid.fr npm run test:smoke   # live site
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
// rule as RankingView.vue (highly exposed: at least 2 of the 3 exposures in
// the most affected quarter, >= 50 residents) — never hardcoded.
const published = JSON.parse(readFileSync(`${ROOT}/public/data/vulnerability_score_iris.geojson`, 'utf-8'))
const nExposures = (p) => ['thermal', 'pollution', 'housing'].filter((k) => p[`subscore_${k}_quartile`] === 4).length
const EXPECTED_RANKING_ROWS = published.features.filter(
  (f) => nExposures(f.properties) >= 2 && (f.properties.population ?? 0) >= 50
).length

const MAP_TIMEOUT_MS = 60_000
// Same 0-4 ramp as MapView.vue's CUMULATIVE_RAMP (= DATA_RAMP_5).
const CUMULATIVE_RAMP = ['#f9c2e0', '#ee61ae', '#e4007c', '#b90066', '#8e0050']

// Share of map pixels whose colour is close to one of the ramp colours,
// read back from both canvases (MapLibre keeps its drawing buffer; the
// deck.gl overlay is read right after a fresh frame, as the PNG export does).
async function choroplethPixelShare(page) {
  return page.evaluate(async (ramp) => {
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
    const canvases = [...document.querySelectorAll('.map canvas')]
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

  // Home page, both languages (redesign D4): no duration on the plan
  // until a mode is chosen; a mode shows the six durations of
  // routes_summary.json; a second click on it hides them again; the
  // question at random is answered and its verdict written out.
  // French first: once /en is visited, a later visit to "/" returns to
  // English (the remembered choice, router.js).
  const routesSummary = JSON.parse(readFileSync(`${ROOT}/public/data/routes_summary.json`, 'utf-8'))
  for (const [path, lang] of [['/', 'fr'], ['/en', 'en']]) {
    await page.goto(base + path, { waitUntil: 'networkidle' })
    const before = await page.locator('.plan-desktop .plan-time').count()
    const wheelchair = page.locator('.modes-desktop .mode-wheelchair')
    await wheelchair.click()
    await page.waitForTimeout(400)
    const times = await page.locator('.plan-desktop .plan-time').allInnerTexts()
    const townHall = routesSummary.day_metropolis_median.wheelchair.town_hall
    const pressed = await wheelchair.getAttribute('aria-pressed')
    await wheelchair.click()
    await page.waitForTimeout(400)
    const after = await page.locator('.plan-desktop .plan-time').count()
    check(
      `${path} home: no duration without a mode, 6 with "wheelchair" (town hall ${townHall} min), none after a second click, html lang=${lang}`,
      before === 0 && times.length === 6 && times.some((x) => x.startsWith(`${townHall} `)) && pressed === 'true' && after === 0 && (await page.getAttribute('html', 'lang')) === lang,
      `${before} / ${times.join(', ')} / ${after}`
    )
    await page.locator('.question-option').first().click()
    check(`${path} home: question answered, verdict written`, (await page.locator('.question-verdict').count()) === 1)
  }

  // Everyday places: every need, three modes, medians from the summary.
  await page.goto(base + '/lieux-du-quotidien', { waitUntil: 'networkidle' })
  const placeTables = await page.locator('.need table').count()
  const townHall = routesSummary.day_metropolis_median.free.town_hall
  check(`everyday places: 9 needs, town hall ${townHall} min without constraint`, placeTables === 9 && (await page.locator('.need tr', { hasText: 'Mairie' }).first().innerText()).includes(`${townHall} min`))

  // Home address field (combobox, keyboard only) -> the neighbourhood page,
  // by its code only: no address or coordinates in the URL.
  await page.goto(base + '/', { waitUntil: 'networkidle' })
  await page.locator('#home-address').fill('1 rue Marie Louise Drancy')
  const homeOption = await page.locator('#home-address-list [role="option"]').first().waitFor({ timeout: 10_000 }).then(() => true, () => false)
  if (!homeOption) {
    record('SKIP', 'home address field', 'address API (BAN) did not answer within 10 s')
  } else {
    await page.locator('#home-address').press('ArrowDown')
    const activeId = await page.locator('#home-address').getAttribute('aria-activedescendant')
    await page.locator('#home-address').press('Enter')
    await page.waitForURL(/\/quartier\/\d{9}/, { timeout: 15_000 })
    const url = new URL(page.url())
    check('home address -> /quartier/<code>, no address in the URL', !!activeId && !/lon|lat|label|rue/i.test(url.search + url.pathname), url.pathname + url.search)
    // The menu now links back to this neighbourhood (once it is loaded).
    await page.waitForSelector('.cards', { timeout: 15_000 })
    check('menu: "Votre quartier" is a link once a neighbourhood is seen', (await page.locator('#site-nav a', { hasText: 'Votre quartier' }).count()) === 1)
  }

  // Neighbourhood page by direct access (Drancy, Économie 1): title, three
  // rank cards, nine needs; no mode = three durations per place; one mode =
  // one duration; compare = a gap; mode in the URL.
  await page.goto(base + '/quartier/930290101', { waitUntil: 'networkidle' })
  await page.waitForSelector('.cards', { timeout: 15_000 })
  const cards = await page.locator('.cards .rank-card').count()
  const needs = await page.locator('.needs .need').count()
  const threeTimes = await page.locator('.place').first().locator('.t-item').count()
  check('neighbourhood page: title, 3 cards, 9 needs, 3 durations per place without a mode', (await page.locator('h1').count()) === 1 && cards === 3 && needs === 9 && threeTimes === 3, `${cards} cards, ${needs} needs, ${threeTimes} durations`)
  await page.locator('.sticky-modes .mode-slow').click()
  await page.waitForURL(/mode=slow/)
  const oneTime = await page.locator('.place').first().locator('.t-item').count()
  await page.locator('.compare .mode-wheelchair').click()
  await page.waitForURL(/compare=wheelchair/)
  const gaps = await page.locator('.place .gap').count()
  check('neighbourhood page: one mode, then a comparison with gaps', oneTime === 0 && gaps >= 5, `${oneTime} / ${gaps} gaps`)
  const unknown = await page.goto(base + '/quartier/000000000', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  check('neighbourhood page: unknown code says so', unknown.status() === 200 && (await page.locator('.flag').count()) >= 1)

  // Explorer la carte (redesign D4), both languages: the map is drawn in
  // the theme's ramp, six themes, filters combined with AND (the count must
  // equal the one recomputed here from the published data), the card opens
  // from an address and closes with Escape, the list is the text
  // alternative with sortable columns.
  const capacity = JSON.parse(readFileSync(`${ROOT}/public/data/adaptive_capacity_iris.json`, 'utf-8'))
  const lowThird = new Set(capacity.iris.filter((r) => r.capacity_class === 0).map((r) => r.code_iris))
  const expectedFiltered = published.features.filter((f) => {
    const p = f.properties
    if ((p.population ?? 0) < 50) return false
    const n = ['thermal', 'pollution', 'housing'].filter((k) => p[`subscore_${k}_quartile`] === 4).length
    return n >= 2 && lowThird.has(p.code_iris)
  }).length
  for (const [path, lang] of [['/en/map', 'en'], ['/carte', 'fr']]) {
    await page.goto(base + path, { waitUntil: 'networkidle' })
    const loaded = await page.waitForFunction(() => !document.querySelector('.map-loading') && document.querySelector('.map canvas'), null, { timeout: MAP_TIMEOUT_MS }).then(() => true, () => false)
    await page.waitForTimeout(1500)
    check(`${path} map loaded`, loaded)
    const painted = await choroplethPixelShare(page)
    check(`${path} map drawn in the cumul ramp`, painted > 0.05, `${(painted * 100).toFixed(1)}% of map pixels`)
    check(`${path} six themes, html lang=${lang}`, (await page.locator('.themes input[type=radio]').count()) === 6 && (await page.getAttribute('html', 'lang')) === lang)
    check(`${path} data date in footer`, (await page.locator('.footer-updated').count()) === 1)
  }
  await page.locator('.theme', { hasText: 'Chaleur' }).click()
  await page.waitForURL(/theme=thermal/)
  check('explore: theme in the URL, legend follows', (await page.locator('.legend-title').innerText()) === 'Chaleur')
  await page.locator('.filter input').nth(0).check()
  await page.locator('.filter input').nth(1).check()
  await page.waitForURL(/f=exposed%2Cresources|f=exposed,resources/)
  const countText = await page.locator('.count').innerText()
  check(`explore: filters combined, count = ${expectedFiltered}`, countText.replace(/\s/g, '').startsWith(String(expectedFiltered)), countText)
  await page.locator('.list-toggle').click()
  const listRows = await page.locator('#explore-list tbody tr').count()
  await page.locator('#explore-list thead button').first().click()
  const sorted = await page.locator('#explore-list thead th').first().getAttribute('aria-sort')
  check('explore: list of the filtered neighbourhoods, sortable', listRows === Math.min(50, expectedFiltered) && sorted === 'ascending', `${listRows} rows, ${sorted}`)

  // Address -> card (needs the BAN API); Escape closes it.
  await page.goto(base + '/carte', { waitUntil: 'networkidle' })
  await page.fill('#explore-address', '1 rue Marie Louise Drancy')
  const suggestion = page.locator('#explore-address-list [role="option"]', { hasText: '93700 Drancy' }).first()
  const banAnswered = await suggestion.waitFor({ timeout: 10_000 }).then(() => true, () => false)
  if (!banAnswered) {
    record('SKIP', 'explore: address -> card', 'address API (BAN) did not answer within 10 s')
  } else {
    await suggestion.click()
    const opened = await page.waitForSelector('.card .card-title', { timeout: 10_000 }).then(() => true, () => false)
    const title = opened ? await page.locator('.card .card-title').innerText() : ''
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)
    check('explore: address opens the card, Escape closes it', /Drancy/.test(title) && (await page.locator('.card').count()) === 0, title)
  }

  // Language switch, both directions (a bounce back was a real bug):
  // French at the root, English under /en, same page in the other language.
  await page.goto(base + '/methode', { waitUntil: 'networkidle' })
  await page.locator('.nav-lang').click()
  await page.waitForURL((url) => url.pathname === '/en/method')
  check('FR -> EN (same page)', new URL(page.url()).pathname === '/en/method')
  await page.locator('.nav-lang').click()
  await page.waitForURL((url) => url.pathname === '/methode')
  check('EN -> FR (same page)', new URL(page.url()).pathname === '/methode')
  await page.goto(base + '/en', { waitUntil: 'networkidle' })
  await page.locator('.nav-lang').click()
  await page.waitForURL((url) => url.pathname === '/')
  check('EN home -> FR home stays in French', new URL(page.url()).pathname === '/' && (await page.getAttribute('html', 'lang')) === 'fr')

  // Every route by direct access
  for (const path of ['/lieux-du-quotidien', '/en/everyday-places', '/corrections', '/en/corrections', '/accessibilite', '/en/accessibility', '/en/method', '/methode', '/en/method/details', '/methode/detail', '/en/most-exposed-neighbourhoods', '/quartiers-les-plus-exposes', '/en/press', '/presse']) {
    const response = await page.goto(base + path, { waitUntil: 'networkidle' })
    check(`direct ${path}`, response.status() === 200 && (await page.locator('h1').count()) === 1)
    if (path.endsWith('exposed-neighbourhoods') || path.endsWith('les-plus-exposes')) {
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

  // Method (nine parts with a table of contents) and About (six parts,
  // citation in two formats, privacy wording) in both languages.
  for (const [path, parts] of [['/methode', 9], ['/en/method', 9], ['/a-propos', 6], ['/en/about', 6]]) {
    const r = await page.goto(base + path, { waitUntil: 'networkidle' })
    const tocLinks = await page.locator('nav.toc a').count()
    const sections = await page.locator('.parts > section.part').count()
    check(`${path}: ${parts} parts, table of contents`, r.status() === 200 && tocLinks === parts && sections === parts, `${tocLinks} links, ${sections} sections`)
  }
  await page.goto(base + '/a-propos', { waitUntil: 'networkidle' })
  await page.locator('[role=tab]', { hasText: 'BibTeX' }).click()
  check('about: BibTeX citation with the version DOI', /@software[\s\S]*10\.5281\/zenodo\.23101510/.test(await page.locator('.citation').innerText()))
  check('about: no e-mail address written in the page', !(await page.content()).includes('research.jehannedussert@'))

  // Links from before the redesign: #data-licences now lives on the
  // detailed page.
  await page.goto(base + '/methode#data-licences', { waitUntil: 'networkidle' })
  await page.waitForTimeout(300)
  check('old methodology anchor redirected to the detailed page', new URL(page.url()).pathname === '/methode/detail' && (await page.locator('#data-licences').count()) === 1, page.url())

  // The permanent redirects of the pre-redesign addresses (vercel.json)
  // match src/routePaths.js; Vercel applies them, the local preview cannot.
  const { vercelRedirects } = await import('../src/routePaths.js')
  const vercel = JSON.parse(readFileSync(`${ROOT}/vercel.json`, 'utf-8'))
  check('vercel.json redirects match routePaths.js', JSON.stringify(vercel.redirects) === JSON.stringify(vercelRedirects()))

  // Phone width: no sideways scroll
  const phone = await (await browser.newContext({ viewport: { width: 400, height: 860 }, isMobile: true, hasTouch: true })).newPage()
  phone.on('pageerror', (e) => errors.push(`phone ${phone.url()}: ${e.message}`))
  for (const path of ['/', '/quartier/930290101', '/lieux-du-quotidien', '/accessibilite', '/carte', '/quartiers-les-plus-exposes', '/methode', '/methode/detail']) {
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
