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
  { name: 'press', fr: '/presse', en: '/en/press', old: { en: '/press', fr: '/fr/press' } },
  { name: 'address', fr: '/adresse', en: '/en/address', old: { en: '/address', fr: '/fr/address' }, sitemap: false },
  { name: 'quiz', fr: '/quiz', en: '/en/quiz', old: { en: '/quiz', fr: '/fr/quiz' }, sitemap: false },
  { name: 'routes', fr: '/itineraires', en: '/en/routes', old: { en: '/routes', fr: '/fr/routes' }, sitemap: false },
]

export const LOCALES = ['fr', 'en']
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
  return out
}
