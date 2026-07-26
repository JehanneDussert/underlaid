import { createI18n } from 'vue-i18n'
import en from './en.json'
import fr from './fr.json'

export const LOCALE_STORAGE_KEY = 'underlaid-locale'

// English default (the project publishes mainly in English), but a
// returning visitor's explicit choice always wins — no auto-detection
// from browser/geolocation, deliberately: let the person choose.
// Guarded for SSG (vite-ssg prerenders in Node, where `localStorage`
// and `document` don't exist) — falls back to the English default
// there, exactly like a fresh visitor would see.
function initialLocale() {
  if (typeof localStorage === 'undefined') return 'en'
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  return saved === 'fr' || saved === 'en' ? saved : 'en'
}

// A factory, not a module-level singleton: vite-ssg's build renders
// several routes concurrently (a PQueue), each via its own createApp()
// call, but a `const i18n = createI18n(...)` at module scope is a single
// object shared by every one of those concurrent renders — one route's
// setLocale() would silently overwrite another's mid-render locale (this
// was caught directly: /ranking prerendered with French content and a
// French canonical URL under the old singleton). Each createApp() call
// must get its own instance instead.
export function createI18nInstance() {
  const i18n = createI18n({
    legacy: false,
    locale: initialLocale(),
    fallbackLocale: 'en',
    messages: { en, fr },
  })

  function setLocale(locale) {
    i18n.global.locale.value = locale
    if (typeof localStorage !== 'undefined') localStorage.setItem(LOCALE_STORAGE_KEY, locale)
    if (typeof document !== 'undefined') document.documentElement.setAttribute('lang', locale)
  }

  return { i18n, setLocale }
}

if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('lang', initialLocale())
}
