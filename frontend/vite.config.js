import { readFileSync, writeFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Single source of truth for the production domain — shared with the
// frontend via the `define` below (see composables/useSeoMeta.js) and
// with the sitemap/robots generator in the seoFilesPlugin below, so
// there's never a second copy to fall out of sync. Override with
// SITE_URL=... at build time (e.g. a fork deployed elsewhere, or a
// custom domain later) — no trailing slash.
const SITE_URL = (process.env.SITE_URL || 'https://underlaid.vercel.app').replace(/\/+$/, '')

// Read at config-eval time (Node, not the browser) so the /ranking page's
// meta description can state the real neighborhood count without either
// hardcoding a number that drifts every time the scoring pipeline re-runs,
// or depending on an async fetch that a static prerender pass can't easily
// wait on for something as small as a page description.
function countRankingNeighborhoods() {
  try {
    const path = fileURLToPath(new URL('./public/data/vulnerability_score_iris.geojson', import.meta.url))
    const geojson = JSON.parse(readFileSync(path, 'utf-8'))
    // Same rule as RankingView.vue: top score (3/3), IRIS with at least 50
    // residents (smaller ones stay on the map but not on the public list).
    return geojson.features.filter(
      (f) => f.properties.cumulative_vulnerability_score === 3 && (f.properties.population ?? 0) >= 50
    ).length
  } catch {
    return 0
  }
}

// The same 8 routes declared in src/router.js — kept as a plain literal
// here rather than imported, since router.js pulls in Vue SFCs that
// this Node-context config file can't (and shouldn't need to) resolve.
const ROUTE_SEGMENTS = ['', 'methodology', 'ranking', 'press']

function routePaths(prefix) {
  return ROUTE_SEGMENTS.map((segment) => {
    if (!prefix) return segment ? `/${segment}` : '/'
    return segment ? `/${prefix}/${segment}` : `/${prefix}`
  })
}

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
      const enPaths = routePaths('')
      const frPaths = routePaths('fr')
      const urls = [...enPaths, ...frPaths].map((path, i) => {
        const isEn = i < enPaths.length
        const enPath = isEn ? path : enPaths[i - enPaths.length]
        const frPath = isEn ? frPaths[i] : path
        return `  <url>
    <loc>${SITE_URL}${path}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="${SITE_URL}${enPath}"/>
    <xhtml:link rel="alternate" hreflang="fr" href="${SITE_URL}${frPath}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}${enPath}"/>
  </url>`
      })
      const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join('\n')}
</urlset>
`
      writeFileSync(`${options.dir}/sitemap.xml`, xml)
      writeFileSync(`${options.dir}/robots.txt`, `User-agent: *
Allow: /

Sitemap: ${SITE_URL}/sitemap.xml
`)
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), seoFilesPlugin()],
  define: {
    __RANKING_COUNT__: JSON.stringify(countRankingNeighborhoods()),
    __SITE_URL__: JSON.stringify(SITE_URL),
  },
})
