// Generates the 1200x630 social-preview images (public/og-image.png for
// English, public/og-image-fr.png for French) and the README screenshot
// (docs/screenshot.png) from the real map of "Explorer la carte" (redesign
// D4: white page, Atkinson Hyperlegible, the cumul ramp), so the preview a
// LinkedIn visitor sees is the actual map. Re-run after any change that
// visibly moves the map:
//
//   cd frontend && node scripts/make-og-images.mjs
//
// Starts its own Vite dev server, screenshots the live map element (the
// browser composites the WebGL canvas itself), then lays the capture out
// next to the title and legend in a plain HTML card rendered at 1200x630.
import { mkdirSync, writeFileSync } from 'fs'
import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { createServer } from 'vite'
import { chromium } from 'playwright'

const OUT_DIR = fileURLToPath(new URL('../public/', import.meta.url))
const README_SCREENSHOT = fileURLToPath(new URL('../../docs/screenshot.png', import.meta.url))
// Same 0-4 ramp as the map's cumulative score (ExploreView.vue, THEMES.cumul).
const RAMP = ['#f9c2e0', '#ee61ae', '#e4007c', '#b90066', '#8e0050']

const COPY = {
  en: {
    file: 'og-image.png',
    path: '/en/map',
    tagline: 'One city, unequal living conditions.',
    body: 'Heat, air and noise, housing, access to care: the 2,752 neighbourhoods of Paris and its inner suburbs, and what is within reach depending on how you get around.',
    legend: 'Number of themes in the most affected quarter, out of 4',
    worst: '4',
  },
  fr: {
    file: 'og-image-fr.png',
    path: '/carte',
    tagline: 'Une même ville, des conditions de vie inégales.',
    body: "Chaleur, air et bruit, logement, accès aux soins : les 2 752 quartiers de Paris et de la petite couronne, et ce qui est à portée selon votre façon de vous déplacer.",
    legend: 'Nombre de thèmes dans le quart le plus touché, sur 4',
    worst: '4',
  },
}

async function captureMap(page, baseUrl, path) {
  await page.goto(`${baseUrl}${path}`, { waitUntil: 'networkidle' })
  await page.waitForFunction(() => !document.querySelector('.map-loading') && document.querySelector('.map canvas'), null, { timeout: 60_000 })
  // Hide what shouldn't appear in a social card (controls, legend, hint):
  // the legend and the attribution are re-stated in the card itself.
  await page.addStyleTag({
    content: '.maplibregl-ctrl-bottom-right, .legend, .map-hint { display: none !important; }',
  })
  await page.waitForTimeout(2500)
  return page.locator('.map').screenshot({ type: 'png' })
}

function cardHtml(copy, mapPngBase64) {
  const swatches = RAMP.map(
    (c, i) => `<span class="sw"><i style="background:${c}"></i>${i === RAMP.length - 1 ? copy.worst : i}</span>`,
  ).join('')
  return `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; }
  html, body { width: 1200px; height: 630px; }
  body { font-family: "Atkinson Hyperlegible", system-ui, sans-serif; color: #101010; background: #fff; overflow: hidden;
    display: grid; grid-template-columns: 500px 1fr; }
  .text { padding: 56px 32px 48px 60px; display: flex; flex-direction: column; }
  .brand { font-size: 30px; font-weight: 700; }
  .tagline { margin-top: 28px; font-size: 44px; font-weight: 700; line-height: 1.06; letter-spacing: -0.02em; }
  .body { margin-top: 20px; font-size: 20px; line-height: 1.45; color: #3c3c3c; }
  .legend { margin-top: auto; }
  .legend p { font-size: 15px; color: #3c3c3c; margin-bottom: 10px; }
  .sws { display: flex; gap: 6px; }
  .sw { display: flex; flex-direction: column; gap: 6px; font-size: 15px; }
  .sw i { display: inline-block; width: 64px; height: 14px; border-radius: 4px; }
  .map { position: relative; margin: 24px 24px 24px 0; overflow: hidden; }
  .map img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .attr { position: absolute; right: 8px; bottom: 6px; font-size: 11px; color: #3c3c3c; background: rgba(255,255,255,.85); padding: 2px 6px; border-radius: 4px; }
  .url { position: absolute; left: 10px; top: 8px; font-size: 15px; font-weight: 700; background: rgba(255,255,255,.9); padding: 4px 12px; border-radius: 999px; border: 1.5px solid #e2e2e2; }
</style></head><body>
  <div class="text">
    <div class="brand">underlaid</div>
    <div class="tagline">${copy.tagline}</div>
    <div class="body">${copy.body}</div>
    <div class="legend"><p>${copy.legend}</p><div class="sws">${swatches}</div></div>
  </div>
  <div class="map">
    <img src="data:image/png;base64,${mapPngBase64}">
    <span class="url">underlaid.vercel.app</span>
    <span class="attr">INSEE, IGN · © OpenStreetMap</span>
  </div>
</body></html>`
}

const server = await createServer({
  root: fileURLToPath(new URL('..', import.meta.url)),
  server: { port: 5199, strictPort: true },
  logLevel: 'error',
})
await server.listen()
const baseUrl = 'http://localhost:5199'
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] })
try {
  for (const [locale, copy] of Object.entries(COPY)) {
    const mapPage = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 })
    const mapPng = await captureMap(mapPage, baseUrl, copy.path)
    await mapPage.close()

    const card = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 })
    await card.setContent(cardHtml(copy, mapPng.toString('base64')), { waitUntil: 'networkidle' })
    await card.evaluate(() => document.fonts.ready)
    writeFileSync(`${OUT_DIR}${copy.file}`, await card.screenshot({ type: 'png' }))
    await card.close()
    console.log(`${locale}: wrote public/${copy.file}`)
  }

  // README screenshot: the real page (panel and map), French.
  const shot = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })
  await shot.goto(`${baseUrl}/carte`, { waitUntil: 'networkidle' })
  await shot.waitForFunction(() => !document.querySelector('.map-loading') && document.querySelector('.map canvas'), null, { timeout: 60_000 })
  await shot.waitForTimeout(3000)
  mkdirSync(dirname(README_SCREENSHOT), { recursive: true })
  await shot.screenshot({ path: README_SCREENSHOT, type: 'png' })
  await shot.close()
  console.log('wrote docs/screenshot.png')
} finally {
  await browser.close()
  await server.close()
}
