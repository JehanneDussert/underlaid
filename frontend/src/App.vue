<script setup>
import { ref, computed, onMounted, onServerPrefetch, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { localizedRouteName } from './router'
import { loadStaticJson } from './utils/loadStaticJson'

const { t, locale } = useI18n()
const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const DOI_URL = 'https://doi.org/10.5281/zenodo.23083312'
const VERSION = '0.2.0'
const route = useRoute()
const router = useRouter()

// Main navigation of the redesign (mock-ups, docs/maquettes/). Pages are
// added here as they are built: a link never leads to a page that doesn't
// exist yet. Five links at most (CLAUDE.md, "pas plus de 5 boutons").
const NAV = [
  { name: 'home', key: 'map' },
  { name: 'methodology', key: 'methodology' },
]

// Switching language navigates to the equivalent page's own URL
// (e.g. /ranking -> /fr/ranking) rather than re-rendering the same URL
// in another language — see router.js for why (hreflang needs each
// language to be its own crawlable page). setLocale() itself still
// runs from the router's beforeEach guard once the navigation lands.
function goToLocale(target) {
  if (locale.value === target) return
  router.push({ name: localizedRouteName(route.name, target), params: route.params, query: route.query })
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
onMounted(loadLastUpdated)

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

const isCurrent = (name) => route.name === localizedRouteName(name, locale.value)
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main">{{ t('site.skipLink') }}</a>
    <header class="site-header container">
      <router-link class="wordmark" :to="{ name: localizedRouteName('home', locale) }">underlaid</router-link>
      <nav class="nav" :aria-label="t('site.navLabel')">
        <router-link
          v-for="item in NAV"
          :key="item.name"
          :to="{ name: localizedRouteName(item.name, locale) }"
          :aria-current="isCurrent(item.name) ? 'page' : undefined"
        >{{ t(`site.nav.${item.key}`) }}</router-link>
        <div class="lang-toggle" role="group" :aria-label="t('site.languageLabel')">
          <button type="button" lang="en" :aria-pressed="locale === 'en'" @click="goToLocale('en')">EN</button>
          <button type="button" lang="fr" :aria-pressed="locale === 'fr'" @click="goToLocale('fr')">FR</button>
        </div>
      </nav>
    </header>

    <main id="main" tabindex="-1">
      <router-view />
    </main>

    <footer id="footer-sources" class="site-footer">
      <div class="container footer-grid">
        <div class="footer-col">
          <p v-if="lastUpdatedLabel" class="footer-updated">{{ lastUpdatedLabel }}</p>
          <p>{{ t('footer') }}</p>
        </div>
        <div class="footer-col footer-links">
          <router-link :to="{ name: localizedRouteName('ranking', locale) }">{{ t('site.nav.ranking') }}</router-link>
          <router-link :to="{ name: localizedRouteName('press', locale) }">{{ t('site.nav.press') }}</router-link>
          <router-link :to="{ name: localizedRouteName('methodology-details', locale), hash: '#data-licences' }">{{ t('footerLicenseLink') }}</router-link>
          <a :href="REPO_URL" rel="noopener">{{ t('site.code') }}</a>
          <a :href="DOI_URL" rel="noopener">{{ t('site.cite') }}</a>
          <span>{{ t('footerLicense') }} · v{{ VERSION }}</span>
        </div>
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
  background: var(--dark);
  color: var(--text-on-dark);
  font-weight: 600;
  text-decoration: none;
}
.skip-link:focus {
  top: 12px;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 24px;
  padding-bottom: 24px;
}

.wordmark {
  font-weight: 800;
  font-size: 20px;
  letter-spacing: -0.02em;
  text-decoration: none;
  color: var(--text-primary);
}

.nav {
  display: flex;
  gap: 28px;
  align-items: center;
  font-size: 15px;
}
.nav a {
  text-decoration: none;
  color: var(--text-primary);
}
.nav a[aria-current='page'] {
  text-decoration: underline;
  text-underline-offset: 6px;
  text-decoration-thickness: 2px;
}
.nav a:hover {
  color: var(--accent);
}

.lang-toggle {
  display: flex;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  border: 1px solid var(--control-border);
}
.lang-toggle button {
  border: none;
  background: none;
  padding: 5px 10px;
  border-radius: 999px;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-primary);
}
.lang-toggle button[aria-pressed='true'] {
  background: var(--dark);
  color: var(--text-on-dark);
}

/* Phone widths: the links drop to their own line and wrap — no drawer
   menu (CLAUDE.md: the main information never sits behind a menu). */
@media (max-width: 720px) {
  .site-header {
    flex-wrap: wrap;
    padding-top: 16px;
    padding-bottom: 16px;
  }
  .nav {
    width: 100%;
    flex-wrap: wrap;
    gap: 10px 20px;
  }
  .lang-toggle {
    margin-left: auto;
  }
}

.site-footer {
  border-top: 1px solid var(--line);
  margin-top: 48px;
  font-size: 13px;
  color: var(--text-secondary);
}
.footer-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px 48px;
  padding-top: 32px;
  padding-bottom: 32px;
}
.footer-col {
  max-width: 640px;
}
.footer-col p {
  margin: 0 0 6px;
  line-height: 1.5;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  align-content: flex-start;
}
.footer-links a {
  color: var(--text-secondary);
}
.footer-links a:hover {
  color: var(--accent);
}
.footer-updated {
  color: var(--text-primary);
  font-weight: 600;
}
</style>
