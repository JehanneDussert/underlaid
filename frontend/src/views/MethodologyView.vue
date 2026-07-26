<script setup>
import { computed, ref, onMounted, onServerPrefetch } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'
import { useSeoMeta } from '../composables/useSeoMeta'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()

useSeoMeta({
  title: {
    en: 'Methodology — How the Cumulative Exposure Score Works',
    fr: "Méthodologie — comment fonctionne le score de cumul d'exposition",
  },
  description: {
    en: 'Why a count of worst-quartile categories instead of an average, what each of the 4 categories measures, and the known limits — written for a non-technical reader, with the full technical version linked.',
    fr: "Pourquoi un compte de catégories au pire quartile plutôt qu'une moyenne, ce que mesure chacune des 4 catégories, et les limites connues — écrit pour un lecteur non technique, avec la version technique complète en lien.",
  },
  jsonLd: (locale) => ({
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline:
      locale === 'fr'
        ? "Méthodologie — comment fonctionne le score de cumul d'exposition"
        : 'Methodology — how the cumulative exposure score works',
    description:
      locale === 'fr'
        ? "Explique pourquoi Underlaid compte les catégories au pire quartile plutôt que de faire une moyenne, ce que mesure chacune des 4 catégories, et les limites connues de la méthode."
        : 'Explains why Underlaid counts worst-quartile categories rather than averaging them, what each of the 4 categories measures, and the method\'s known limits.',
    author: { '@type': 'Organization', name: 'Underlaid' },
    publisher: { '@type': 'Organization', name: 'Underlaid' },
    inLanguage: locale,
  }),
})

// Static facts from SCORING.md (scripts/11_compute_vulnerability_score.py's
// output) — not user data, so no fetch: this page describes the method,
// it doesn't recompute or re-derive anything from the live GeoJSON.
const DISTRIBUTION = [
  { score: 0, count: 874, share: 0.318 },
  { score: 1, count: 1230, share: 0.447 },
  { score: 2, count: 586, share: 0.213 },
  { score: 3, count: 58, share: 0.021 },
  { score: 4, count: 4, share: 4 / 2752 },
]

const SUBSCORES = [
  { key: 'thermal' },
  { key: 'pollution' },
  { key: 'access' },
  { key: 'housing' },
]

const LIMIT_KEYS = [
  'limitIncome', 'limitIcu', 'limitAccesslibre', 'limitFootway',
  'limitThermosensitivity', 'limitArtificialization', 'limitCapacity', 'limitEstimate',
]

function numberLocale() {
  return locale.value === 'fr' ? 'fr-FR' : 'en-US'
}

function formatShare(value) {
  return new Intl.NumberFormat(numberLocale(), { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)
}

function formatCount(value) {
  return new Intl.NumberFormat(numberLocale()).format(value)
}

const distributionRows = computed(() =>
  DISTRIBUTION.map((row) => ({
    ...row,
    countLabel: formatCount(row.count),
    shareLabel: formatShare(row.share),
  }))
)

// Same "which snapshot is this" concern as the footer (see App.vue) —
// repeated here because this is the page that cites the distribution
// numbers directly, so the date belongs right next to them too.
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
  const formatted = new Intl.DateTimeFormat(numberLocale(), { year: 'numeric', month: 'long', day: 'numeric' }).format(date)
  return t('methodology.distLastUpdated', { date: formatted })
})
</script>

<template>
  <div class="methodology">
    <router-link class="back-link" :to="{ name: localizedRouteName('home', locale) }">{{ t('methodology.backLink') }}</router-link>

    <h1>{{ t('methodology.title') }}</h1>
    <p class="intro">{{ t('methodology.intro') }}</p>

    <section class="glass">
      <h2>{{ t('methodology.countTitle') }}</h2>
      <p>{{ t('methodology.countBody1') }}</p>
      <p>{{ t('methodology.countBody2') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.notMeasuredTitle') }}</h2>
      <p>{{ t('methodology.notMeasuredBody1') }}</p>
      <p>{{ t('methodology.notMeasuredBody2') }}</p>
      <p>{{ t('methodology.notMeasuredBody3') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.subscoresTitle') }}</h2>
      <p>{{ t('methodology.subscoresIntro') }}</p>
      <div class="subscore-grid">
        <div v-for="s in SUBSCORES" :key="s.key" class="subscore-card">
          <h3>{{ t(`methodology.${s.key}Name`) }}</h3>
          <p>{{ t(`methodology.${s.key}Desc`) }}</p>
        </div>
      </div>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.thresholdTitle') }}</h2>
      <p>{{ t('methodology.thresholdBody1') }}</p>
      <p>{{ t('methodology.thresholdBody2') }}</p>
      <p>{{ t('methodology.thresholdBody3') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.electricalTitle') }}</h2>
      <p>{{ t('methodology.electricalBody1') }}</p>
      <p>{{ t('methodology.electricalBody2') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.expansionTitle') }}</h2>
      <p>{{ t('methodology.expansionBody1') }}</p>
      <p>{{ t('methodology.expansionBody2') }}</p>
      <p>{{ t('methodology.expansionBody3') }}</p>
      <p>{{ t('methodology.expansionBody4') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.limitsTitle') }}</h2>
      <p>{{ t('methodology.limitsIntro') }}</p>
      <ul class="limits-list">
        <li v-for="key in LIMIT_KEYS" :key="key">{{ t(`methodology.${key}`) }}</li>
      </ul>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.distributionTitle') }}</h2>
      <table class="dist-table">
        <thead>
          <tr>
            <th scope="col">{{ t('methodology.distColScore') }}</th>
            <th scope="col">{{ t('methodology.distColCount') }}</th>
            <th scope="col">{{ t('methodology.distColShare') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in distributionRows" :key="row.score">
            <td>{{ row.score }} / 4</td>
            <td>{{ row.countLabel }}</td>
            <td>{{ row.shareLabel }}</td>
          </tr>
        </tbody>
      </table>
      <p class="dist-note">{{ t('methodology.distNote') }}</p>
      <p v-if="lastUpdatedLabel" class="dist-note">{{ lastUpdatedLabel }}</p>
    </section>

    <router-link class="press-kit-link" :to="{ name: localizedRouteName('press', locale) }">{{ t('methodology.pressKitLink') }}</router-link>
  </div>
</template>

<style scoped>
.methodology {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 40px 64px;
}
@media (max-width: 920px) {
  .methodology {
    padding: 28px 20px 48px;
  }
}

.back-link {
  display: inline-block;
  margin-bottom: 24px;
  font-size: 12.5px;
  color: var(--text-secondary);
  text-decoration: none;
}
.back-link:hover {
  color: var(--cyan);
}

h1 {
  font-weight: 700;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.08;
  margin: 0 0 16px;
  letter-spacing: -0.02em;
}

.intro {
  font-size: 15px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 32px;
}

section {
  padding: 24px 28px;
  margin-bottom: 20px;
}

h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 14px;
}

section p {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 12px;
}
section p:last-child {
  margin-bottom: 0;
}

.subscore-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin-top: 16px;
}
@media (max-width: 640px) {
  .subscore-grid {
    grid-template-columns: 1fr;
  }
}

.subscore-card {
  padding: 14px 16px;
  border: 1px solid var(--panel-b);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}
.subscore-card h3 {
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text-primary);
}
.subscore-card p {
  font-size: 12.5px;
  margin: 0;
}

.limits-list {
  margin: 12px 0 0;
  padding-left: 20px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.limits-list li {
  margin-bottom: 10px;
}
.limits-list li:last-child {
  margin-bottom: 0;
}

.dist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  margin-top: 8px;
}
.dist-table th,
.dist-table td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--gridline);
  color: var(--text-secondary);
}
.dist-table th {
  font-family: var(--mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}
.dist-table td:first-child {
  color: var(--text-primary);
  font-family: var(--mono);
  font-weight: 600;
}

.dist-note {
  margin-top: 14px !important;
  font-size: 12px !important;
  color: var(--text-muted) !important;
}

.press-kit-link {
  display: inline-block;
  margin-top: 4px;
  font-size: 13px;
  color: var(--cyan);
  text-decoration: none;
}
.press-kit-link:hover {
  color: var(--magenta);
}
</style>
