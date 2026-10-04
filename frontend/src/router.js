import HomeView from './views/HomeView.vue'
import NeighbourhoodView from './views/NeighbourhoodView.vue'
import AboutView from './views/AboutView.vue'
import AddressView from './views/AddressView.vue'
import QuizView from './views/QuizView.vue'
import RoutesView from './views/RoutesView.vue'
import MethodView from './views/MethodView.vue'
import MethodologyView from './views/MethodologyView.vue'
import PressKitView from './views/PressKitView.vue'
import RankingView from './views/RankingView.vue'
import { LOCALE_STORAGE_KEY } from './i18n'
import { ROUTE_PATHS, DEFAULT_LOCALE } from './routePaths'

const COMPONENTS = {
  home: HomeView,
  neighbourhood: NeighbourhoodView,
  about: AboutView,
  address: AddressView,
  quiz: QuizView,
  routes: RoutesView,
  // Loaded on demand: MapLibre (about 1 MB) is only needed by the map.
  map: () => import('./views/ExploreView.vue'),
  methodology: MethodView,
  // The detailed methodology page (before the redesign): kept in full for
  // journalists and researchers, linked from the short "Method" page.
  'methodology-details': MethodologyView,
  ranking: RankingView,
  press: PressKitView,
}

// One URL per language (French at the root, English under /en — see
// routePaths.js) rather than one URL rendering either language: hreflang
// and the sitemap need each language to be its own crawlable page. French
// routes carry the base name, English ones an "-en" suffix, so the
// language toggle can jump to the equivalent page (localizedRouteName).
function buildRoutes(locale) {
  return ROUTE_PATHS.map(({ name, ...paths }) => ({
    path: paths[locale],
    name: locale === DEFAULT_LOCALE ? name : `${name}-${locale}`,
    component: COMPONENTS[name],
    meta: { locale },
  }))
}

// Plain route records, not a constructed router instance: vite-ssg builds
// its own router (once per prerendered page at build time, plus once in
// the browser), so it needs the raw records rather than something
// already wrapped in createRouter().
export const routeRecords = [...buildRoutes('fr'), ...buildRoutes('en')]

// The base (French) route name for a given route name — strips the "-en"
// suffix if present.
export function baseRouteName(name) {
  return typeof name === 'string' && name.endsWith('-en') ? name.slice(0, -3) : name
}

export function localizedRouteName(name, locale) {
  const base = baseRouteName(name)
  return locale === DEFAULT_LOCALE ? base : `${base}-${locale}`
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
  router.beforeEach((to, from) => {
    // "/" is always French for crawlers (no localStorage there), but a
    // returning visitor whose last explicit choice was English lands back
    // on the English home — browser only, and only on the first
    // navigation of a visit: applied to in-app navigations too, it would
    // bounce the FR button straight back to English.
    if (to.path === '/' && from.matched.length === 0 && typeof localStorage !== 'undefined') {
      const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
      if (saved === 'en') return { name: 'home-en' }
    }
    setLocale(to.meta.locale || DEFAULT_LOCALE)
  })
}
