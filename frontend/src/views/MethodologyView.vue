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
    en: 'Why a count of worst-quartile categories instead of an average, what each of the 3 categories measures, why access to services left the score, and the known limits — written for a non-technical reader, with the full technical version linked.',
    fr: "Pourquoi un compte de catégories au pire quartile plutôt qu'une moyenne, ce que mesure chacune des 3 catégories, pourquoi l'accès aux services est sorti du score, et les limites connues — écrit pour un lecteur non technique, avec la version technique complète en lien.",
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
        ? "Explique pourquoi Underlaid compte les catégories au pire quartile plutôt que de faire une moyenne, ce que mesure chacune des 3 catégories, pourquoi l'accès aux services est sorti du score, et les limites connues de la méthode."
        : 'Explains why Underlaid counts worst-quartile categories rather than averaging them, what each of the 3 categories measures, why access to services left the score, and the method\'s known limits.',
    author: { '@type': 'Organization', name: 'Underlaid' },
    publisher: { '@type': 'Organization', name: 'Underlaid' },
    inLanguage: locale,
  }),
})

// Mirrors README "License & data attribution" — each license checked
// against the publisher's own metadata, not assumed. Keep both in sync.
const DATA_SOURCES = [
  { name: { en: 'INSEE — BPE, Filosofi, 2021 census', fr: 'INSEE — BPE, Filosofi, Recensement 2021' }, license: 'lo' },
  { name: { en: 'IGN & INSEE — IRIS boundaries', fr: 'IGN & INSEE — contours IRIS' }, license: 'lo' },
  { name: { en: 'CSTB — Sat4BDNB (urban heat islands)', fr: 'CSTB — Sat4BDNB (îlots de chaleur)' }, license: 'lo' },
  { name: { en: "L'Institut Paris Region — green spaces, MOS land use", fr: "L'Institut Paris Region — espaces verts, MOS" }, license: 'lo' },
  { name: { en: 'Airparif & Bruitparif — air-noise map', fr: 'Airparif & Bruitparif — cartographie air-bruit' }, license: 'airBruit' },
  { name: { en: 'DEPP — Ministry of Education (IPS)', fr: "DEPP — Ministère de l'Éducation nationale (IPS)" }, license: 'lo' },
  { name: { en: 'ADEME — DPE energy certificates', fr: 'ADEME — DPE' }, license: 'lo' },
  { name: { en: 'Enedis — electricity consumption by IRIS', fr: 'Enedis — consommation électrique par IRIS' }, license: 'lo' },
  { name: { en: 'Acceslibre', fr: 'Acceslibre' }, license: 'lo' },
  { name: { en: 'ANCT — priority neighborhoods (QPV)', fr: 'ANCT — quartiers prioritaires (QPV)' }, license: 'lo' },
  { name: { en: 'Ministry of the Interior — RNA', fr: "Ministère de l'Intérieur — RNA" }, license: 'lo' },
  { name: { en: 'Ville de Paris — street trees, public lighting', fr: 'Ville de Paris — arbres, éclairage public' }, license: 'odbl' },
  { name: { en: '© OpenStreetMap contributors — footways, street network', fr: "© les contributeurs d'OpenStreetMap — cheminements piétons, réseau de rues" }, license: 'odbl' },
  { name: { en: 'ANS — RPPS directory of health professionals', fr: 'ANS — répertoire RPPS des professionnels de santé' }, license: 'lo' },
  { name: { en: 'Ministry of Health — FINESS (pharmacies)', fr: 'Ministère de la Santé — FINESS (pharmacies)' }, license: 'lo' },
  { name: { en: 'DREES — APL age weights and decay', fr: 'DREES — pondérations par âge et décroissance de l\'APL' }, license: 'lo' },
  { name: { en: 'Île-de-France Mobilités — public transport timetables (GTFS)', fr: 'Île-de-France Mobilités — horaires des transports en commun (GTFS)' }, license: 'mobilites' },
  { name: { en: 'IGN — BD TOPO (staircases)', fr: 'IGN — BD TOPO (escaliers)' }, license: 'lo' },
  { name: { en: '© CARTO, © OpenStreetMap contributors — basemap', fr: "© CARTO, © les contributeurs d'OpenStreetMap — fond de carte" }, license: 'carto' },
  { name: { en: 'IGN, DINUM — API Adresse (BAN)', fr: 'IGN, DINUM — API Adresse (BAN)' }, license: 'lo' },
]

// Static facts from SCORING.md (scripts/11_compute_vulnerability_score.py's
// output) — not user data, so no fetch: this page describes the method,
// it doesn't recompute or re-derive anything from the live GeoJSON.
const DISTRIBUTION = [
  { score: 0, count: 774, share: 774 / 2752 },
  { score: 1, count: 1286, share: 1286 / 2752 },
  { score: 2, count: 610, share: 610 / 2752 },
  { score: 3, count: 78, share: 78 / 2752 },
  { score: 4, count: 4, share: 4 / 2752 },
]

const SUBSCORES = [
  { key: 'thermal' },
  { key: 'pollution' },
  { key: 'housing' },
  { key: 'accessCare' },
]

const LIMIT_KEYS = [
  'limitIncome', 'limitIcu',
  'limitThermosensitivity', 'limitArtificialization', 'limitEstimate',
]

// OSM sidewalk audit (scripts/analysis/osm_sidewalk_completeness.py,
// Geofabrik extract of 2026-09-30): share of street length with any
// sidewalk information, by density quintile of inhabited IRIS. `few`
// marks departments with fewer than 20 neighborhoods in that band.
const SIDEWALK_DEPS = ['75', '92', '93', '94']
const SIDEWALK_COMPLETENESS = [
  { band: 'all', values: [96.2, 62.7, 25.9, 47.2] },
  { band: 'q1', min: null, max: 7200, values: [83.2, 50.9, 22.8, 35.6] },
  { band: 'q2', min: 7200, max: 12900, values: [97.2, 62.4, 25.7, 60.3] },
  { band: 'q3', min: 12900, max: 21000, values: [97.2, 72.3, 32.0, 61.7] },
  { band: 'q4', min: 21000, max: 34100, values: [98.6, 74.7, 36.7, 73.5] },
  { band: 'q5', min: 34100, max: null, values: [98.8, 82.1, 47.9, 57.2], few: ['93', '94'] },
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

const sidewalkRows = computed(() =>
  SIDEWALK_COMPLETENESS.map((row) => {
    let label
    if (row.band === 'all') label = t('methodology.sidewalkBandAll')
    else if (row.min === null) label = t('methodology.sidewalkBandBelow', { n: formatCount(row.max) })
    else if (row.max === null) label = t('methodology.sidewalkBandAbove', { n: formatCount(row.min) })
    else label = t('methodology.sidewalkBandRange', { min: formatCount(row.min), max: formatCount(row.max) })
    const percent = new Intl.NumberFormat(numberLocale(), { style: 'percent', maximumFractionDigits: 0 })
    return {
      band: row.band,
      label,
      cells: row.values.map((v, i) => ({
        dep: SIDEWALK_DEPS[i],
        text: percent.format(v / 100) + (row.few?.includes(SIDEWALK_DEPS[i]) ? '*' : ''),
      })),
    }
  })
)

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
    <router-link class="back-link" :to="{ name: localizedRouteName('map', locale) }">{{ t('methodology.backLink') }}</router-link>

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

    <section id="means" class="glass">
      <h2>{{ t('methodology.capacityTitle') }}</h2>
      <p>{{ t('methodology.capacityBody1') }}</p>
      <p>{{ t('methodology.capacityBody2') }}</p>
      <p>{{ t('methodology.capacityBody3') }}</p>
      <p>{{ t('methodology.capacityBody4') }}</p>
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

    <section id="access" class="glass">
      <h2>{{ t('methodology.accessOutTitle') }}</h2>
      <p v-for="n in [1, 2, 3, 4, 5]" :key="n">{{ t(`methodology.accessOut${n}`) }}</p>
      <h3 id="osm-sidewalks">{{ t('methodology.sidewalkTitle') }}</h3>
      <p>{{ t('methodology.sidewalkBody1') }}</p>
      <p id="sidewalk-caption" class="table-caption">{{ t('methodology.sidewalkCaption') }}</p>
      <div class="table-scroll">
        <table class="dist-table sidewalk-table" aria-labelledby="sidewalk-caption">
          <thead>
            <tr>
              <th scope="col">{{ t('methodology.sidewalkColDensity') }}</th>
              <th v-for="dep in SIDEWALK_DEPS" :key="dep" scope="col">{{ t(`methodology.dep${dep}`) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in sidewalkRows" :key="row.band">
              <th scope="row">{{ row.label }}</th>
              <td v-for="cell in row.cells" :key="cell.dep">{{ cell.text }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="dist-note">{{ t('methodology.sidewalkNote') }}</p>
      <p>{{ t('methodology.sidewalkBody2') }}</p>
      <p>{{ t('methodology.sidewalkBody3') }}</p>
      <h3 id="access-without-car">{{ t('methodology.carFreeTitle') }}</h3>
      <p>{{ t('methodology.carFreeBody1') }}</p>
      <p>{{ t('methodology.carFreeBody2') }}</p>
      <h3 id="access-rebuilt">{{ t('methodology.accessBackTitle') }}</h3>
      <p>{{ t('methodology.accessBack1') }}</p>
      <p>{{ t('methodology.accessBack2') }}</p>
      <p>{{ t('methodology.accessBack3') }}</p>
      <h3 id="inclusive-mobility">{{ t('methodology.mobilityTitle') }}</h3>
      <p>{{ t('methodology.mobilityBody1') }}</p>
      <p>{{ t('methodology.mobilityBody2') }}</p>
    </section>

    <section class="glass">
      <h2>{{ t('methodology.thresholdTitle') }}</h2>
      <p>{{ t('methodology.thresholdBody1') }}</p>
      <p>{{ t('methodology.thresholdBody2') }}</p>
      <p>{{ t('methodology.thresholdBody3') }}</p>
      <p>{{ t('methodology.thresholdBody4') }}</p>
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

    <section id="data-licences" class="glass">
      <h2>{{ t('methodology.licensesTitle') }}</h2>
      <p>{{ t('methodology.licensesIntro') }}</p>
      <ul class="sources-list">
        <li v-for="source in DATA_SOURCES" :key="source.name.en">
          <span class="source-name">{{ source.name[locale] }}</span>
          <span class="source-license">{{ t(`methodology.license_${source.license}`) }}</span>
        </li>
      </ul>
      <p class="dist-note">{{ t('methodology.licensesNote') }}</p>
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

.sources-list {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}
.sources-list li {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 2px 16px;
  padding: 8px 0;
  border-bottom: 1px solid var(--gridline);
  font-size: 13.5px;
}
.source-license {
  color: var(--text-secondary);
  font-family: var(--mono);
  font-size: 12px;
}
#data-licences {
  scroll-margin-top: 24px;
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

.table-scroll {
  overflow-x: auto;
}
.table-caption {
  font-size: 13px !important;
  color: var(--text-secondary);
  margin-bottom: 0 !important;
}
.sidewalk-table th[scope='row'] {
  font-family: inherit;
  font-size: 13px;
  text-transform: none;
  letter-spacing: normal;
  color: var(--text-primary);
  white-space: nowrap;
}
@media (max-width: 600px) {
  .sidewalk-table th,
  .sidewalk-table td {
    padding: 7px 4px;
    font-size: 12px;
  }
  .sidewalk-table th[scope='col'] {
    font-size: 9.5px;
    letter-spacing: 0.02em;
    hyphens: manual;
  }
}
.sidewalk-table td,
.sidewalk-table td:first-child {
  font-family: inherit;
  font-weight: normal;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
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
