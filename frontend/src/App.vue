<script setup>
import { ref, computed, nextTick, onMounted, onServerPrefetch, provide, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { localizedRouteName } from './router'
import { loadStaticJson } from './utils/loadStaticJson'
import { lastNeighbourhood, restoreNeighbourhood } from './utils/neighbourhood'

const { t, locale } = useI18n()
const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const DISCUSSIONS_URL = `${REPO_URL}/discussions`
const DOI_URL = 'https://doi.org/10.5281/zenodo.23083312'
const VERSION = '0.2.0'
const route = useRoute()

// Main navigation of the redesign (docs/design/refonte-d4/): "Votre
// quartier", "Explorer la carte", "Méthode", then the other language.
// "Votre quartier" stays greyed until an address has been chosen (the
// page needs a neighbourhood). Other pages live in the footer.
const NAV = [
  { name: 'map', key: 'map' },
  { name: 'methodology', key: 'methodology' },
  { name: 'about', key: 'about' },
]
const otherLocale = computed(() => (locale.value === 'fr' ? 'en' : 'fr'))
// The equivalent page in the other language, same params, query and hash.
const otherLocaleTo = computed(() => ({
  name: localizedRouteName(route.name, otherLocale.value),
  params: route.params,
  query: route.query,
  hash: route.hash,
}))

const isCurrent = (name) => route.name === localizedRouteName(name, locale.value)

// Phone menu: a disclosure button (aria-expanded); Escape closes it and
// gives the focus back to the button; a page change closes it.
const menuOpen = ref(false)
const menuButton = ref(null)
function closeMenu(returnFocus = false) {
  if (!menuOpen.value) return
  menuOpen.value = false
  if (returnFocus) nextTick(() => menuButton.value?.focus())
}
function onKeydown(event) {
  if (event.key === 'Escape') closeMenu(true)
}

// After each page change, move the focus to the new page's h1 so a screen
// reader announces the new page (decision of 3 October 2026). The watcher
// does not run on the first load (no `immediate`), where the browser's own
// focus handling applies. Anchor links keep their own target.
watch(
  () => route.path,
  async () => {
    closeMenu()
    if (route.hash) return
    await nextTick()
    const h1 = document.querySelector('#main h1')
    if (!h1) return
    if (!h1.hasAttribute('tabindex')) h1.setAttribute('tabindex', '-1')
    h1.focus({ preventScroll: true })
  }
)

// Contact without the address in the page's code: the mailto link is
// composed on click only, from parts (address given by the project owner
// on 3 October 2026). Without JavaScript, the link leads to the GitHub
// discussions, the other contact channel.
const CONTACT_PARTS = ['research.jehannedussert', 'gmail.com']
const contactHref = DISCUSSIONS_URL
function openContact(event) {
  event.preventDefault()
  window.location.href = `mailto:${CONTACT_PARTS.join('@')}`
}

// So anyone citing a specific neighbourhood knows which snapshot of the
// score they're referencing (the score moves with every pipeline run).
// Written by scripts/run_all.py; loaded with the SSR-safe helper so it is
// part of the prerendered HTML.
const lastUpdated = ref(null)

async function loadLastUpdated() {
  try {
    const data = await loadStaticJson('/data/last_updated.json')
    lastUpdated.value = data.generated_at
  } catch {
    lastUpdated.value = null
  }
}

onServerPrefetch(loadLastUpdated)
onMounted(() => {
  loadLastUpdated()
  restoreNeighbourhood()
})

const dataDate = computed(() => {
  if (!lastUpdated.value) return ''
  return new Intl.DateTimeFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(lastUpdated.value))
})
// Shared with every figure's source line (components/FigureSource.vue).
provide('dataDate', dataDate)
const lastUpdatedLabel = computed(() => (dataDate.value ? t('footerLastUpdated', { date: dataDate.value }) : ''))
</script>

<template>
  <div class="app-shell" @keydown="onKeydown">
    <a class="skip-link" href="#main">{{ t('site.skipLink') }}</a>
    <header class="site-header">
      <router-link class="wordmark" :to="{ name: localizedRouteName('home', locale) }" :aria-label="t('site.homeLabel')">underlaid</router-link>
      <button
        ref="menuButton"
        type="button"
        class="menu-button"
        :aria-expanded="menuOpen ? 'true' : 'false'"
        aria-controls="site-nav"
        :aria-label="menuOpen ? t('site.closeMenu') : t('site.openMenu')"
        @click="menuOpen = !menuOpen"
      >
        <svg v-if="!menuOpen" aria-hidden="true" width="18" height="14" viewBox="0 0 18 14">
          <path d="M1 1h16M1 7h16M1 13h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <svg v-else aria-hidden="true" width="16" height="16" viewBox="0 0 16 16">
          <path d="M2 2l12 12M14 2 2 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </button>
      <nav id="site-nav" class="nav" :class="{ open: menuOpen }" :aria-label="t('site.navLabel')">
        <ul class="nav-list">
          <li>
            <!-- Greyed text until a neighbourhood has been seen in this tab
                 (a link would lead nowhere), then a link back to it. -->
            <router-link
              v-if="lastNeighbourhood"
              :to="{ name: localizedRouteName('neighbourhood', locale), params: { code: lastNeighbourhood } }"
              :aria-current="isCurrent('neighbourhood') ? 'page' : undefined"
            >{{ t('site.nav.neighbourhood') }}</router-link>
            <span v-else class="nav-disabled" aria-disabled="true">{{ t('site.nav.neighbourhood') }}<span class="sr-only"> {{ t('site.nav.neighbourhoodHint') }}</span></span>
          </li>
          <li v-for="item in NAV" :key="item.name">
            <router-link :to="{ name: localizedRouteName(item.name, locale) }" :aria-current="isCurrent(item.name) ? 'page' : undefined">{{ t(`site.nav.${item.key}`) }}</router-link>
          </li>
          <li>
            <router-link class="nav-lang" :to="otherLocaleTo" :lang="otherLocale" :hreflang="otherLocale" :aria-label="t('site.otherLanguage')">{{ otherLocale.toUpperCase() }}</router-link>
          </li>
        </ul>
      </nav>
    </header>

    <main id="main" tabindex="-1">
      <router-view />
    </main>

    <footer id="footer-sources" class="site-footer">
      <div class="footer-main">
        <p class="footer-lead">
          {{ t('site.footerOpenData') }}
          <router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('site.footerSources') }}</router-link>
        </p>
        <ul class="footer-links">
          <li><router-link :to="{ name: localizedRouteName('ranking', locale) }">{{ t('site.nav.ranking') }}</router-link></li>
          <li><router-link :to="{ name: localizedRouteName('about', locale), hash: '#citer' }">{{ t('site.footerReuse') }}</router-link></li>
          <li><router-link :to="{ name: localizedRouteName('about', locale), hash: '#presse' }">{{ t('site.nav.press') }}</router-link></li>
          <li><router-link :to="{ name: localizedRouteName('about', locale) }">{{ t('site.nav.about') }}</router-link></li>
          <li><a :href="contactHref" rel="noopener" @click="openContact">{{ t('site.footerContact') }}</a></li>
          <li><router-link :to="{ name: localizedRouteName('accessibility', locale) }">{{ t('site.footerA11y') }}</router-link></li>
        </ul>
      </div>
      <div class="footer-meta">
        <p v-if="lastUpdatedLabel" class="footer-updated">{{ lastUpdatedLabel }}</p>
        <p>{{ t('footer') }}</p>
        <p>
          {{ t('footerLicense') }} · <a :href="REPO_URL" rel="noopener">{{ t('site.code') }}</a> ·
          <a :href="DOI_URL" rel="noopener">{{ t('site.cite') }}</a> · v{{ VERSION }}
        </p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}
main:focus {
  outline: none;
}

.skip-link {
  position: absolute;
  left: 16px;
  top: -60px;
  z-index: 100;
  padding: 10px 16px;
  border-radius: var(--radius-small);
  background: var(--primary);
  color: #fff;
  font-weight: 700;
  text-decoration: none;
}
.skip-link:focus {
  top: 12px;
}

/* Header: 88 px high, 64 px side gutters (desktop mock-up); 60 px, a
   bottom hairline and a menu button on phones (AccueilMobileBD4). */
.site-header {
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 var(--page-gutter);
  position: relative;
}
.wordmark {
  font-weight: 700;
  font-size: 22px;
  text-decoration: none;
  color: var(--text-primary);
}
.nav-list {
  display: flex;
  align-items: center;
  gap: 28px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 16px;
}
.nav a {
  color: var(--text-primary);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  min-height: 44px;
}
.nav a:hover {
  color: var(--primary);
}
.nav a[aria-current='page'] {
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 6px;
  text-decoration-thickness: 2px;
}
.nav-disabled {
  color: var(--text-muted);
  cursor: default;
}
.nav .nav-lang {
  color: var(--text-muted);
}
.menu-button {
  display: none;
}

@media (max-width: 1024px) {
  .site-header {
    padding: 0 32px;
  }
}

@media (max-width: 760px) {
  .site-header {
    height: 60px;
    padding: 0 16px;
    border-bottom: 1px solid var(--line-soft);
  }
  .wordmark {
    font-size: 20px;
  }
  .menu-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 1.5px solid var(--control-border);
    background: var(--surface);
    color: var(--text-primary);
    cursor: pointer;
  }
  .nav {
    display: none;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    z-index: 50;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    box-shadow: 0 12px 24px var(--panel-shadow);
  }
  .nav.open {
    display: block;
  }
  .nav-list {
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: 8px 16px 16px;
    font-size: 18px;
  }
  .nav-list li {
    border-bottom: 1px solid var(--line-soft);
  }
  .nav-list li:last-child {
    border-bottom: none;
  }
  .nav a,
  .nav-disabled {
    display: flex;
    align-items: center;
    min-height: 52px;
  }
}

.site-footer {
  margin: 80px var(--page-gutter) 0;
  padding: 24px 0 40px;
  border-top: 1px solid var(--line-soft);
  font-size: 14px;
  color: var(--text-secondary);
}
.footer-main {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px 24px;
}
.footer-lead {
  margin: 0;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.site-footer a {
  color: var(--text-primary);
}
.site-footer a:hover {
  color: var(--primary);
}
.footer-meta {
  margin-top: 20px;
  font-size: 13px;
  color: var(--text-muted);
}
.footer-meta p {
  margin: 0 0 6px;
  line-height: 1.5;
}
.footer-meta a {
  color: var(--text-muted);
}
.footer-updated {
  color: var(--text-secondary);
  font-weight: 700;
}
@media (max-width: 1024px) {
  .site-footer {
    margin: 64px 32px 0;
  }
}
@media (max-width: 600px) {
  .site-footer {
    margin: 48px 16px 0;
  }
  .footer-links a {
    display: inline-flex;
    min-height: 44px;
    align-items: center;
  }
}
</style>
