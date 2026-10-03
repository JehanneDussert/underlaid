// Automated accessibility checks of the production build (redesign of
// October 2026, CLAUDE.md "Refonte D4"):
//   1. axe-core (WCAG 2.0/2.1 A and AA rules) on every page, desktop and
//      phone width; the run fails on any "serious" or "critical" violation
//      and lists the "moderate" and "minor" ones;
//   2. keyboard: skip link first, a visible focus ring on every stop of
//      the header, the phone menu opens with Enter and closes with Escape,
//      giving the focus back to its button; after a page change the focus
//      is on the new page's h1.
//
//   cd frontend && npm run build && npm run test:a11y
//   A11Y_BASE_URL=https://<preview> npm run test:a11y   # deployed preview
//
// Automated checks find only part of the problems (roughly a third to a
// half of WCAG failures): the manual tests listed in docs/accessibilite.md
// (screen readers, zoom, high contrast) are still needed before the
// accessibility statement can say more than "partially compliant".
import { fileURLToPath } from 'url'
import { preview } from 'vite'
import { chromium } from 'playwright'
import { AxeBuilder } from '@axe-core/playwright'
import { ROUTE_PATHS } from '../src/routePaths.js'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const BLOCKING = new Set(['serious', 'critical'])
const VIEWPORTS = {
  desktop: { width: 1280, height: 860 },
  phone: { width: 390, height: 844 },
}

let server = null
let base = process.env.A11Y_BASE_URL
if (!base) {
  server = await preview({ root: ROOT, preview: { port: 4322, strictPort: false }, logLevel: 'error' })
  base = server.resolvedUrls.local[0].replace(/\/$/, '')
}

const failures = []
const notes = []
const browser = await chromium.launch()
try {
  // 1. axe on every page and viewport.
  for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
    const context = await browser.newContext({ viewport, reducedMotion: 'reduce' })
    const page = await context.newPage()
    for (const route of ROUTE_PATHS) {
      for (const locale of ['fr', 'en']) {
        const path = route.sample ? route.sample[locale] : route[locale]
        await page.goto(base + path, { waitUntil: 'networkidle' })
        const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
        for (const v of result.violations) {
          const line = `${vpName} ${path}: [${v.impact}] ${v.id} — ${v.help} (${v.nodes.length} element${v.nodes.length > 1 ? 's' : ''}: ${v.nodes
            .slice(0, 3)
            .map((n) => n.target.join(' '))
            .join(' | ')})`
          ;(BLOCKING.has(v.impact) ? failures : notes).push(line)
        }
        console.log(`axe ${vpName} ${path}: ${result.violations.length} violation(s)`)
      }
    }
    await context.close()
  }

  // 1b. axe on interactive states of the home page.
  for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
    const context = await browser.newContext({ viewport, reducedMotion: 'reduce' })
    const page = await context.newPage()
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    if (vpName === 'desktop') {
      await page.locator('.modes-desktop .mode-wheelchair').click()
    } else {
      await page.locator('.phone-modes-button').click()
    }
    await page.locator('.question-option').first().click()
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
    for (const v of result.violations) {
      const line = `${vpName} / (mode chosen, question answered): [${v.impact}] ${v.id} — ${v.help} (${v.nodes.map((n) => n.target.join(' ')).slice(0, 3).join(' | ')})`
      ;(BLOCKING.has(v.impact) ? failures : notes).push(line)
    }
    console.log(`axe ${vpName} / interactive states: ${result.violations.length} violation(s)`)
    await context.close()
  }

  // 1c. axe on the explorer with a card and the list open, and the
  // neighbourhood page with a mode, a comparison and every need open.
  for (const [vpName, viewport] of Object.entries(VIEWPORTS)) {
    const context = await browser.newContext({ viewport, reducedMotion: 'reduce' })
    const page = await context.newPage()
    for (const [label, path, prep] of [
      ['explorer, card + list', '/carte?q=930290101&f=exposed', async () => { await page.locator('.list-toggle').click() }],
      ['neighbourhood, compare + all open', '/quartier/930290101?mode=free&compare=wheelchair', async () => { for (const b of await page.locator('.need .accordion-button').all()) await b.click() }],
    ]) {
      await page.goto(base + path, { waitUntil: 'networkidle' })
      await page.waitForTimeout(1500)
      await prep()
      const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
      for (const v of result.violations) {
        const line = `${vpName} ${label}: [${v.impact}] ${v.id} — ${v.help} (${v.nodes.map((x) => x.target.join(' ')).slice(0, 3).join(' | ')})`
        ;(BLOCKING.has(v.impact) ? failures : notes).push(line)
      }
      console.log(`axe ${vpName} ${label}: ${result.violations.length} violation(s)`)
    }
    await context.close()
  }

  // 2. Keyboard, desktop.
  {
    const context = await browser.newContext({ viewport: VIEWPORTS.desktop })
    const page = await context.newPage()
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    await page.keyboard.press('Tab')
    const first = await page.evaluate(() => document.activeElement?.className)
    if (!String(first).includes('skip-link')) failures.push(`keyboard: first Tab stop is "${first}", not the skip link`)
    // Every header stop shows a focus ring (outline at least 2 px).
    for (let i = 0; i < 4; i++) {
      await page.keyboard.press('Tab')
      const ring = await page.evaluate(() => {
        const el = document.activeElement
        const s = getComputedStyle(el)
        return { text: el.textContent.trim(), width: parseFloat(s.outlineWidth), style: s.outlineStyle }
      })
      if (!(ring.width >= 2 && ring.style !== 'none')) failures.push(`keyboard: no visible focus ring on "${ring.text}"`)
    }
    // Home: a mode and an answer chosen with the keyboard only.
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    await page.locator('.modes-desktop .mode-slow').focus()
    await page.keyboard.press('Enter')
    if ((await page.locator('.modes-desktop .mode-slow').getAttribute('aria-pressed')) !== 'true') failures.push('keyboard: Enter does not choose a travel mode')
    await page.locator('.question-option').nth(1).focus()
    await page.keyboard.press('Space')
    if ((await page.locator('.question-verdict').count()) !== 1) failures.push('keyboard: Space does not answer the question')
    await page.locator('.question-actions .pill-button').focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(100)
    if (!(await page.evaluate(() => document.activeElement?.classList.contains('question-text')))) failures.push('keyboard: after "another question" the focus is not on the new question')
    // After a page change, the focus is on the new page's h1.
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    await page.locator('#site-nav a', { hasText: 'Méthode' }).click()
    await page.waitForURL('**/methode')
    const focused = await page.evaluate(() => document.activeElement?.tagName)
    if (focused !== 'H1') failures.push(`keyboard: after a page change the focus is on ${focused}, not the h1`)
    await context.close()
  }

  // 3. Keyboard, phone menu.
  {
    const context = await browser.newContext({ viewport: VIEWPORTS.phone })
    const page = await context.newPage()
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    const button = page.locator('.menu-button')
    await button.focus()
    await page.keyboard.press('Enter')
    const expanded = await button.getAttribute('aria-expanded')
    const visible = await page.locator('#site-nav').isVisible()
    if (expanded !== 'true' || !visible) failures.push('phone menu: Enter does not open the menu')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Escape')
    const closed = (await button.getAttribute('aria-expanded')) === 'false' && !(await page.locator('#site-nav').isVisible())
    const back = await page.evaluate(() => document.activeElement?.classList.contains('menu-button'))
    if (!closed) failures.push('phone menu: Escape does not close the menu')
    if (!back) failures.push('phone menu: after Escape the focus does not return to the menu button')
    // No horizontal scroll at 320 px (reflow, WCAG 1.4.10).
    await page.setViewportSize({ width: 320, height: 700 })
    for (const path of ['/', '/methode', '/en']) {
      await page.goto(base + path, { waitUntil: 'networkidle' })
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
      if (overflow > 1) failures.push(`reflow: ${path} is ${overflow} px wider than a 320 px screen`)
    }
    await context.close()
  }
} finally {
  await browser.close()
  if (server) await new Promise((resolve) => server.httpServer.close(resolve))
}

if (notes.length) {
  console.log(`\nModerate or minor (${notes.length}):`)
  for (const n of notes) console.log('  ' + n)
}
if (failures.length) {
  console.log(`\nFAIL (${failures.length}):`)
  for (const f of failures) console.log('  ' + f)
  process.exit(1)
}
console.log('\nAccessibility checks: no serious or critical violation, keyboard checks passed.')
