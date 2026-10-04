// Sharing images (1200 x 630) in the site's identity: the curved lines of
// the home-page plan, the page title, the site name. One fixed image per
// main page (home, Explorer, Method, About), French and English; and, for
// "Votre quartier", the template of an image per neighbourhood (name,
// commune, exposure pills; never an address).
//
// Drafts for review first (decision of 4 October 2026: images shown before
// they are used):
//   cd frontend && OUT=<folder> node scripts/make-share-images.mjs
// Without OUT, writes public/share/<page>-<lang>.png.
import { mkdirSync, readFileSync, writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { chromium } from 'playwright'

const OUT = process.env.OUT || fileURLToPath(new URL('../public/share/', import.meta.url))
const font = (w) =>
  readFileSync(fileURLToPath(new URL(`../node_modules/@fontsource/atkinson-hyperlegible/files/atkinson-hyperlegible-latin-${w}-normal.woff2`, import.meta.url))).toString('base64')
const FONT_CSS = `@font-face{font-family:A;font-weight:400;src:url(data:font/woff2;base64,${font(400)}) format('woff2')}
@font-face{font-family:A;font-weight:700;src:url(data:font/woff2;base64,${font(700)}) format('woff2')}`

// Lines and stations of the home plan (NetworkPlan.vue), same frame.
const LINES = [
  ['M580 220 C 780 200, 860 260, 940 380 C 1020 500, 1120 640, 1320 620', '#0057B8'],
  ['M700 820 C 780 660, 860 560, 980 520 C 1100 480, 1200 470, 1320 380', '#E4007C'],
  ['M1160 40 C 1140 200, 1080 300, 980 400 C 880 500, 780 560, 620 520', '#00A06B'],
  ['M820 30 C 840 180, 920 260, 1030 290 C 1140 320, 1240 300, 1320 250', '#FF7A00'],
  ['M590 620 C 740 640, 860 700, 940 760 C 1020 820, 1080 860, 1120 860', '#7B3FA0'],
]
const STATIONS = [[1167, 463], [881, 192], [1172, 302], [1103, 566], [736, 654], [787, 524]]
const HERE = [975, 430]

function plan(view) {
  const lines = LINES.map(([d, c]) => `<path d="${d}" stroke="${c}" />`).join('')
  const st = STATIONS.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="13" />`).join('')
  return `<svg viewBox="${view}" preserveAspectRatio="xMidYMid slice" class="plan">
    <defs><linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".25" stop-color="#fff"/></linearGradient>
    <mask id="m" maskUnits="userSpaceOnUse" x="500" y="0" width="900" height="900"><rect x="560" y="0" width="760" height="900" fill="url(#f)"/></mask></defs>
    <g fill="none" stroke-width="14" stroke-linecap="round" mask="url(#m)">${lines}</g>
    <g fill="#fff" stroke="#101010" stroke-width="5">${st}</g>
    <circle cx="${HERE[0]}" cy="${HERE[1]}" r="12" fill="#fff" stroke="#101010" stroke-width="4"/><circle cx="${HERE[0]}" cy="${HERE[1]}" r="5" fill="#101010"/>
  </svg>`
}

const page = (body, extraCss = '') => `<!doctype html><html><head><meta charset="utf-8"><style>
${FONT_CSS}
*{box-sizing:border-box}html,body{margin:0}
body{width:1200px;height:630px;overflow:hidden;background:#fff;color:#101010;font-family:A,sans-serif;position:relative}
.plan{position:absolute;right:-40px;top:0;width:640px;height:630px}
.text{position:absolute;left:72px;top:72px;width:600px}
.kicker{font-size:24px;font-weight:700;color:#3C3C3C;margin:0 0 18px}
h1{font-size:60px;line-height:1.05;letter-spacing:-.02em;margin:0 0 22px}
.lead{font-size:26px;line-height:1.4;color:#3C3C3C;margin:0}
.brand{position:absolute;left:72px;bottom:56px;font-size:30px;font-weight:700;display:flex;gap:16px;align-items:baseline}
.brand span{font-size:22px;font-weight:400;color:#3C3C3C}
${extraCss}</style></head><body>${body}</body></html>`

const FIXED = {
  fr: {
    accueil: ['', 'Une même ville, des conditions de vie inégales.', 'Chaleur, pollution, logement, accès aux soins et aux services, quartier par quartier, à Paris et en petite couronne.'],
    carte: ['Explorer la carte', 'Les 2 752 quartiers de Paris et de la petite couronne', 'Chaleur, air et bruit, logement, accès aux soins, ressources des habitants, et leur cumul.'],
    methode: ['Sources et méthode', 'Comment les quartiers sont comparés', 'Données publiques, calculs, hypothèses testées, limites et corrections.'],
    apropos: ['À propos', 'Un projet ouvert et indépendant', 'Qui porte Underlaid, comment le citer, réutiliser ses données et son code.'],
  },
  en: {
    accueil: ['', 'One city, unequal living conditions.', 'Heat, pollution, housing, access to care and services, neighbourhood by neighbourhood, in Paris and its inner suburbs.'],
    carte: ['Explore the map', 'The 2,752 neighbourhoods of Paris and its inner suburbs', 'Heat, air and noise, housing, access to care, residents’ resources, and where they combine.'],
    methode: ['Sources and method', 'How neighbourhoods are compared', 'Open data, calculations, tested hypotheses, limits and corrections.'],
    apropos: ['About', 'An open, independent project', 'Who runs Underlaid, how to cite it, reuse its data and code.'],
  },
}
const BRAND = { fr: 'Paris et petite couronne', en: 'Paris and its inner suburbs' }

function fixedCard(lang, [kicker, title, lead]) {
  return page(`${plan('560 88 720 712')}<div class="text">${kicker ? `<p class="kicker">${kicker}</p>` : ''}<h1>${title}</h1><p class="lead">${lead}</p></div>
  <div class="brand">underlaid.fr<span>${BRAND[lang]}</span></div>`)
}

// Neighbourhood template: name, commune, pills of the exposures in the most
// affected quarter (pink, as on the page), or a neutral line if none.
const PILL = {
  fr: { thermal: 'Chaleur', pollution: 'Air et bruit', housing: 'Logements énergivores', access_care: 'Accès aux soins difficile', note: 'Dans le quart le plus touché des 2 752 quartiers', none: 'Hors du quart le plus touché pour la chaleur, l’air et le bruit, le logement', kicker: 'Votre quartier' },
  en: { thermal: 'Heat', pollution: 'Air and noise', housing: 'Energy-inefficient housing', access_care: 'Difficult access to care', note: 'In the most affected quarter of the 2,752 neighbourhoods', none: 'Outside the most affected quarter for heat, air and noise, housing', kicker: 'Your neighbourhood' },
}
function hoodCard(lang, name, commune, pills) {
  const p = PILL[lang]
  const list = pills.length
    ? `<p class="note">${p.note}</p><div class="pills">${pills.map((k) => `<span class="pill"><i></i>${p[k]}</span>`).join('')}</div>`
    : `<p class="note">${p.none}</p>`
  return page(`${plan('560 88 720 712')}<div class="text"><p class="kicker">${p.kicker}</p><h1>${name}</h1><p class="commune">${commune}</p>${list}</div>
  <div class="brand">underlaid.fr<span>${BRAND[lang]}</span></div>`,
  `.commune{font-size:30px;margin:0 0 30px;color:#3C3C3C}.note{font-size:22px;color:#3C3C3C;margin:0 0 14px}
   .pills{display:flex;flex-wrap:wrap;gap:12px;width:620px}.pill{display:inline-flex;align-items:center;gap:12px;background:#FCE4F1;border-radius:999px;padding:10px 20px;font-size:24px}
   .pill i{width:14px;height:14px;border-radius:50%;background:#E4007C}`)
}

mkdirSync(OUT, { recursive: true })
const browser = await chromium.launch()
const tab = await browser.newPage({ viewport: { width: 1200, height: 630 } })
async function shoot(html, file) {
  await tab.setContent(html, { waitUntil: 'load' })
  await tab.evaluate(() => document.fonts.ready)
  writeFileSync(`${OUT}/${file}`, await tab.screenshot({ type: 'png' }))
  console.log('wrote', file)
}
for (const lang of ['fr', 'en']) {
  for (const [key, copy] of Object.entries(FIXED[lang])) await shoot(fixedCard(lang, copy), `${key}-${lang}.png`)
}
if (process.env.OUT) {
  await shoot(hoodCard('fr', 'Économie 1', 'Drancy', ['thermal', 'pollution', 'housing']), 'quartier-exemple-1-fr.png')
  await shoot(hoodCard('fr', 'Batignolles 14', 'Paris 17e', ['pollution']), 'quartier-exemple-2-fr.png')
  await shoot(hoodCard('fr', 'Saint-Fargeau 8', 'Paris 20e', []), 'quartier-exemple-3-fr.png')
}
await browser.close()
