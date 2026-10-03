// Checks that the home page's first screen fits the viewport: the plan
// never runs below the hero, the strip ends within the screen when the
// text fits, and nothing scrolls sideways — at common desktop sizes.
//
//   cd frontend && npm run build && node scripts/check-home-fit.mjs
import { fileURLToPath } from 'url'
import { preview } from 'vite'
import { chromium } from 'playwright'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const SIZES = [
  [1024, 768],
  [1280, 720],
  [1280, 860],
  [1366, 768],
  [1440, 900],
  [1536, 864],
  [1920, 1080],
  [2560, 1440],
  [1920, 1200],
]

const server = await preview({ root: ROOT, preview: { port: 4324, strictPort: false }, logLevel: 'error' })
const base = server.resolvedUrls.local[0].replace(/\/$/, '')
const browser = await chromium.launch()
let failed = 0
try {
  for (const [width, height] of SIZES) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' })
    await page.goto(base + '/', { waitUntil: 'networkidle' })
    const m = await page.evaluate(() => {
      const r = (sel) => document.querySelector(sel)?.getBoundingClientRect()
      const text = r('.hero-text')
      return {
        hero: r('.hero'),
        plan: r('.plan-desktop'),
        strip: r('.strip'),
        textBottom: text ? text.bottom : 0,
        overflowX: document.documentElement.scrollWidth - window.innerWidth,
      }
    })
    const planInHero = m.plan.bottom <= m.hero.bottom + 1
    // The strip must end on screen unless the text itself is taller.
    const textFits = m.textBottom + m.strip.height <= height
    const stripOnScreen = !textFits || m.strip.bottom <= height + 1
    const ok = planInHero && stripOnScreen && m.overflowX <= 0
    if (!ok) failed++
    console.log(
      `${ok ? 'PASS' : 'FAIL'}  ${width}x${height}: plan ${Math.round(m.plan.width)}x${Math.round(m.plan.height)}, plan bottom ${Math.round(m.plan.bottom)} / hero bottom ${Math.round(m.hero.bottom)}, strip bottom ${Math.round(m.strip.bottom)} / screen ${height}${textFits ? '' : ' (text taller than the screen)'}, sideways ${m.overflowX}px`
    )
    await page.close()
  }
} finally {
  await browser.close()
  await new Promise((resolve) => server.httpServer.close(resolve))
}
process.exit(failed ? 1 : 0)
