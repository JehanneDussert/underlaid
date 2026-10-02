<script setup>
// Routes page (mock-up docs/maquettes/Trajet.dc.html, adapted to option A:
// precomputed times from each neighbourhood to the nearest key
// destinations, no free A-to-B trip). Pre-registered on 2026-10-02
// (CLAUDE.md, "Hypothèse de travail"): profiles, time slots, destinations,
// population-weighted median of the neighbourhood's 200 m cells, 90 min
// cap, imposed detour = step-free time minus standard time.
// Data: public/data/routes_iris_<slot>.json and routes_stations_iris.json
// (scripts 33, 34, 36).
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import booleanPointInPolygon from '@turf/boolean-point-in-polygon'
import AddressSearch from '../components/AddressSearch.vue'
import FigureSource from '../components/FigureSource.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()

useSeoMeta({
  title: { en: 'Routes: one trip, unequal durations', fr: 'Itinéraires : un même trajet, des durées inégales' },
  description: {
    en: 'From each neighbourhood of Paris and its inner suburbs, travel time to the nearest hospital, GP, town hall, CAF, CPAM and other key destinations, without constraint, walking slowly or step-free, by time of day.',
    fr: "Depuis chaque quartier de Paris et de la petite couronne, durée jusqu'à l'hôpital, au médecin, à la mairie, à la CAF, à la CPAM et aux autres destinations clés les plus proches, sans contrainte, en marchant lentement ou sans marches, selon l'heure.",
  },
})

const TYPES = ['emergency', 'gp', 'pharmacy', 'town_hall', 'france_services', 'caf', 'cpam', 'employment', 'post_office', 'station']
const SLOTS = ['tue10', 'tue21', 'tue01', 'sun10']
const PROFILES = ['standard', 'slow', 'step_free_no']

const destination = ref('emergency')
const slot = ref('tue10')
const place = ref(null) // { label, code, name, commune }
const features = ref(null)
const slotData = ref({})
const stations = ref(null)
const unavailable = ref(false)
const notFound = ref('')

async function ensureFeatures() {
  if (!features.value) features.value = (await loadStaticJson('/data/vulnerability_score_iris.geojson')).features
}
async function ensureSlot(s) {
  if (slotData.value[s]) return
  try {
    slotData.value = { ...slotData.value, [s]: await loadStaticJson(`/data/routes_iris_${s}.json`) }
  } catch {
    unavailable.value = true
  }
}
async function ensureStations() {
  if (stations.value) return
  try {
    stations.value = await loadStaticJson('/data/routes_stations_iris.json')
  } catch {
    unavailable.value = true
  }
}

async function locate({ label, lon, lat }) {
  await ensureFeatures()
  const f = features.value.find((x) => booleanPointInPolygon([lon, lat], x.geometry))
  if (!f) {
    notFound.value = t('addressPage.outside')
    place.value = null
    return
  }
  notFound.value = ''
  place.value = { label, code: f.properties.code_iris, name: f.properties.nom_iris, commune: f.properties.nom_com }
  await Promise.all([ensureSlot(slot.value), ensureStations()])
}

watch(slot, (s) => {
  if (place.value) ensureSlot(s)
})

const isStation = computed(() => destination.value === 'station')

// Values for the selected neighbourhood, destination and slot.
const values = computed(() => {
  if (!place.value) return null
  if (isStation.value) {
    const row = stations.value?.iris?.[place.value.code]
    if (!row) return null
    const at = (p) => row[stations.value.profiles.indexOf(p)] ?? null
    return { times: Object.fromEntries([...PROFILES, 'step_free_yes'].map((p) => [p, at(p)])), detour: null }
  }
  const data = slotData.value[slot.value]
  const row = data?.iris?.[place.value.code]
  if (!row) return null
  const { blocks, types } = data.layout
  const ti = types.indexOf(destination.value)
  const at = (block) => row[blocks.indexOf(block) * types.length + ti] ?? null
  return {
    times: Object.fromEntries([...PROFILES, 'step_free_yes'].map((p) => [p, at(`time:${p}`)])),
    detour: { no: at('detour:step_free_no'), yes: at('detour:step_free_yes') },
  }
})

const fmt = (v, digits = 1) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: digits }).format(v)
const minutes = (v) => (v === null || v === undefined ? t('routes.over90') : t('routes.minutes', { n: v }))
const barWidth = (v) => `${v === null || v === undefined ? 100 : Math.max(2, (100 * v) / 90)}%`

const ratio = computed(() => {
  const v = values.value?.times
  if (!v || !v.standard || v.step_free_no === null) return null
  const r = v.step_free_no / v.standard
  return r >= 1.05 ? fmt(r) : null
})
</script>

<template>
  <div class="routes container">
    <section class="head">
      <p class="eyebrow">{{ t('site.nav.routes') }}</p>
      <h1>{{ t('routes.title') }}</h1>
      <p class="lead">{{ t('routes.lead') }}</p>
    </section>

    <section class="form card" :aria-label="t('routes.formLabel')">
      <AddressSearch id="routes-address" :label="t('routes.from')" :placeholder="t('address.placeholder')" @select="locate" />
      <div class="field">
        <label for="routes-dest" class="label">{{ t('routes.to') }}</label>
        <select id="routes-dest" v-model="destination">
          <option v-for="ty in TYPES" :key="ty" :value="ty">{{ t(`routes.types.${ty}`) }}</option>
        </select>
      </div>
      <div class="field">
        <span id="slot-label" class="label">{{ t('routes.when') }}</span>
        <div class="segmented" role="group" aria-labelledby="slot-label">
          <button v-for="s in SLOTS" :key="s" type="button" :aria-pressed="slot === s" :disabled="isStation" @click="slot = s">{{ t(`routes.slots.${s}`) }}</button>
        </div>
        <p v-if="isStation" class="hint">{{ t('routes.stationNoSlot') }}</p>
      </div>
      <p v-if="notFound" class="flag" role="status">{{ notFound }}</p>
    </section>

    <section v-if="place" class="card result" aria-live="polite">
      <h2>{{ t('routes.resultTitle', { dest: t(`routes.types.${destination}`), name: place.name, commune: place.commune }) }}</h2>
      <p v-if="unavailable" class="flag">{{ t('routes.unavailable') }}</p>
      <template v-else-if="values">
        <ul class="bars" role="list">
          <li v-for="p in PROFILES" :key="p">
            <span class="bar-label"><span>{{ t(`routes.profiles.${p}`) }}</span><strong>{{ minutes(values.times[p]) }}</strong></span>
            <span class="track" aria-hidden="true"><span class="fill" :class="p" :style="{ width: barWidth(values.times[p]) }"></span></span>
          </li>
        </ul>
        <p v-if="ratio" class="ratio">{{ t('routes.ratio', { n: ratio }) }}</p>
        <p v-if="values.detour && values.detour.no !== null && values.detour.no > 0" class="detail">{{ t('routes.detour', { n: values.detour.no }) }}</p>
        <p class="detail">{{ t('routes.variant', { v: minutes(values.times.step_free_yes) }) }}</p>
      </template>
      <p v-else class="flag">{{ t('routes.noValue') }}</p>
      <p class="note">{{ t('routes.note') }}</p>
      <FigureSource :sources="t('routes.sources')" anchor="sources" :show-date="false" />
    </section>
  </div>
</template>

<style scoped>
.routes {
  padding-top: 32px;
  padding-bottom: 48px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.head {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.eyebrow {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.04;
  letter-spacing: -0.03em;
  font-weight: 800;
  max-width: 820px;
}
.lead {
  margin: 0;
  font-size: 19px;
  line-height: 1.5;
  color: var(--text-body);
  max-width: 720px;
}
.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.label {
  font-size: 15px;
  font-weight: 600;
}
select {
  max-width: 420px;
  height: 52px;
  padding: 0 14px;
  border: 1.5px solid var(--dark);
  border-radius: var(--radius-small);
  background: var(--surface);
  color: var(--text-primary);
  font: inherit;
  font-size: 16px;
}
.segmented {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px;
  border-radius: 14px;
  background: var(--surface-muted);
  align-self: flex-start;
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
.segmented button:disabled {
  color: var(--text-secondary);
  cursor: default;
}
.hint,
.note,
.detail {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.flag {
  margin: 0;
  color: var(--accent);
}
.result h2 {
  margin: 0;
  font-size: 24px;
  letter-spacing: -0.02em;
}
.bars {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.bars li {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bar-label {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 16px;
}
.track {
  height: 16px;
  border-radius: 4px;
  background: var(--line-soft);
}
.fill {
  display: block;
  height: 16px;
  border-radius: 4px;
  background: var(--dark);
}
.fill.slow {
  background: #5b616b;
}
.fill.step_free_no {
  background: var(--accent);
}
.ratio {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}
</style>
