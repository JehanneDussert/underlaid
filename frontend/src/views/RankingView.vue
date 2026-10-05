<script setup>
import { ref, computed, onMounted, onServerPrefetch } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'
import { useSeoMeta } from '../composables/useSeoMeta'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()
const DATA_URL = '/data/vulnerability_score_iris.geojson'
const CAPACITY_URL = '/data/adaptive_capacity_iris.json'
// "Très exposé" = at least 2 of the 3 exposures (heat, air and noise,
// housing) in the most affected quarter, the definition used everywhere on
// the site (decision of 3 October 2026, confirmed on 5 October). Listed:
// every inhabited IRIS that is highly exposed; those exposed on all three
// come first. Access to care is measured apart (a figure per row).
const EXPOSURES = ['thermal', 'pollution', 'housing']
const nExposures = (p) => EXPOSURES.filter((k) => p[`subscore_${k}_quartile`] === 4).length
// Same floor as cool_facility_deficit's per-resident rate (scripts/11,
// MIN_POPULATION_FOR_RATE): below 50 residents an IRIS is a park, a
// station or a business block, not a neighborhood people live in. Such
// IRIS stay on the map (flagged "very sparsely populated" in the detail
// panel) but are left out of this public list — see SCORING.md.
const MIN_POPULATION_FOR_LIST = 50

// Injected at build time (vite.config.js) from the actual scoring
// output — never hardcoded, so this count can't silently drift out of
// sync with the pipeline the way a hand-typed number would.
useSeoMeta({
  title: {
    en: `The ${__RANKING_COUNT__} neighbourhoods where exposures stack up`,
    fr: `Les ${__RANKING_COUNT__} quartiers où les expositions se cumulent`,
  },
  description: {
    en: `Neighbourhoods of Paris and its inner suburbs with at least 2 of the 3 exposures (heat, air and noise, housing) in the most affected quarter, with their residents' resources.`,
    fr: `Les quartiers de Paris et de la petite couronne qui cumulent au moins 2 des 3 expositions (chaleur, air et bruit, logement) dans le quart le plus touché, avec les ressources de leurs habitants.`,
  },
})

// Grouped by the separate means-to-cope axis (Phase 8), never by an
// implied cause: the groups only show that the same score doesn't mean the
// same situation. Each row shows one figure per category against the
// metro-wide median — facts rather than generated prose, so a row can't
// contradict itself.
const GROUPS = [
  { key: 'low', capacityClass: 0 },
  { key: 'mid', capacityClass: 1 },
  { key: 'high', capacityClass: 2 },
  { key: 'masked', capacityClass: null },
]

const allRows = ref([])
const capacityByIris = ref({})
const loading = ref(true)

async function loadRows() {
  const [geojson, capacity] = await Promise.all([loadStaticJson(DATA_URL), loadStaticJson(CAPACITY_URL)])
  allRows.value = geojson.features.map((f) => f.properties)
  capacityByIris.value = Object.fromEntries(capacity.iris.map((r) => [r.code_iris, r]))
  loading.value = false
}

onServerPrefetch(loadRows)
onMounted(loadRows)

function median(field) {
  const values = allRows.value.map((p) => p[field]).filter((v) => v !== null && v !== undefined).sort((a, b) => a - b)
  if (!values.length) return null
  const mid = Math.floor(values.length / 2)
  return values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2
}

const medians = computed(() => ({
  pct_artificialized: median('pct_artificialized'),
  air_noise_coexposure_class: median('air_noise_coexposure_class'),
  pct_dpe_fg: median('pct_dpe_fg'),
  median_income: median('median_income'),
  gp_std: median('gp_std'),
}))

// Department filter (native <select>: keyboard- and screen-reader-ready;
// the visible count is announced through an aria-live region).
const DEPARTMENTS = ['75', '92', '93', '94']
const department = ref('all')
const filterAnnouncement = computed(() =>
  t('ranking.filterCount', { n: listed.value.length })
)

const listed = computed(() =>
  allRows.value
    .filter((p) => nExposures(p) >= 2 && (p.population ?? 0) >= MIN_POPULATION_FOR_LIST)
    .filter((p) => department.value === 'all' || String(p.code_iris).slice(0, 2) === department.value)
    .sort((a, b) => String(a.insee_com).localeCompare(String(b.insee_com)) || a.nom_iris.localeCompare(b.nom_iris))
)

const atMax = computed(() => listed.value.filter((p) => nExposures(p) === 3))
const atThree = computed(() => listed.value.filter((p) => nExposures(p) === 2))

const groups = computed(() =>
  GROUPS.map((g) => ({
    ...g,
    rows: atThree.value.filter((p) => {
      const capacityClass = capacityByIris.value[p.code_iris]?.capacity_class
      return g.capacityClass === null ? capacityClass === null || capacityClass === undefined : capacityClass === g.capacityClass
    }),
  })).filter((g) => g.rows.length)
)

function numberLocale() {
  return locale.value === 'fr' ? 'fr-FR' : 'en-US'
}
function pct(v) {
  return v === null || v === undefined ? '—' : `${new Intl.NumberFormat(numberLocale(), { maximumFractionDigits: 0 }).format(v * 100)}%`
}
function num(v) {
  return v === null || v === undefined ? '—' : new Intl.NumberFormat(numberLocale(), { maximumFractionDigits: 1 }).format(v)
}
function eur(v) {
  return v === null || v === undefined
    ? t('ranking.incomeMasked')
    : new Intl.NumberFormat(numberLocale(), { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v)
}

function figures(p) {
  return [
    { key: 'artif', value: pct(p.pct_artificialized), median: pct(medians.value.pct_artificialized) },
    { key: 'airNoise', value: num(p.air_noise_coexposure_class), median: num(medians.value.air_noise_coexposure_class) },
    { key: 'dpe', value: pct(p.pct_dpe_fg), median: pct(medians.value.pct_dpe_fg) },
    { key: 'gp', value: num(p.gp_std), median: num(medians.value.gp_std) },
    { key: 'income', value: eur(p.median_income), median: eur(medians.value.median_income) },
  ]
}
</script>

<template>
  <div class="ranking-view">
    <router-link class="back-link" :to="{ name: localizedRouteName('methodology', locale) }">{{ t('methodology.backLink') }}</router-link>

    <h1>{{ t('ranking.title') }}</h1>
    <p class="intro">{{ t('ranking.intro') }}</p>
    <p class="intro-split">{{ t('ranking.sameScoreNote') }}</p>
    <p class="tie-notice">{{ t('ranking.tieNotice') }}</p>
    <p class="tie-notice">{{ t('ranking.figuresNote') }}</p>

    <p v-if="loading" class="loading">{{ t('scatter.loading') }}</p>
    <template v-else>
      <div class="filter">
        <label for="dep-filter">{{ t('ranking.filterLabel') }}</label>
        <select id="dep-filter" v-model="department" aria-describedby="filter-count">
          <option value="all">{{ t('ranking.filterAll') }}</option>
          <option v-for="d in DEPARTMENTS" :key="d" :value="d">{{ t(`methodology.dep${d}`) }}</option>
        </select>
        <span id="filter-count" class="filter-count" aria-live="polite">{{ filterAnnouncement }}</span>
      </div>

      <section v-if="atMax.length" class="ranking-group top-group">
        <h2 class="group-title">{{ t('ranking.group_max_title', { n: atMax.length }) }}</h2>
        <p class="group-desc">{{ t('ranking.group_max_desc') }}</p>
        <ol class="ranking-list">
          <li v-for="p in atMax" :key="p.code_iris" class="ranking-row glass">
            <div class="row-head">
              <router-link class="name" :to="{ name: localizedRouteName('neighbourhood', locale), params: { code: p.code_iris } }">{{ p.nom_iris }}</router-link>
              <span class="commune">{{ p.nom_com }}</span>
              <span class="badge">{{ t('ranking.maxBadge') }}</span>
            </div>
            <ul class="figures">
              <li v-for="f in figures(p)" :key="f.key">
                {{ t(`ranking.fig_${f.key}`) }} <span class="fig-value">{{ f.value }}</span>
                <span class="fig-median">{{ t('ranking.metroMedian', { value: f.median }) }}</span>
              </li>
            </ul>
          </li>
        </ol>
      </section>

      <h2 v-if="atThree.length" class="three-title">{{ t('ranking.threeTitle', { n: atThree.length }) }}</h2>
      <section v-for="g in groups" :key="g.key" class="ranking-group">
        <h3 class="group-title">{{ t(`ranking.group_${g.key}_title`, { n: g.rows.length }) }}</h3>
        <p class="group-desc">{{ t(`ranking.group_${g.key}_desc`) }}</p>
        <ol class="ranking-list">
          <li v-for="p in g.rows" :key="p.code_iris" class="ranking-row glass">
            <div class="row-head">
              <router-link class="name" :to="{ name: localizedRouteName('neighbourhood', locale), params: { code: p.code_iris } }">{{ p.nom_iris }}</router-link>
              <span class="commune">{{ p.nom_com }}</span>
            </div>
            <ul class="figures">
              <li v-for="f in figures(p)" :key="f.key">
                {{ t(`ranking.fig_${f.key}`) }} <span class="fig-value">{{ f.value }}</span>
                <span class="fig-median">{{ t('ranking.metroMedian', { value: f.median }) }}</span>
              </li>
            </ul>
          </li>
        </ol>
      </section>
      <p v-if="!listed.length" class="group-desc">{{ t('ranking.filterEmpty') }}</p>
    </template>

    <p v-if="!loading" class="footnote">{{ t('ranking.footnote') }}</p>
  </div>
</template>

<style scoped>
.filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin: 8px 0 24px;
  font-size: 16px;
  color: var(--text-secondary);
}
.filter select {
  background: var(--surface);
  color: var(--text-primary);
  border: 1.5px solid var(--control-border);
  border-radius: 8px;
  padding: 7px 10px;
  font: inherit;
}
.filter select option {
  color: #14161a;
}
.filter-count {
  font-size: 15px;
  color: var(--text-muted);
}
.three-title {
  font-size: 20px;
  margin: 32px 0 6px;
}
.badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  background: var(--accent);
  color: #ffffff;
}
.ranking-view {
  max-width: calc(1000px + 2 * var(--page-gutter));
  padding: 40px var(--page-gutter) 64px;
}
@media (max-width: 920px) {
  .ranking-view {
    padding: 28px 20px 48px;
  }
}

.back-link {
  display: inline-block;
  margin-bottom: 24px;
  font-size: 15px;
  color: var(--text-secondary);
  text-decoration: none;
}
.back-link:hover {
  color: var(--primary);
}

h1 {
  font-weight: 700;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.08;
  margin: 0 0 16px;
  letter-spacing: -0.02em;
}

.intro {
  font-size: 17px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 14px;
}

.tie-notice {
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-muted);
  font-style: italic;
  margin: 0 0 16px;
}

.intro-split {
  font-size: 16px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 28px;
  padding: 14px 16px;
  border-left: 2px solid var(--accent);
  background: var(--surface);
}

.loading {
  color: var(--text-secondary);
  font-size: 15px;
}

.ranking-group {
  margin-bottom: 32px;
}
.ranking-group:last-child {
  margin-bottom: 0;
}

.group-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.group-desc {
  font-size: 15px;
  line-height: 1.55;
  color: var(--text-muted);
  margin: 0 0 14px;
}

.ranking-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-row {
  padding: 16px 20px;
}

.row-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.name {
  font-weight: 700;
  font-size: 17px;
  color: var(--text-primary);
}
.commune {
  font-size: 14px;
  color: var(--text-muted);
}

.gap-sentence {
  margin: 0;
  font-size: 15px;
  line-height: 1.55;
  color: var(--text-secondary);
}

.footnote {
  margin-top: 24px;
  font-size: 14px;
  color: var(--text-muted);
}

.figures {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 16px;
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
}
@media (max-width: 520px) {
  .figures {
    grid-template-columns: 1fr;
  }
}
.figures li {
  font-size: 15px;
  color: var(--text-secondary);
}
.figures .fig-value {
  color: var(--text-primary);
  font-weight: 500;
}
.figures .fig-median {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
