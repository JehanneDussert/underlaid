// No page may scroll sideways on a phone. Checks every page (and the open
// states that change widths: filters, comparison, selected neighbourhood)
// at 320, 375 and 390 px, with Chromium and with WebKit (Safari's engine:
// a <select> there is as wide as its longest option, which once pushed the
// Explorer filters button off-screen while Chromium showed nothing).
// Fails, naming the widest element, if the document is wider than the screen.
//
//   npm run build && npm run test:overflow
import { preview } from 'vite'
import { chromium, webkit } from 'playwright'

const PATHS = [
  '/',
  '/quartier/930290101',
  '/quartier/930290101?mode=slow&compare=wheelchair',
  '/carte',
  '/carte?f=exposed,care',
  '/carte?f=exposed,resources,care&theme=resources&q=930290101',
  '/methode',
  '/methode/detail',
  '/quartiers-les-plus-exposes',
  '/a-propos',
  '/presse',
  '/lieux-du-quotidien',
  '/corrections',
  '/accessibilite',
  '/404',
  '/en',
  '/en/neighbourhood/930290101?mode=wheelchair&compare=free',
  '/en/map?f=exposed,care',
  '/en/method',
  '/en/about',
  '/en/everyday-places',
]
const WIDTHS = [320, 375, 390]

const server = await preview({ root: process.cwd(), preview: { port: 4350 }, logLevel: 'error' })
const base = server.resolvedUrls.local[0].replace(/\/$/, '')
const failures = []
let checks = 0
for (const engine of [chromium, webkit]) {
  const browser = await engine.launch()
  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, isMobile: engine === chromium, hasTouch: true })
    const page = await context.newPage()
    for (const path of PATHS) {
      await page.goto(base + path, { waitUntil: 'networkidle' })
      await page.waitForTimeout(600)
      const [over, widest] = await page.evaluate(() => {
        const over = document.documentElement.scrollWidth - window.innerWidth
        let widest = ''
        let right = 0
        if (over > 0) {
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect()
            if (r.width > 0 && r.right > right) {
              right = r.right
              widest = `${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} (right ${Math.round(r.right)})`
            }
          }
        }
        return [over, widest]
      })
      checks++
      if (over > 0) failures.push(`${engine.name()} ${width}px ${path}: ${over}px too wide — ${widest}`)
    }
    await context.close()
  }
  await browser.close()
}
server.httpServer.close()

if (failures.length) {
  console.log(`FAIL (${failures.length} of ${checks}):`)
  for (const f of failures) console.log('  ' + f)
  process.exit(1)
}
console.log(`No horizontal scrolling: ${checks} checks (2 engines × ${WIDTHS.length} widths × ${PATHS.length} pages).`)
