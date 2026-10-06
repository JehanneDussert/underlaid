import { readdirSync, readFileSync, writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { ROUTE_PATHS, paramRewrites, shellPath } from './src/routePaths.js'
import { DEFAULT_SITE_URL } from './src/siteUrl.js'

// Single source of truth for the production domain — shared with the
// frontend via the `define` below (see composables/useSeoMeta.js) and
// with the sitemap/robots generator in the seoFilesPlugin below, so
// there's never a second copy to fall out of sync. Override with
// SITE_URL=... at build time (e.g. a fork deployed elsewhere) — no
// trailing slash. The default lives in src/siteUrl.js.
const SITE_URL = (process.env.SITE_URL || DEFAULT_SITE_URL).replace(/\/+$/, '')

// Only the production deployment may be indexed. On Vercel, preview
// deployments (any branch other than master, e.g. the redesign branch)
// get VERCEL_ENV=preview: every page then carries <meta name="robots"
// content="noindex, nofollow"> and robots.txt disallows everything — on
// top of the X-Robots-Tag: noindex header Vercel adds to previews itself.
// A local build (no VERCEL_ENV) is indexable, as before, so the dist/
// checks keep testing the production output.
const NOINDEX = Boolean(process.env.VERCEL_ENV) && process.env.VERCEL_ENV !== 'production'

// Read at config-eval time (Node, not the browser) so the /ranking page's
// meta description can state the real neighborhood count without either
// hardcoding a number that drifts every time the scoring pipeline re-runs,
// or depending on an async fetch that a static prerender pass can't easily
// wait on for something as small as a page description.
function countRankingNeighborhoods() {
  try {
    const path = fileURLToPath(new URL('./public/data/vulnerability_score_iris.geojson', import.meta.url))
    const geojson = JSON.parse(readFileSync(path, 'utf-8'))
    // Same rule as RankingView.vue: highly exposed = at least 2 of the 3
    // exposures (heat, air and noise, housing) in the most affected quarter,
    // IRIS with at least 50 residents (smaller ones stay on the map only).
    const n = (p) => ['thermal', 'pollution', 'housing'].filter((k) => p[`subscore_${k}_quartile`] === 4).length
    return geojson.features.filter((f) => n(f.properties) >= 2 && (f.properties.population ?? 0) >= 50).length
  } catch {
    return 0
  }
}

// Every neighbourhood gets its own prerendered page in both languages
// (decision of 5 October 2026), so that sharing a neighbourhood shows its
// name; codes read from the published per-commune files (script 39).
// Inhabited ones (>= 50 residents) go into the sitemap.
function neighbourhoodCodes() {
  try {
    const dir = fileURLToPath(new URL('./public/data/quartiers/', import.meta.url))
    const all = []
    const inhabited = []
    for (const f of readdirSync(dir)) {
      if (!/^\d+\.json$/.test(f)) continue
      for (const r of JSON.parse(readFileSync(`${dir}${f}`, 'utf-8')).iris) {
        all.push(r.code)
        if (r.inhabited) inhabited.push(r.code)
      }
    }
    return { all, inhabited }
  } catch {
    return { all: [], inhabited: [] }
  }
}
const NEIGHBOURHOODS = neighbourhoodCodes()

function dataDate() {
  try {
    const path = fileURLToPath(new URL('./public/data/last_updated.json', import.meta.url))
    return JSON.parse(readFileSync(path, 'utf-8')).generated_at.slice(0, 10)
  } catch {
    return null
  }
}
const NBHD = ROUTE_PATHS.find((r) => r.name === 'neighbourhood')
const nbhdPath = (pattern, code) => pattern.replace(':code?', code)

// Generates a standard multilingual sitemap.xml (one <url> per language
// per route, each carrying its own reciprocal hreflang alternates) and
// robots.txt after the production build writes its output — the same
// URL structure the frontend itself uses for canonical/hreflang tags
// (see useSeoMeta.js), so the two can't silently disagree with each other.
function seoFilesPlugin() {
  return {
    name: 'underlaid-seo-files',
    apply: 'build',
    writeBundle(options) {
      const urls = ROUTE_PATHS.filter((r) => r.sitemap !== false).flatMap((r) =>
        [r.fr, r.en].map(
          (path) => `  <url>
    <loc>${SITE_URL}${path}</loc>
    <xhtml:link rel="alternate" hreflang="fr" href="${SITE_URL}${r.fr}"/>
    <xhtml:link rel="alternate" hreflang="en" href="${SITE_URL}${r.en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}${r.fr}"/>
  </url>`
        )
      )
      for (const code of NEIGHBOURHOODS.inhabited) {
        const fr = nbhdPath(NBHD.fr, code)
        const en = nbhdPath(NBHD.en, code)
        for (const path of [fr, en]) {
          urls.push(`  <url>
    <loc>${SITE_URL}${path}</loc>
    <xhtml:link rel="alternate" hreflang="fr" href="${SITE_URL}${fr}"/>
    <xhtml:link rel="alternate" hreflang="en" href="${SITE_URL}${en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}${fr}"/>
  </url>`)
        }
      }
      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join('\n')}
</urlset>
`
      writeFileSync(`${options.dir}/sitemap.xml`, xml)
      writeFileSync(`${options.dir}/robots.txt`, NOINDEX ? `User-agent: *
Disallow: /
` : `User-agent: *
Allow: /

Sitemap: ${SITE_URL}/sitemap.xml
`)
    },
  }
}

// The local preview (smoke and accessibility tests) applies the same
// rewrites as vercel.json: /quartier/<code> -> the prerendered shell.
function previewRewritesPlugin() {
  const rules = paramRewrites().map((r) => ({ prefix: r.source.replace(/:[^/]+$/, ''), to: `${r.destination}.html` }))
  return {
    name: 'underlaid-preview-rewrites',
    configurePreviewServer(server) {
      server.middlewares.use((req, _res, next) => {
        const rule = rules.find((r) => req.url.startsWith(r.prefix) && req.url.length > r.prefix.length)
        if (rule) req.url = rule.to
        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), seoFilesPlugin(), previewRewritesPlugin()],
  ssgOptions: {
    // Pages with an optional parameter are prerendered once, as a shell.
    includedRoutes: (paths) => [
      ...paths.map((p) => shellPath(p)),
      ...NEIGHBOURHOODS.all.flatMap((code) => [nbhdPath(NBHD.fr, code), nbhdPath(NBHD.en, code)]),
    ],
  },
  define: {
    __RANKING_COUNT__: JSON.stringify(countRankingNeighborhoods()),
    // Date of the published data snapshot (schema.org Dataset on the Method page).
    __DATA_DATE__: JSON.stringify(dataDate()),
    __SITE_URL__: JSON.stringify(SITE_URL),
    __NOINDEX__: JSON.stringify(NOINDEX),
  },
})
