import HomeView from './views/HomeView.vue'
import MethodologyView from './views/MethodologyView.vue'
import PressKitView from './views/PressKitView.vue'
import RankingView from './views/RankingView.vue'
import { LOCALE_STORAGE_KEY } from './i18n'

// Locale-prefixed routes (English unprefixed, French under /fr) rather
// than a single URL with a client-side-only language toggle: proper
// hreflang alternates and a clean sitemap both need each language to be
// its own crawlable URL, not the same URL rendering different content
// depending on localStorage. Route names get a `-fr` suffix so the
// language toggle can jump to the equivalent page in the other language
// (see localizedRouteName below) rather than just re-rendering in place.
const ROUTE_DEFS = [
  { segment: '', name: 'home', component: HomeView },
  { segment: 'methodology', name: 'methodology', component: MethodologyView },
  { segment: 'ranking', name: 'ranking', component: RankingView },
  { segment: 'press', name: 'press', component: PressKitView },
]

function buildRoutes(locale, prefix) {
  return ROUTE_DEFS.map(({ segment, name, component }) => ({
    path: prefix ? (segment ? `/${prefix}/${segment}` : `/${prefix}`) : segment ? `/${segment}` : '/',
    name: prefix ? `${name}-${locale}` : name,
    component,
    meta: { locale },
  }))
}

// Plain route records, not a constructed router instance: vite-ssg builds
// its own router (once per prerendered page at build time, plus once in
// the browser), so it needs the raw records rather than something
// already wrapped in createRouter().
export const routeRecords = [...buildRoutes('en', ''), ...buildRoutes('fr', 'fr')]

// The base (English, unprefixed) route name for a given route name —
// strips the "-fr" suffix if present. Used by the language toggle to
// find the equivalent page in the other language.
export function baseRouteName(name) {
  return typeof name === 'string' && name.endsWith('-fr') ? name.slice(0, -3) : name
}

export function localizedRouteName(name, locale) {
  const base = baseRouteName(name)
  return locale === 'fr' ? `${base}-fr` : base
}

// Attaches the locale-redirect/sync guard to whatever router instance
// vite-ssg creates (one per build-time render, one in the browser) —
// called from main.js's setup callback rather than defined on a
// module-level router export, since no such export exists anymore.
// `setLocale` is passed in bound to that same call's own i18n instance
// (see createI18nInstance in i18n/index.js) rather than imported as a
// shared singleton — a module-level i18n instance is reused across every
// concurrently-rendered route in vite-ssg's build queue, so one route's
// locale would otherwise leak into another's (caught directly: /ranking
// prerendered with French content under the old singleton setup).
export function installLocaleGuard(router, setLocale) {
  router.beforeEach((to) => {
    // The bare, unprefixed "/" is unambiguous for crawlers (always
    // English, matching this project's own "no auto-detection, English
    // default" rule) but a returning visitor whose last explicit choice
    // was French should still land back in French — a client-side-only
    // redirect, never applied to any other route, so indexing of "/"
    // itself stays stable and crawlable as English content. Guarded to
    // the browser only: during SSG prerendering there is no localStorage
    // and "/" must always prerender as English.
    if (to.path === '/' && typeof localStorage !== 'undefined') {
      const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
      if (saved === 'fr') return { name: 'home-fr' }
    }
    setLocale(to.meta.locale || 'en')
  })
}
