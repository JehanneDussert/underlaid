// Every prerendered page carries its sharing and indexing tags (decision of
// 4 October 2026, block 5): a title, a meta description, an Open Graph and a
// Twitter image, a canonical address and the French / English alternates.
// Main pages must have distinct titles. Reads dist/ (run after the build):
//
//   npm run build && npm run test:seo
import { readdirSync, readFileSync, statSync } from 'fs'
import { join, relative } from 'path'
import { fileURLToPath } from 'url'

const DIST = fileURLToPath(new URL('../dist/', import.meta.url))
const files = []
const walk = (dir) => {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f)
    if (statSync(p).isDirectory()) {
      if (f !== 'assets' && f !== 'data' && f !== 'share') walk(p)
    } else if (f.endsWith('.html')) files.push(p)
  }
}
walk(DIST)

const get = (html, re) => (html.match(re) || [])[1]
const failures = []
const titles = new Map()
let neighbourhoods = 0
for (const file of files) {
  const rel = relative(DIST, file).replace(/\\/g, '/')
  if (rel === '404.html' || rel === 'en/404.html') continue
  const html = readFileSync(file, 'utf-8')
  const checks = {
    title: get(html, /<title>([^<]+)<\/title>/),
    description: get(html, /<meta name="description" content="([^"]+)"/),
    'og:image': get(html, /<meta property="og:image" content="([^"]+)"/),
    'twitter:image': get(html, /<meta name="twitter:image" content="([^"]+)"/),
    canonical: get(html, /<link rel="canonical" href="([^"]+)"/),
    'hreflang fr': get(html, /hreflang="fr" href="([^"]+)"/),
    'hreflang en': get(html, /hreflang="en" href="([^"]+)"/),
  }
  for (const [k, v] of Object.entries(checks)) if (!v) failures.push(`${rel}: no ${k}`)
  const isNeighbourhood = /^(quartier|en\/neighbourhood)\/\d+\.html$/.test(rel)
  if (isNeighbourhood) neighbourhoods++
  else if (checks.title) {
    if (titles.has(checks.title)) failures.push(`${rel}: same title as ${titles.get(checks.title)} ("${checks.title}")`)
    titles.set(checks.title, rel)
  }
}
if (failures.length) {
  console.log(`FAIL (${failures.length}):`)
  for (const f of failures.slice(0, 40)) console.log('  ' + f)
  process.exit(1)
}
console.log(`Sharing and indexing tags present on ${files.length - 1} pages (${neighbourhoods} neighbourhood pages); main page titles distinct.`)
