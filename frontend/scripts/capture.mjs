// Screenshots of the build for comparison with the mock-ups
// (docs/design/refonte-d4/png/), one step of the redesign at a time.
//
//   cd frontend && npm run build && node scripts/capture.mjs <out-dir> <spec.json>
//
// spec.json: [{ "name": "header-desktop", "path": "/methode",
//   "width": 1280, "height": 860, "fullPage": false,
//   "actions": [{ "click": ".menu-button" }], "clip": "footer" }]
// `clip` is a CSS selector: only that element is captured.
import { readFileSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { preview } from 'vite'
import { chromium } from 'playwright'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const [outDir, specFile] = process.argv.slice(2)
const specs = JSON.parse(readFileSync(specFile, 'utf-8'))
mkdirSync(outDir, { recursive: true })

const server = await preview({ root: ROOT, preview: { port: 4323, strictPort: false }, logLevel: 'error' })
const base = server.resolvedUrls.local[0].replace(/\/$/, '')
const browser = await chromium.launch()
try {
  for (const s of specs) {
    const context = await browser.newContext({ viewport: { width: s.width, height: s.height }, deviceScaleFactor: 2, reducedMotion: s.reducedMotion ? 'reduce' : 'no-preference' })
    const page = await context.newPage()
    await page.goto(base + s.path, { waitUntil: 'networkidle' })
    await page.evaluate(() => document.fonts.ready)
    for (const a of s.actions || []) {
      if (a.click) await page.locator(a.click).first().click()
      if (a.wait) await page.waitForTimeout(a.wait)
    }
    const file = `${outDir}/${s.name}.png`
    if (s.clip) await page.locator(s.clip).first().screenshot({ path: file })
    else await page.screenshot({ path: file, fullPage: !!s.fullPage })
    console.log(file)
    await context.close()
  }
} finally {
  await browser.close()
  await new Promise((resolve) => server.httpServer.close(resolve))
}
