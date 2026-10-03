<script setup>
// "By address" page (mock-up docs/maquettes/Adresse.dc.html): the
// neighbourhood that contains an address, its cumulative score on one
// line, then six criteria placed against the metro-wide median, a travel
// mode switch (only access to care and transport depend on it), an
// optional comparison with another address, and residents' means apart.
//
// Positions: rank of the neighbourhood among the inhabited neighbourhoods
// (>= 50 residents), oriented so that the right-hand side is always "less
// favourable"; the median is the middle of the scale. The figure behind
// each position is written out in the row, with its metro-wide median.
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import booleanPointInPolygon from '@turf/boolean-point-in-polygon'
import AddressSearch from '../components/AddressSearch.vue'
import FigureSource from '../components/FigureSource.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

useSeoMeta({
  title: { en: 'Look up a neighbourhood', fr: 'Consulter un quartier' },
  description: {
    en: 'Enter an address in Paris or its inner suburbs: heat, air pollution and noise, housing, cool places, access to care and step-free travel for that neighbourhood, compared with the metro-wide median.',
    fr: "Saisissez une adresse à Paris ou en petite couronne : chaleur, pollution de l'air et bruit, logement, lieux frais, accès aux soins et déplacements sans marches pour ce quartier, comparés à la médiane métropolitaine.",
  },
})

const MIN_POPULATION = 50
const CATEGORY_KEYS = ['thermal', 'pollution', 'housing', 'access_care']

const features = ref(null)
const capacity = ref(null)
const loadError = ref(false)
const mode = ref('standard')
const main = ref(null) // { label, feature }
const other = ref(null)
const compareOpen = ref(false)
const notFound = ref('')

onMounted(async () => {
  try {
    const [geojson, cap] = await Promise.all([
      loadStaticJson('/data/vulnerability_score_iris.geojson'),
      loadStaticJson('/data/adaptive_capacity_iris.json'),
    ])
    features.value = geojson.features
    capacity.value = Object.fromEntries(cap.iris.map((r) => [r.code_iris, r]))
    const q = route.query
    if (q.lon && q.lat) locate({ label: String(q.label ?? ''), lon: Number(q.lon), lat: Number(q.lat) }, 'main', false)
    if (q.cmp_lon && q.cmp_lat) {
      compareOpen.value = true
      locate({ label: String(q.cmp_label ?? ''), lon: Number(q.cmp_lon), lat: Number(q.cmp_lat) }, 'other', false)
    }
  } catch {
    loadError.value = true
  }
})

function findFeature(lon, lat) {
  return features.value?.find((f) => booleanPointInPolygon([lon, lat], f.geometry)) ?? null
}

function locate({ label, lon, lat }, which = 'main', updateUrl = true) {
  const feature = findFeature(lon, lat)
  if (which === 'main') {
    notFound.value = feature ? '' : t('addressPage.outside')
    main.value = feature ? { label, feature } : null
  } else {
    other.value = feature ? { label, feature } : null
  }
  if (updateUrl && feature) {
    const query = { ...route.query }
    const prefix = which === 'main' ? '' : 'cmp_'
    Object.assign(query, { [`${prefix}lon`]: lon, [`${prefix}lat`]: lat, [`${prefix}label`]: label })
    router.replace({ query })
  }
}

function closeCompare() {
  compareOpen.value = false
  other.value = null
  const { cmp_lon, cmp_lat, cmp_label, ...rest } = route.query
  router.replace({ query: rest })
}

// --- Reference distributions over inhabited neighbourhoods ---------------

const inhabited = computed(() => (features.value ?? []).map((f) => f.properties).filter((p) => (p.population ?? 0) >= MIN_POPULATION))

function sortedValues(getter) {
  return inhabited.value
    .map(getter)
    .filter((v) => v !== null && v !== undefined && !Number.isNaN(v))
    .sort((a, b) => a - b)
}
function median(sorted) {
  if (!sorted.length) return null
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
}
// Percentile rank (0-100) of x in a sorted list, ties counted half.
function rank(sorted, x) {
  if (x === null || x === undefined || Number.isNaN(x) || !sorted.length) return null
  let below = 0
  let equal = 0
  for (const v of sorted) {
    if (v < x) below++
    else if (v === x) equal++
  }
  return (100 * (below + equal / 2)) / sorted.length
}

// Each criterion: `bad` gives the value oriented "higher = less
// favourable" (used for the position); `shown` the figures written out.
const CRITERIA = {
  thermal: { bad: (p) => p.subscore_thermal },
  pollution: { bad: (p) => p.subscore_pollution },
  housing: { bad: (p) => p.subscore_housing },
  cool: { bad: null }, // mean rank of two indicators, see coolRank()
  care_standard: { bad: (p) => p.subscore_access_care },
  care_step_free: { bad: (p) => (p.gp_acc_no == null ? null : -p.gp_acc_no) },
  transport: { bad: (p) => (p.gp_gap_no == null ? null : -p.gp_gap_no) },
}
const sorted = computed(() => {
  const out = {}
  for (const [k, c] of Object.entries(CRITERIA)) if (c.bad) out[k] = sortedValues(c.bad)
  for (const k of ['pct_artificialized', 'air_noise_coexposure_class', 'pct_dpe_fg', 'cool_spots_within_400m', 'pct_cool_green_area', 'gp_std', 'pharmacy_std', 'gp_acc_no', 'gp_gap_no']) {
    out[k] = sortedValues((p) => p[k])
  }
  return out
})
const medians = computed(() => Object.fromEntries(Object.entries(sorted.value).map(([k, v]) => [k, median(v)])))

function coolRank(p) {
  // Fewer cool places and less cool green space = less favourable.
  const a = rank(sorted.value.cool_spots_within_400m, p.cool_spots_within_400m)
  const b = rank(sorted.value.pct_cool_green_area, p.pct_cool_green_area)
  if (a === null || b === null) return null
  return 100 - (a + b) / 2
}

const nf = (v, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v)
    ? '—'
    : new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v)
const pct = (v, digits = 0) =>
  v === null || v === undefined || Number.isNaN(v)
    ? '—'
    : new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { style: 'percent', maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v / 100)

// Shares stored as fractions (0-1) in the published data.
const frac = (v, digits = 0) => pct(v === null || v === undefined ? v : 100 * v, digits)

function positions(p) {
  const care = mode.value === 'standard' ? 'care_standard' : 'care_step_free'
  return {
    thermal: rank(sorted.value.thermal, CRITERIA.thermal.bad(p)),
    pollution: rank(sorted.value.pollution, CRITERIA.pollution.bad(p)),
    housing: rank(sorted.value.housing, CRITERIA.housing.bad(p)),
    cool: coolRank(p),
    care: rank(sorted.value[care], CRITERIA[care].bad(p)),
    transport: rank(sorted.value.transport, CRITERIA.transport.bad(p)),
  }
}

const rows = computed(() => {
  if (!main.value) return []
  const p = main.value.feature.properties
  const m = medians.value
  const pos = positions(p)
  const posOther = other.value ? positions(other.value.feature.properties) : {}
  const stepFree = mode.value !== 'standard'
  const list = [
    { key: 'thermal', text: t('addressPage.rows.thermal', { v: frac(p.pct_artificialized), m: frac(m.pct_artificialized) }), scope: t('addressPage.scope.thermal') },
    { key: 'pollution', text: t('addressPage.rows.pollution', { v: nf(p.air_noise_coexposure_class, 1), m: nf(m.air_noise_coexposure_class, 1) }) },
    { key: 'housing', text: t('addressPage.rows.housing', { v: frac(p.pct_dpe_fg), m: frac(m.pct_dpe_fg) }), scope: t('addressPage.scope.housing') },
    {
      key: 'cool',
      text: t('addressPage.rows.cool', { n: nf(p.cool_spots_within_400m), mn: nf(m.cool_spots_within_400m), g: frac(p.pct_cool_green_area, 1), mg: frac(m.pct_cool_green_area, 1) }),
    },
    {
      key: 'care',
      variesWithMode: true,
      text: stepFree
        ? t('addressPage.rows.careStepFree', { v: nf(p.gp_acc_no, 1), m: nf(m.gp_acc_no, 1) })
        : t('addressPage.rows.care', { gp: nf(p.gp_std, 1), mgp: nf(m.gp_std, 1), ph: nf(p.pharmacy_std, 1), mph: nf(m.pharmacy_std, 1) }),
    },
    {
      key: 'transport',
      variesWithMode: true,
      info: true,
      text: t('addressPage.rows.transport', { v: pct(p.gp_gap_no == null ? null : 100 * p.gp_gap_no), m: pct(m.gp_gap_no == null ? null : 100 * m.gp_gap_no) }),
    },
  ]
  return list.map((r) => ({
    ...r,
    title: t(`addressPage.titles.${r.key}`),
    position: pos[r.key],
    otherPosition: posOther[r.key] ?? null,
    positionText: positionText(pos[r.key]),
    otherPositionText: other.value ? positionText(posOther[r.key]) : '',
  }))
})

function positionText(position) {
  if (position === null || position === undefined) return t('addressPage.noData')
  const r = Math.round(position)
  return r >= 50 ? t('addressPage.lessFavourable', { n: r }) : t('addressPage.moreFavourable', { n: 100 - r })
}

// Information-only rows (transport) are not counted in the summary.
// Two blocks (redesign, 2 October 2026): what the neighbourhood is exposed
// to (independent of how one travels) and what can be reached from it
// (depends on the travel mode, hence the mode switch inside that block).
const EXPOSURE_KEYS = ['thermal', 'pollution', 'housing', 'cool']
const blocks = computed(() => [
  { key: 'exposure', rows: rows.value.filter((r) => EXPOSURE_KEYS.includes(r.key)) },
  { key: 'access', rows: rows.value.filter((r) => !EXPOSURE_KEYS.includes(r.key)) },
])

const worseCount = computed(() => rows.value.filter((r) => !r.info && r.position !== null && r.position > 50).length)
const ratedCount = computed(() => rows.value.filter((r) => !r.info && r.position !== null).length)

const scoreLine = computed(() => {
  if (!main.value) return null
  const p = main.value.feature.properties
  const score = p.cumulative_vulnerability_score
  if (score === null || score === undefined) return { text: t('addressPage.scoreUnknown') }
  const domains = CATEGORY_KEYS.filter((k) => p[`subscore_${k}_quartile`] === 4).map((k) => t(`method.calc.cat.${k}`).toLowerCase())
  return {
    text: domains.length
      ? t('addressPage.score', { score, domains: domains.join(locale.value === 'fr' ? ', ' : ', ') })
      : t('addressPage.scoreZero', { score }),
  }
})

const means = computed(() => {
  if (!main.value || !capacity.value) return null
  const c = capacity.value[main.value.feature.properties.code_iris]
  if (!c || c.capacity_class === null || c.capacity_class === undefined) return t('addressPage.meansMasked')
  return t('addressPage.means', { third: t(`addressPage.third${c.capacity_class}`) })
})

const sparse = computed(() => main.value && (main.value.feature.properties.population ?? 0) < MIN_POPULATION)

const markerStyle = (position) => ({ left: `calc(${position}% - 10px)` })

watch(locale, () => {
  notFound.value = ''
})
</script>

<template>
  <div class="address-page container">
    <section class="head">
      <p class="eyebrow">{{ t('site.nav.address') }}</p>
      <template v-if="main">
        <p class="typed">{{ main.label }}</p>
        <h1>{{ main.feature.properties.nom_iris }}, {{ main.feature.properties.nom_com }}</h1>
        <p class="score-line">
          {{ scoreLine.text }}
          <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#calcul' }">{{ t('addressPage.scoreLink') }}</router-link>
        </p>
        <p v-if="sparse" class="flag">{{ t('panel.sparselyPopulated') }}</p>
      </template>
      <h1 v-else>{{ t('addressPage.title') }}</h1>
      <AddressSearch id="address-main" :label="main ? t('addressPage.another') : t('address.label')" :placeholder="t('address.placeholder')" @select="(a) => locate(a, 'main')" />
      <p v-if="notFound" class="flag" role="status">{{ notFound }}</p>
      <p v-if="loadError" class="flag" role="status">{{ t('addressPage.loadError') }}</p>
    </section>

    <template v-if="main">
      <p class="summary">
        <i18n-t keypath="addressPage.summary" tag="span">
          <template #n><strong class="accent">{{ worseCount }}</strong></template>
          <template #total>{{ ratedCount }}</template>
        </i18n-t>
      </p>

      <section class="compare">
        <button v-if="!compareOpen" type="button" class="pill-btn" @click="compareOpen = true">{{ t('addressPage.compare') }}</button>
        <template v-else>
          <div class="compare-row">
            <AddressSearch id="address-other" :label="t('addressPage.compareLabel')" :placeholder="t('address.placeholder')" @select="(a) => locate(a, 'other')" />
            <button type="button" class="pill-btn" @click="closeCompare">{{ t('addressPage.compareClose') }}</button>
          </div>
        </template>
      </section>

      <ul class="legend" role="list" :aria-label="t('addressPage.legendLabel')">
        <li class="key"><span class="dot bad" aria-hidden="true"></span>{{ t('addressPage.legendWorse', { name: main.feature.properties.nom_iris }) }}</li>
        <li class="key"><span class="dot main" aria-hidden="true"></span>{{ t('addressPage.legendBetter', { name: main.feature.properties.nom_iris }) }}</li>
        <li v-if="other" class="key"><span class="dot other" aria-hidden="true"></span>{{ other.feature.properties.nom_iris }}, {{ other.feature.properties.nom_com }}</li>
      </ul>

      <section v-for="block in blocks" :key="block.key" class="block" :aria-labelledby="`block-${block.key}`">
        <div class="block-head">
          <div>
            <h2 :id="`block-${block.key}`">{{ t(`addressPage.blocks.${block.key}.title`) }}</h2>
            <p class="block-intro">{{ t(`addressPage.blocks.${block.key}.intro`) }}</p>
          </div>
          <div v-if="block.key === 'access'" class="mode">
            <span id="mode-label" class="mode-label">{{ t('addressPage.modeLabel') }}</span>
            <div class="segmented" role="group" aria-labelledby="mode-label">
              <button type="button" :aria-pressed="mode === 'standard'" @click="mode = 'standard'">{{ t('addressPage.modeStandard') }}</button>
              <button type="button" :aria-pressed="mode === 'stepFree'" @click="mode = 'stepFree'">{{ t('addressPage.modeStepFree') }}</button>
            </div>
            <p class="lower-bound">{{ t('routes.lowerBound') }}</p>
          </div>
        </div>

        <div class="scale-head" aria-hidden="true">
          <span>{{ t('addressPage.moreFav') }}</span>
          <span>{{ t('addressPage.median') }}</span>
          <span>{{ t('addressPage.lessFav') }}</span>
        </div>

        <ul class="rows" role="list">
          <li v-for="r in block.rows" :key="r.key" class="criterion-row">
            <div class="row-text">
              <h3>{{ r.title }}<span v-if="r.info" class="tag">{{ t('addressPage.infoTag') }}</span></h3>
              <p>{{ r.text }}</p>
              <p v-if="r.scope" class="scope">{{ r.scope }}</p>
            </div>
            <div class="row-scale">
              <div class="track" aria-hidden="true">
                <span class="line"></span>
                <span class="mid"></span>
                <span v-if="r.otherPosition !== null && other" class="marker other" :style="markerStyle(r.otherPosition)"></span>
                <span v-if="r.position !== null" class="marker" :class="{ bad: r.position > 50 }" :style="markerStyle(r.position)"></span>
              </div>
              <p class="pos-text">{{ r.positionText }}<template v-if="other"> · {{ t('addressPage.otherPos', { name: other.feature.properties.nom_iris, text: r.otherPositionText }) }}</template></p>
            </div>
          </li>
        </ul>
      </section>

      <div class="means">
        <p>{{ means }}</p>
        <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#calcul' }">{{ t('addressPage.meansLink') }}</router-link>
      </div>

      <p class="note">{{ t('addressPage.note', { n: nf(inhabited.length) }) }}</p>
      <FigureSource :sources="t('addressPage.sources')" anchor="sources" />
      <p class="links">
        <router-link :to="{ name: localizedRouteName('map', locale), query: route.query.lon ? { lon: route.query.lon, lat: route.query.lat, label: route.query.label } : {} }">{{ t('addressPage.onMap') }}</router-link>
      </p>
    </template>
  </div>
</template>

<style scoped>
.address-page {
  padding-top: 32px;
  padding-bottom: 48px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.head {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.eyebrow {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
.typed {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}
h1 {
  margin: 0 0 6px;
  font-size: clamp(34px, 5vw, 52px);
  letter-spacing: -0.03em;
  font-weight: 800;
  line-height: 1.05;
}
.score-line {
  margin: 0 0 12px;
  font-size: 19px;
  line-height: 1.45;
  color: var(--text-body);
}
.score-line a {
  margin-left: 6px;
  font-size: 15px;
  white-space: nowrap;
}
.flag {
  margin: 0;
  font-size: 15px;
  color: var(--accent);
}

.block {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}
.block-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px 32px;
  flex-wrap: wrap;
}
.block-head h2 {
  margin: 0;
  font-size: 26px;
  letter-spacing: -0.02em;
}
.block-intro {
  margin: 6px 0 0;
  font-size: 15px;
  color: var(--text-body);
  max-width: 560px;
}
.controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px 32px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.summary {
  margin: 0;
  font-size: 19px;
  color: var(--text-body);
  max-width: 560px;
}
.accent {
  color: var(--accent);
}
.mode {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.lower-bound {
  margin: 4px 0 0;
  max-width: 460px;
  font-size: 13px;
  line-height: 1.45;
  color: var(--text-secondary);
}
.mode-label {
  font-size: 14px;
  font-weight: 600;
}
.segmented {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
  border-radius: 14px;
  background: var(--surface-muted);
}
.segmented button {
  min-height: 44px;
  padding: 0 16px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text-primary);
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.segmented button[aria-pressed='true'] {
  background: var(--dark);
  color: #ffffff;
}

.compare {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.compare-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.pill-btn {
  align-self: flex-start;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 1.5px solid var(--control-border);
  background: var(--surface);
  color: var(--text-primary);
  font: inherit;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.compare-row .pill-btn {
  margin-top: 33px;
}
.legend {
  display: flex;
  gap: 8px 20px;
  flex-wrap: wrap;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 14px;
  color: var(--text-body);
}
.scope {
  margin-top: 4px !important;
  font-size: 13px !important;
  color: var(--text-secondary) !important;
}
.key {
  display: flex;
  gap: 6px;
  align-items: center;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.dot.main {
  background: var(--dark);
}
.dot.bad {
  background: var(--accent);
}
.dot.other {
  border: 2.5px solid var(--focus);
  background: #ffffff;
}

.scale-head {
  display: flex;
  justify-content: space-between;
  margin-left: auto;
  width: min(520px, 100%);
  font-size: 13px;
  color: var(--text-secondary);
}
.rows {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.criterion-row {
  background: var(--surface);
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.row-text {
  flex: 1;
  min-width: 0;
}
.row-text h3 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0;
}
.row-text p {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-body);
}
.tag {
  margin-left: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--control-border);
  font-size: 12px;
  font-weight: 600;
  vertical-align: middle;
  color: var(--text-secondary);
}
.row-scale {
  width: 520px;
  flex-shrink: 0;
}
.track {
  position: relative;
  height: 28px;
}
.line {
  position: absolute;
  left: 0;
  right: 0;
  top: 12px;
  height: 4px;
  border-radius: 2px;
  background: var(--surface-muted);
}
.mid {
  position: absolute;
  left: 50%;
  top: 4px;
  width: 2px;
  height: 20px;
  background: var(--control-border);
}
.marker {
  position: absolute;
  top: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 3px solid #ffffff;
  box-shadow: 0 0 0 1px var(--control-border);
  background: var(--dark);
  transition: left 300ms;
}
.marker.bad {
  background: var(--accent);
}
.marker.other {
  top: 6px;
  width: 16px;
  height: 16px;
  border: 2.5px solid var(--focus);
  background: #ffffff;
  box-shadow: none;
}
.pos-text {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.means {
  background: var(--dark);
  color: #ffffff;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px 24px;
  flex-wrap: wrap;
}
.means p {
  margin: 0;
  font-size: 17px;
  line-height: 1.45;
  max-width: 760px;
}
.means a {
  color: #ffffff;
  font-weight: 600;
  font-size: 15px;
}
.means :focus-visible {
  outline-color: #ffffff;
}
.note {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.links {
  margin: 0;
  font-weight: 600;
}

@media (max-width: 900px) {
  .criterion-row {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }
  .row-scale,
  .scale-head {
    width: 100%;
  }
  .scale-head {
    display: none;
  }
  .compare-row .pill-btn {
    margin-top: 0;
  }
}
</style>
