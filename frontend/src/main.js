import { ViteSSG } from 'vite-ssg'
// Self-hosted font (no request to a third-party font service).
// Atkinson Hyperlegible (Braille Institute, SIL Open Font License),
// designed for low-vision readers: regular and bold only.
import '@fontsource/atkinson-hyperlegible/400.css'
import '@fontsource/atkinson-hyperlegible/400-italic.css'
import '@fontsource/atkinson-hyperlegible/700.css'
import './style.css'
import App from './App.vue'
import { createI18nInstance } from './i18n'
import { routeRecords, installLocaleGuard } from './router'

// vite-ssg needs the raw route records (it builds its own router
// instance internally, since it also has to build one per prerendered
// page at build time) rather than the already-constructed router this
// app used before — see router.js for why the locale-redirect guard is
// now installed via installLocaleGuard(router, setLocale) instead of
// being wired directly onto a module-level router export. @unhead/vue's
// createHead() is set up internally by ViteSSG itself, so it isn't
// installed here. A fresh i18n instance is created per createApp() call
// (this setup callback runs once per prerendered route, plus once in the
// browser) rather than reusing a shared singleton — see createI18nInstance
// for why that leaked locale state across concurrently-rendered routes.
// Scroll to #anchors on in-app navigation too (the footer links to
// /methodology#data-licences), and to the top on a plain page change.
function scrollBehavior(to, from, savedPosition) {
  if (savedPosition) return savedPosition
  if (to.hash) return { el: to.hash }
  return { top: 0 }
}

export const createApp = ViteSSG(App, { routes: routeRecords, scrollBehavior }, ({ app, router }) => {
  const { i18n, setLocale } = createI18nInstance()
  app.use(i18n)
  installLocaleGuard(router, setLocale)
})
