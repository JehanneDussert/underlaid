// Page addresses, one per language: French at the root, English under /en
// (redesign decision of 3 October 2026, CLAUDE.md "Refonte D4"). Plain data
// with no Vue import, so vite.config.js can read it too (sitemap, robots)
// and the two can never disagree. `old` lists the addresses used before the
// redesign; vercel.json redirects them permanently (checked by the smoke
// test).
//
// `sitemap: false`: transitional pages, replaced during the redesign
// (address and routes by "Votre quartier", quiz by the question on the
// home page) — still reachable, not advertised to search engines.
export const ROUTE_PATHS = [
  { name: 'home', fr: '/', en: '/en', old: { en: '/', fr: '/fr' } },
  // One page per neighbourhood, by its INSEE code (never an address in the
  // URL). Prerendered once as a shell (/quartier), served for every code by
  // a rewrite (vercel.json); not in the sitemap.
  {
    name: 'neighbourhood',
    fr: '/quartier/:code?',
    en: '/en/neighbourhood/:code?',
    sample: { fr: '/quartier/930290101', en: '/en/neighbourhood/930290101' },
    sitemap: false,
  },
  { name: 'map', fr: '/carte', en: '/en/map', old: { en: '/map', fr: '/fr/map' } },
  { name: 'methodology', fr: '/methode', en: '/en/method', old: { en: '/methodology', fr: '/fr/methodology' } },
  {
    name: 'methodology-details',
    fr: '/methode/detail',
    en: '/en/method/details',
    old: { en: '/methodology/details', fr: '/fr/methodology/details' },
  },
  {
    name: 'ranking',
    fr: '/quartiers-les-plus-exposes',
    en: '/en/most-exposed-neighbourhoods',
    old: { en: '/ranking', fr: '/fr/ranking' },
  },
  { name: 'about', fr: '/a-propos', en: '/en/about' },
  { name: 'press', fr: '/presse', en: '/en/press', old: { en: '/press', fr: '/fr/press' } },
  { name: 'places', fr: '/lieux-du-quotidien', en: '/en/everyday-places' },
  { name: 'corrections', fr: '/corrections', en: '/en/corrections' },
  { name: 'accessibility', fr: '/accessibilite', en: '/en/accessibility' },
  // Prerendered as dist/404.html, served by the host for unknown addresses.
  { name: 'notFound', fr: '/404', en: '/en/404', sitemap: false },
]

// Pages removed by the redesign (D4): their addresses, old and transitional,
// redirect permanently to the page that replaced them.
const RETIRED = [
  ['/adresse', '/'], ['/en/address', '/en'], ['/fr/address', '/'], ['/address', '/en'],
  ['/quiz', '/'], ['/en/quiz', '/en'], ['/fr/quiz', '/'],
  ['/itineraires', '/lieux-du-quotidien'], ['/en/routes', '/en/everyday-places'], ['/fr/routes', '/lieux-du-quotidien'], ['/routes', '/en/everyday-places'],
]

export const LOCALES = ['fr', 'en']

// Address of a page without its optional parameter (the prerendered shell).
export const shellPath = (path) => path.replace(/\/:[^/]+\?$/, '')

// Rewrites for pages with a parameter: every /quartier/<code> is served the
// prerendered shell, which reads the code from the URL.
export function paramRewrites() {
  return ROUTE_PATHS.filter((r) => r.sample).flatMap((r) =>
    LOCALES.map((l) => ({ source: r[l].replace(/\?$/, ''), destination: shellPath(r[l]) }))
  )
}
export const DEFAULT_LOCALE = 'fr'

// Permanent redirects from the pre-redesign addresses. A source that is
// now the address of a current page is skipped: the old English home "/"
// and quiz "/quiz" are now the French pages and must keep serving them.
export function legacyRedirects() {
  const current = new Set(ROUTE_PATHS.flatMap((r) => LOCALES.map((l) => r[l])))
  const out = []
  for (const r of ROUTE_PATHS) {
    for (const locale of LOCALES) {
      const source = r.old?.[locale]
      if (!source || current.has(source)) continue
      out.push({ source, destination: r[locale], permanent: true })
    }
  }
  for (const [source, destination] of RETIRED) if (!current.has(source)) out.push({ source, destination, permanent: true })
  return out
}
