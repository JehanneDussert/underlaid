<script setup>
import { ref, computed, onMounted, onServerPrefetch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { localizedRouteName } from './router'
import { loadStaticJson } from './utils/loadStaticJson'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

// Switching language now navigates to the equivalent page's own URL
// (e.g. /ranking -> /fr/ranking) rather than re-rendering the same URL
// in another language — see router.js for why (hreflang needs each
// language to be its own crawlable page). setLocale() itself still
// runs from the router's beforeEach guard once the navigation lands.
function goToLocale(target) {
  if (locale.value === target) return
  router.push({ name: localizedRouteName(route.name, target), params: route.params, query: route.query })
}

// So anyone citing a specific IRIS by example (Drancy, etc.) knows which
// snapshot of the score they're referencing — the score is explicitly
// not a fixed, final number (see SCORING.md), it moves with
// every pipeline re-run. Written by scripts/run_all.py at the end of a
// full pipeline run. Shown in the footer (present on every page) rather
// than only on /methodology, and loaded via the same SSR-safe helper as
// the rest of the app's static data so it's part of the prerendered HTML.
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

const lastUpdatedLabel = computed(() => {
  if (!lastUpdated.value) return ''
  const date = new Date(lastUpdated.value)
  const formatted = new Intl.DateTimeFormat(locale.value === 'fr' ? 'fr-FR' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
  return t('footerLastUpdated', { date: formatted })
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="wordmark">Under<span>laid</span></div>
      <nav class="nav" aria-label="Primary">
        <a href="#footer-sources">{{ t('nav.sources') }}</a>
        <router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('nav.methodology') }}</router-link>
        <router-link :to="{ name: localizedRouteName('ranking', locale) }">{{ t('nav.ranking') }}</router-link>
        <span class="nav-inert">{{ t('nav.github') }}</span>
        <div class="lang-toggle" role="group" aria-label="Language / Langue">
          <button :class="{ active: locale === 'en' }" @click="goToLocale('en')">EN</button>
          <button :class="{ active: locale === 'fr' }" @click="goToLocale('fr')">FR</button>
        </div>
      </nav>
    </header>

    <router-view />

    <footer id="footer-sources">
      <span>{{ t('footer') }}</span>
      <span v-if="lastUpdatedLabel" class="footer-updated">{{ lastUpdatedLabel }}</span>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 40px;
  border-bottom: 1px solid var(--gridline);
}

.wordmark {
  font-weight: 700;
  font-size: 19px;
  letter-spacing: -0.01em;
}
.wordmark span {
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.nav {
  display: flex;
  gap: 22px;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}
.nav a {
  color: var(--text-secondary);
  text-decoration: none;
}
.nav a:hover,
.nav a:focus-visible {
  color: var(--cyan);
}
.nav-inert {
  opacity: 0.6;
  cursor: default;
}

.lang-toggle {
  display: flex;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  overflow: hidden;
}
.lang-toggle button {
  border: none;
  background: none;
  padding: 5px 11px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-secondary);
  font-family: var(--mono);
}
.lang-toggle button.active {
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  color: #080a0f;
}

@media (max-width: 920px) {
  .topbar {
    padding-left: 20px;
    padding-right: 20px;
  }
}

footer {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 22px 40px;
  border-top: 1px solid var(--gridline);
  font-size: 11.5px;
  color: var(--text-secondary);
  font-family: var(--mono);
}

.footer-updated {
  color: var(--text-muted);
}
</style>
