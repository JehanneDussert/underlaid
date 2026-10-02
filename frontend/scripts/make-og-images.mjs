// Generates the 1200x630 social-preview images (public/og-image.png for
// English, public/og-image-fr.png for French) and the README screenshot
// (docs/screenshot.png) and the home-page illustration (public/home-map.png)
// from the real map, so the
// preview a LinkedIn/Twitter visitor sees is the actual choropleth rather
// than a mock-up. Re-run after any scoring change that visibly moves the map:
//
//   cd frontend && node scripts/make-og-images.mjs
//
// Starts its own Vite dev server, screenshots the live #map element (the
// browser composites the MapLibre basemap and deck.gl overlay itself, so
// this sidesteps the canvas read-back race documented in MapView.vue),
// then lays that capture out next to the title/legend in a plain HTML
// card rendered at exactly 1200x630.
import { mkdirSync, writeFileSync } from 'fs'
import { dirname } from 'path'
import { fileURLToPath } from 'url'
import { createServer } from 'vite'
import { chromium } from 'playwright'

const OUT_DIR = fileURLToPath(new URL('../public/', import.meta.url))
const README_SCREENSHOT = fileURLToPath(new URL('../../docs/screenshot.png', import.meta.url))
// Same 0-4 ramp as the map's cumulative score (MapView.vue CUMULATIVE_RAMP).
const RAMP = ['#e09ab7', '#d2668f', '#bf336a', '#980f48', '#5f002d']

const COPY = {
  en: {
    file: 'og-image.png',
    path: '/map',
    tagline: 'Where environmental exposures overlap',
    body: 'Heat, air/noise pollution, housing, access to care — counted neighborhood by neighborhood across 2,752 IRIS in Paris & its inner suburbs, beside the means to cope.',
    legend: 'Categories in their worst quartile at once',
    worst: '4',
  },
  fr: {
    file: 'og-image-fr.png',
    path: '/fr/map',
    tagline: 'Là où les expositions environnementales se superposent',
    body: "Chaleur, pollution de l'air et bruit, logement, accès aux soins — comptés quartier par quartier sur 2 752 IRIS à Paris et en petite couronne, en regard des moyens des habitants.",
    legend: 'Catégories simultanément dans leur pire quartile',
    worst: '4',
  },
}

async function captureMap(page, baseUrl, path) {
  await page.goto(`${baseUrl}${path}`, { waitUntil: 'networkidle' })
  await page.waitForSelector('#deckgl-overlay')
  // Hide chrome that shouldn't appear in a social card (zoom buttons,
  // attribution — the attribution is re-stated in the card itself).
  await page.addStyleTag({
    content: '.maplibregl-ctrl-top-right, .maplibregl-ctrl-bottom-right, .maplibregl-ctrl-bottom-left { display: none !important; }',
  })
  // Let raster tiles and the choropleth settle; networkidle alone doesn't
  // cover the WebGL paint that follows the last tile response.
  await page.waitForTimeout(2500)
  const map = page.locator('#map')
  return map.screenshot({ type: 'png' })
}

function cardHtml(copy, mapPngBase64) {
  const swatches = RAMP.map(
    (c, i) => `<span class="sw"><i style="background:${c}"></i>${i === RAMP.length - 1 ? copy.worst : i}</span>`,
  ).join('')
  return `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; }
  html, body { width: 1200px; height: 630px; }
  body {
    font-family: "Space Grotesk", system-ui, sans-serif; color: #eaf0f5; overflow: hidden;
    background: radial-gradient(60% 80% at 0% 0%, rgba(34,230,214,.16), transparent 60%),
                radial-gradient(60% 80% at 100% 100%, rgba(255,61,138,.18), transparent 60%), #080a0f;
    display: grid; grid-template-columns: 470px 1fr; gap: 0;
  }
  .text { padding: 56px 36px 44px 60px; display: flex; flex-direction: column; }
  .brand { font-size: 64px; font-weight: 700; letter-spacing: -0.02em;
    background: linear-gradient(90deg, #22e6d6, #ffb020 55%, #ff3d8a); -webkit-background-clip: text; color: transparent; }
  .tagline { margin-top: 18px; font-size: 32px; font-weight: 700; line-height: 1.15; }
  .body { margin-top: 18px; font-size: 19px; line-height: 1.4; color: #b7c2cf; }
  .legend { margin-top: auto; }
  .legend p { font-size: 15px; color: #b7c2cf; margin-bottom: 10px; }
  .sws { display: flex; gap: 14px; }
  .sw { display: flex; align-items: center; gap: 6px; font-size: 17px; font-weight: 500; }
  .sw i { display: inline-block; width: 26px; height: 18px; border-radius: 4px; }
  .map { position: relative; margin: 28px 28px 28px 0; border-radius: 18px; overflow: hidden;
    border: 1px solid rgba(255,255,255,.14); box-shadow: 0 20px 60px rgba(0,0,0,.5); }
  .map img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .attr { position: absolute; right: 10px; bottom: 8px; font-size: 11px; color: #334; background: rgba(255,255,255,.75); padding: 2px 6px; border-radius: 4px; }
  .url { position: absolute; left: 12px; top: 10px; font-size: 15px; font-weight: 500; color: #080a0f; background: rgba(255,255,255,.85); padding: 4px 10px; border-radius: 999px; }
</style></head><body>
  <div class="text">
    <div class="brand">Underlaid</div>
    <div class="tagline">${copy.tagline}</div>
    <div class="body">${copy.body}</div>
    <div class="legend"><p>${copy.legend}</p><div class="sws">${swatches}</div></div>
  </div>
  <div class="map">
    <img src="data:image/png;base64,${mapPngBase64}">
    <span class="url">underlaid.vercel.app</span>
    <span class="attr">© OpenStreetMap contributors © CARTO</span>
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

  // Home page illustration (first finding): the bare choropleth, no
  // controls; the legend and the text alternative are in the page itself.
  // Same image for both languages (the basemap labels are place names).
  const homePage = await browser.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1.5 })
  writeFileSync(`${OUT_DIR}home-map.png`, await captureMap(homePage, baseUrl, '/map'))
  await homePage.close()
  console.log('wrote public/home-map.png')

  // README screenshot: the real page (map panel + side panel), English.
  // Viewport tall enough for the whole block: an element screenshot
  // larger than the viewport resizes the page mid-capture, and the WebGL
  // map doesn't repaint in time (came out as a narrow strip).
  const shot = await browser.newPage({ viewport: { width: 1440, height: 1400 }, deviceScaleFactor: 1 })
  await shot.goto(`${baseUrl}/map`, { waitUntil: 'networkidle' })
  await shot.waitForSelector('#deckgl-overlay')
  await shot.evaluate(() => {
    document.querySelector('.heatwave-banner')?.remove()
    document.querySelector('.layout').scrollIntoView()
  })
  await shot.waitForTimeout(3000)
  const box = await shot.locator('.layout').boundingBox()
  mkdirSync(dirname(README_SCREENSHOT), { recursive: true })
  await shot.screenshot({ path: README_SCREENSHOT, type: 'png', clip: { x: box.x, y: box.y, width: box.width, height: Math.min(box.height, 880) } })
  await shot.close()
  console.log('wrote docs/screenshot.png')
} finally {
  await browser.close()
  await server.close()
}
