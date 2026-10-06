<script setup>
// "Explorer la carte" (redesign D4, docs/design/refonte-d4/: 04, 04b, 04c,
// 13, 90 — map style B). Left panel: an address, "Que voulez-vous voir ?"
// (six themes), filters combined with AND; the map: real IRIS outlines,
// inner commune boundaries, Paris underlined, the Seine and the Marne, no
// tiles and no grey background; a legend; the selected neighbourhood's card
// on the side opposite to it (desktop) or a sheet from the bottom (phone).
// A sortable, filterable list of the neighbourhoods is the text alternative
// to the map, with the same theme and filters.
//
// Definitions (decision of 3 October 2026): "très exposé" = at least 2 of
// the 3 exposures (heat, air and noise, housing) in the most affected
// quarter; residents' resources: lowest third of the metropolis; access to
// care: most difficult quarter. Ramps validated on white (light end 2:1).
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AddressSearch from '../components/AddressSearch.vue'
import LoadingDots from '../components/LoadingDots.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'
import { findNeighbourhood, rememberNeighbourhood } from '../utils/neighbourhood'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

useSeoMeta({
  image: 'carte',
  title: { en: 'Explore the map', fr: 'Explorer la carte' },
  description: {
    en: 'The 2,752 neighbourhoods of Paris and its inner suburbs: heat, air and noise, housing, access to care, residents’ resources, and where they combine.',
    fr: 'Les 2 752 quartiers de Paris et de la petite couronne : chaleur, air et bruit, logement, accès aux soins, ressources des habitants, et leur cumul.',
  },
})

const MIN_POPULATION = 50
const EXPOSURES = ['thermal', 'pollution', 'housing']
// Ramps checked with the dataviz validator on white (ordinal: one hue,
// monotone lightness, visible steps between neighbours: all pass). The light
// end is at 1.5:1 against white, darker than the mock-ups (about 1.1:1) as
// decided on 3 October 2026, but below the validator's 2:1 floor: at 2:1 the
// whole map turned saturated (most neighbourhoods are in the lightest class).
// Compensated by the white outlines between neighbourhoods, the written
// legend, the card and the list. The 2:1 variant, for reference: cumul
// #f494c8 #ec4aa2 #e4007c #b90066 #8e0050.
const THEMES = {
  cumul: { color: '#E4007C', ramp: ['#f9c2e0', '#ee61ae', '#e4007c', '#b90066', '#8e0050'] },
  thermal: { color: '#FF7A00', ramp: ['#ffc896', '#ff9432', '#cf6100', '#6e3000'] },
  pollution: { color: '#7B3FA0', ramp: ['#ddcde6', '#9c6eb7', '#6c358d', '#4e2266'] },
  housing: { color: '#00A06B', ramp: ['#a6decb', '#37b58b', '#008b5d', '#006240'] },
  access_care: { color: '#00A3E0', ramp: ['#9edcf3', '#35b6e6', '#0080b1', '#003a52'] },
  resources: { color: '#E0A800', ramp: ['#eed075', '#a6873b', '#5e3e00'] },
}
const THEME_IDS = Object.keys(THEMES)
const FILTERS = ['exposed', 'resources', 'care']
const NO_DATA = '#e6e6e6'
const MGP_BOUNDS = [
  [2.15, 48.725],
  [2.61, 48.97],
]
const FEW = '#f3f3f3'

// --- State in the URL (theme, filters, selected neighbourhood code) -------
const theme = computed({
  get: () => (THEME_IDS.includes(route.query.theme) ? route.query.theme : 'cumul'),
  set: (v) => setQuery({ theme: v === 'cumul' ? undefined : v }),
})
const filters = computed({
  get: () => String(route.query.f || '').split(',').filter((f) => FILTERS.includes(f)),
  set: (list) => setQuery({ f: list.length ? FILTERS.filter((f) => list.includes(f)).join(',') : undefined }),
})
const selectedCode = computed(() => (typeof route.query.q === 'string' ? route.query.q : null))
function setQuery(patch) {
  const q = { ...route.query, ...patch }
  for (const k of Object.keys(q)) if (q[k] === undefined) delete q[k]
  router.replace({ query: q })
}
function toggleFilter(f) {
  const set = new Set(filters.value)
  set.has(f) ? set.delete(f) : set.add(f)
  filters.value = [...set]
}

// --- Data ---------------------------------------------------------------------
const loading = ref(true)
const records = shallowRef([]) // one per IRIS, with classes and ranks
const byCode = shallowRef(new Map())
let geojson = null
let layers = null

function rankShares(values) {
  const ref_ = values.filter((v) => v !== null && v !== undefined).sort((a, b) => a - b)
  return (v) => {
    if (v === null || v === undefined) return null
    let lo = 0
    let hi = ref_.length
    while (lo < hi) {
      const mid = (lo + hi) >> 1
      if (ref_[mid] < v) lo = mid + 1
      else hi = mid
    }
    return lo / ref_.length
  }
}

async function loadData() {
  const [score, cap, mapLayers] = await Promise.all([
    // Map-only file (script 39): only the fields read here, 5-decimal outlines.
    loadStaticJson('/data/map_iris.geojson'),
    loadStaticJson('/data/adaptive_capacity_iris.json'),
    loadStaticJson('/data/map_layers.geojson'),
  ])
  layers = mapLayers
  const capByCode = new Map(cap.iris.map((r) => [r.code_iris, r]))
  const props = score.features.map((f) => f.properties)
  const inhabited = (p) => (p.population ?? 0) >= MIN_POPULATION
  const rankers = {}
  for (const k of [...EXPOSURES, 'access_care']) rankers[k] = rankShares(props.filter(inhabited).map((p) => p[`subscore_${k}`]))
  const recs = score.features.map((f) => {
    const p = f.properties
    const c = capByCode.get(p.code_iris)
    const quarter = {}
    const rank = {}
    for (const k of [...EXPOSURES, 'access_care']) {
      quarter[k] = p[`subscore_${k}_quartile`] ?? null
      rank[k] = rankers[k](p[`subscore_${k}`] ?? null)
    }
    const nExp = EXPOSURES.filter((k) => quarter[k] === 4).length
    return {
      code: p.code_iris,
      name: p.nom_iris,
      commune: p.nom_com,
      population: p.population ?? 0,
      inhabited: inhabited(p),
      score: p.cumulative_vulnerability_score ?? null,
      quarter,
      rank,
      nExp,
      third: c?.capacity_class ?? null,
    }
  })
  records.value = recs
  byCode.value = new Map(recs.map((r) => [r.code, r]))
  geojson = { type: 'FeatureCollection', features: score.features.map((f) => ({ type: 'Feature', geometry: f.geometry, properties: { code: f.properties.code_iris } })) }
  loading.value = false
}

// --- Classes and filters ----------------------------------------------------
function colorOf(r, th) {
  if (!r.inhabited) return FEW
  const ramp = THEMES[th].ramp
  if (th === 'cumul') return r.score === null ? NO_DATA : ramp[r.score]
  if (th === 'resources') return r.third === null ? NO_DATA : ramp[2 - r.third]
  const q = r.quarter[th]
  return q === null ? NO_DATA : ramp[q - 1]
}
function passes(r, list) {
  if (!list.length) return true
  if (!r.inhabited) return false
  if (list.includes('exposed') && r.nExp < 2) return false
  if (list.includes('resources') && r.third !== 0) return false
  if (list.includes('care') && r.quarter.access_care !== 4) return false
  return true
}
const kept = computed(() => records.value.filter((r) => passes(r, filters.value)))
const countLabel = computed(() =>
  filters.value.length ? t('explore.count', { n: nf(kept.value.length), total: nf(records.value.length) }) : t('explore.noFilter')
)
const nf = (v) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB').format(v)

// --- Map ------------------------------------------------------------------------
const mapEl = ref(null)
let map = null
const mapReady = ref(false)

function paint() {
  if (!map || !mapReady.value) return
  const th = theme.value
  const list = filters.value
  for (const r of records.value) {
    map.setFeatureState({ source: 'iris', id: r.code }, { color: colorOf(r, th), dim: !passes(r, list) })
  }
}

function initMap() {
  map = new maplibregl.Map({
    container: mapEl.value,
    style: {
      version: 8,
      sources: {},
      layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#ffffff' } }],
    },
    bounds: MGP_BOUNDS,
    fitBoundsOptions: { padding: 24 },
    attributionControl: false,
    // Kept so that the smoke test (and a future image export) can read
    // the drawn map back.
    canvasContextAttributes: { preserveDrawingBuffer: true },
    dragRotate: false,
    pitchWithRotate: false,
  })
  map.touchZoomRotate.disableRotation()
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
  map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: '© OpenStreetMap (Seine, Marne) · INSEE, IGN (contours)' }), 'bottom-right')
  map.on('load', () => {
    map.addSource('iris', { type: 'geojson', data: geojson, promoteId: 'code' })
    map.addSource('layers', { type: 'geojson', data: layers })
    map.addLayer({
      id: 'iris-fill',
      type: 'fill',
      source: 'iris',
      paint: {
        'fill-color': ['coalesce', ['feature-state', 'color'], NO_DATA],
        'fill-opacity': ['case', ['boolean', ['feature-state', 'dim'], false], 0.22, 1],
        'fill-color-transition': { duration: 300 },
        'fill-opacity-transition': { duration: 250 },
      },
    })
    map.addLayer({ id: 'iris-line', type: 'line', source: 'iris', paint: { 'line-color': '#ffffff', 'line-width': 0.6 } })
    map.addLayer({ id: 'communes', type: 'line', source: 'layers', filter: ['==', ['get', 'layer'], 'communes'], paint: { 'line-color': '#8a8a8a', 'line-width': 0.9 } })
    map.addLayer({ id: 'river-casing', type: 'line', source: 'layers', filter: ['==', ['get', 'layer'], 'river'], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#ffffff', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 7, 14, 16] } })
    map.addLayer({ id: 'river', type: 'line', source: 'layers', filter: ['==', ['get', 'layer'], 'river'], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#8db8e8', 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 3.5, 14, 10] } })
    map.addLayer({ id: 'paris', type: 'line', source: 'layers', filter: ['==', ['get', 'layer'], 'paris'], paint: { 'line-color': '#101010', 'line-width': 2.4 } })
    map.addLayer({
      id: 'iris-selected',
      type: 'line',
      source: 'iris',
      filter: ['==', ['get', 'code'], ''],
      paint: { 'line-color': '#101010', 'line-width': 3 },
    })
    // Place names (decorative: the list and the card name every place).
    for (const [name, lngLat, cls] of [
      ['Paris', [2.345, 48.872], 'place-label paris'],
      ['Hauts-de-Seine', [2.205, 48.86], 'place-label'],
      ['Seine-Saint-Denis', [2.53, 48.965], 'place-label'],
      ['Val-de-Marne', [2.5, 48.765], 'place-label'],
    ]) {
      const el = document.createElement('span')
      el.className = cls
      el.textContent = name
      el.setAttribute('aria-hidden', 'true')
      new maplibregl.Marker({ element: el }).setLngLat(lngLat).addTo(map)
    }
    mapReady.value = true
    // Fit the whole metropolis once the container has its final size.
    map.resize()
    // The compact attribution starts open; keep it as an (i) button.
    mapEl.value.querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show')
    map.fitBounds(MGP_BOUNDS, { padding: 40, duration: 0 })
    paint()
    showSelection(false)
  })
  map.on('click', 'iris-fill', (e) => {
    const code = e.features?.[0]?.properties?.code
    if (code) select(code)
  })
  map.on('mouseenter', 'iris-fill', () => (map.getCanvas().style.cursor = 'pointer'))
  map.on('mouseleave', 'iris-fill', () => (map.getCanvas().style.cursor = ''))
}

watch([theme, filters], paint)

// --- Selection --------------------------------------------------------------------
const selected = computed(() => (selectedCode.value ? byCode.value.get(selectedCode.value) ?? null : null))
const cardSide = ref('right')
let marker = null

function bboxOf(code) {
  const f = geojson?.features.find((x) => x.properties.code === code)
  if (!f) return null
  let minX = 180, minY = 90, maxX = -180, maxY = -90
  const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates
  for (const poly of polys) for (const ring of poly) for (const [x, y] of ring) {
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y)
  }
  return [[minX, minY], [maxX, maxY]]
}
function showSelection(fly = true) {
  if (!map || !mapReady.value) return
  map.setFilter('iris-selected', ['==', ['get', 'code'], selectedCode.value || ''])
  if (marker) {
    marker.remove()
    marker = null
  }
  if (!selectedCode.value) return
  const b = bboxOf(selectedCode.value)
  if (!b) return
  const center = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]
  const el = document.createElement('div')
  el.className = 'here-marker'
  el.setAttribute('aria-hidden', 'true')
  marker = new maplibregl.Marker({ element: el }).setLngLat(center).addTo(map)
  // The card goes on the side opposite to the neighbourhood (desktop).
  const px = map.project(center)
  cardSide.value = px.x > mapEl.value.clientWidth / 2 ? 'left' : 'right'
  if (fly && !map.getBounds().contains(center)) map.easeTo({ center, duration: 600 })
}
function select(code) {
  setQuery({ q: code })
}
function closeCard() {
  setQuery({ q: undefined })
  nextTick(() => mapEl.value?.focus())
}
watch(selectedCode, () => showSelection(true))

async function onAddress(a) {
  const r = await findNeighbourhood(a)
  if (!r) {
    addressError.value = t('nbhd.outside')
    return
  }
  addressError.value = ''
  select(r.code)
  const b = bboxOf(r.code)
  if (b && map) map.fitBounds(b, { padding: 120, maxZoom: 14, duration: 600 })
}
const addressError = ref('')

// Card content.
function rankLine(r, k) {
  const share = r.rank[k]
  if (share === null || r.quarter[k] === null) return t('nbhd.rank.missing')
  const n = Math.min(9, Math.max(0, Math.round(share * 10)))
  return k === 'access_care' ? t('explore.card.care', { n }, n) : t('explore.card.exposure', { n }, n)
}
const cardRows = computed(() => {
  const r = selected.value
  if (!r) return []
  return [...EXPOSURES, 'access_care'].map((k) => ({ key: k, label: t(`explore.theme.${k}.short`), text: rankLine(r, k), worst: r.quarter[k] === 4 }))
})

// --- Phone: theme menu, filters sheet, bottom card ----------------------------
const filtersOpen = ref(false)
const filtersButton = ref(null)
const sheetExpanded = ref(false)

// --- Text alternative: the list -----------------------------------------------------
const listOpen = ref(false)
const sortKey = ref('score')
const sortDir = ref(-1)
const listLimit = ref(50)
const SORTABLE = ['name', 'commune', 'score', 'thermal', 'pollution', 'housing', 'access_care', 'third']
function sortValue(r, k) {
  if (k === 'name' || k === 'commune') return r[k]
  if (k === 'score') return r.score ?? -1
  if (k === 'third') return r.third ?? 9
  return r.rank[k] ?? -1
}
const listRows = computed(() => {
  const rows = kept.value.filter((r) => r.inhabited)
  const k = sortKey.value
  const dir = sortDir.value
  return [...rows].sort((a, b) => {
    const va = sortValue(a, k)
    const vb = sortValue(b, k)
    if (typeof va === 'string') return dir * va.localeCompare(vb, 'fr')
    return dir * (va - vb)
  })
})
function sortBy(k) {
  if (sortKey.value === k) sortDir.value = -sortDir.value
  else {
    sortKey.value = k
    sortDir.value = k === 'name' || k === 'commune' ? 1 : -1
  }
  listLimit.value = 50
}
const ariaSort = (k) => (sortKey.value === k ? (sortDir.value === 1 ? 'ascending' : 'descending') : 'none')
const quarterText = (r, k) => (r.quarter[k] === null ? '—' : r.quarter[k] === 4 ? t('explore.list.worst') : t('explore.list.quarter', { q: r.quarter[k] }))
const thirdText = (r) => (r.third === null ? '—' : t(`explore.list.third${r.third}`))

const legend = computed(() => {
  const th = theme.value
  const ramp = THEMES[th].ramp
  return ramp.map((color, i) => ({ color, label: t(`explore.legend.${th}.${i}`) }))
})

onMounted(async () => {
  await loadData()
  await nextTick()
  initMap()
})
// Escape closes the card (or the filters panel on phones) from anywhere.
function onKeydown(e) {
  if (e.key !== 'Escape') return
  if (filtersOpen.value) {
    filtersOpen.value = false
    nextTick(() => filtersButton.value?.focus())
  } else if (selected.value) closeCard()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  map?.remove()
  map = null
})

const pageLink = (code) => ({ name: localizedRouteName('neighbourhood', locale.value), params: { code } })
function openPage(code) {
  rememberNeighbourhood(code)
}
</script>

<template>
  <div class="explore">
    <h1 class="sr-only">{{ t('explore.title') }}</h1>
    <aside class="panel" :aria-label="t('explore.panelLabel')">
      <AddressSearch id="explore-address" compact hide-label :label="t('landing.addressLabel')" :placeholder="t('explore.addressPlaceholder')" @select="onAddress" />
      <p v-if="addressError" class="flag" role="alert">{{ addressError }}</p>

      <div class="themes-desktop">
        <h2 id="themes-title" class="panel-title">{{ t('explore.what') }}</h2>
        <div class="themes" role="radiogroup" aria-labelledby="themes-title">
          <label v-for="th in THEME_IDS" :key="th" class="theme" :class="{ active: theme === th }" :style="{ '--theme-color': THEMES[th].color }">
            <input type="radio" name="theme" class="sr-only" :value="th" :checked="theme === th" @change="theme = th" />
            <span class="theme-ring" aria-hidden="true"></span>
            <span class="theme-text">
              <span class="theme-name">{{ t(`explore.theme.${th}.name`) }}</span>
              <span class="theme-desc">{{ t(`explore.theme.${th}.desc`) }}</span>
            </span>
          </label>
        </div>
      </div>

      <!-- Phone: compact theme menu and filters button -->
      <div class="phone-controls">
        <label class="sr-only" for="theme-select">{{ t('explore.what') }}</label>
        <div class="theme-select-wrap" :style="{ '--theme-color': THEMES[theme].color }">
          <span class="theme-dot" aria-hidden="true"></span>
          <select id="theme-select" class="theme-select" :value="theme" @change="theme = $event.target.value">
            <option v-for="th in THEME_IDS" :key="th" :value="th">{{ t(`explore.theme.${th}.name`) }}</option>
          </select>
        </div>
        <button ref="filtersButton" type="button" class="filters-button" :aria-expanded="filtersOpen ? 'true' : 'false'" aria-controls="filters" @click="filtersOpen = !filtersOpen">
          {{ filters.length ? t('explore.filtersN', { n: filters.length }) : t('explore.filters') }}
        </button>
      </div>

      <p v-if="filters.length" class="phone-count">{{ countLabel }}</p>
      <fieldset id="filters" class="filters" :class="{ open: filtersOpen }">
        <legend>{{ t('explore.showOnly') }}</legend>
        <label v-for="f in FILTERS" :key="f" class="filter">
          <input type="checkbox" :checked="filters.includes(f)" @change="toggleFilter(f)" />
          <span>{{ t(`explore.filter.${f}`) }}</span>
        </label>
        <div class="filters-foot">
          <p class="count" aria-live="polite">{{ countLabel }}</p>
          <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#calcul' }">{{ t('explore.definitions') }}</router-link>
        </div>
      </fieldset>

      <button type="button" class="list-toggle" :aria-expanded="listOpen ? 'true' : 'false'" aria-controls="explore-list" @click="listOpen = !listOpen">
        {{ listOpen ? t('explore.list.hide') : t('explore.list.show') }}
      </button>
    </aside>

    <section class="map-area" :aria-label="t('explore.mapLabel')">
      <div ref="mapEl" class="map" tabindex="-1" role="region" :aria-label="t('explore.mapRegion')"></div>
      <div v-if="loading" class="map-loading"><LoadingDots :label="t('explore.loading')" /></div>
      <p class="sr-only" aria-live="polite">{{ loading ? t('explore.loading') : '' }}</p>
      <p class="sr-only" aria-live="polite">{{ selected ? t('explore.card.announce', { name: selected.name, commune: selected.commune }) : '' }}</p>

      <div class="legend">
        <p class="legend-title">{{ t(`explore.theme.${theme}.name`) }}</p>
        <ul class="legend-items">
          <li v-for="(l, i) in legend" :key="i"><span class="swatch" :style="{ background: l.color }"></span><span>{{ l.label }}</span></li>
        </ul>
        <p class="legend-note">{{ t('explore.legendNote') }}</p>
      </div>
      <p class="map-hint">{{ t('explore.hint') }}</p>

      <section v-if="selected" class="card" :class="[`side-${cardSide}`, { expanded: sheetExpanded }]" aria-labelledby="card-title">
        <button type="button" class="sheet-handle" :aria-label="sheetExpanded ? t('explore.card.collapse') : t('explore.card.expand')" @click="sheetExpanded = !sheetExpanded"><span></span></button>
        <div class="card-head">
          <div>
            <p class="card-kicker">{{ t('explore.card.kicker') }}</p>
            <h2 id="card-title" class="card-title">{{ selected.name }}, {{ selected.commune }}</h2>
          </div>
          <button type="button" class="card-close" :aria-label="t('explore.card.close')" @click="closeCard">
            <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12"><path d="M1.5 1.5l9 9M10.5 1.5l-9 9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" /></svg>
          </button>
        </div>
        <p v-if="!selected.inhabited" class="flag">{{ t('nbhd.fewResidents') }}</p>
        <dl class="card-rows">
          <div class="card-row card-cumul">
            <dt>{{ t('explore.card.cumul') }}</dt>
            <dd>{{ selected.score === null ? '—' : t('explore.card.outOf4', { n: selected.score }) }}</dd>
          </div>
          <div v-for="row in cardRows" :key="row.key" class="card-row">
            <dt>{{ row.label }}</dt>
            <dd :class="{ worst: row.worst }">{{ row.text }}</dd>
          </div>
          <div class="card-row">
            <dt>{{ t('explore.theme.resources.short') }}</dt>
            <dd>{{ thirdText(selected) }}</dd>
          </div>
        </dl>
        <router-link class="primary-button" :to="pageLink(selected.code)" @click="openPage(selected.code)">{{ t('explore.card.open') }}</router-link>
        <p class="sheet-hint">{{ t('explore.card.swipe') }}</p>
      </section>
    </section>

    <section v-if="listOpen" id="explore-list" class="list container" aria-labelledby="list-title">
      <h2 id="list-title">{{ t('explore.list.title') }}</h2>
      <p class="list-intro">{{ t('explore.list.intro', { n: nf(listRows.length) }) }}</p>
      <!-- Focusable: a scrollable region must be reachable with the keyboard. -->
      <div class="table-wrap" tabindex="0" role="region" :aria-label="t('site.tableRegion')">
        <table>
          <thead>
            <tr>
              <th v-for="k in SORTABLE" :key="k" scope="col" :aria-sort="ariaSort(k)">
                <button type="button" class="sort" @click="sortBy(k)">{{ t(`explore.list.col.${k}`) }}<span aria-hidden="true">{{ sortKey === k ? (sortDir === 1 ? ' ↑' : ' ↓') : '' }}</span></button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in listRows.slice(0, listLimit)" :key="r.code">
              <th scope="row"><router-link :to="pageLink(r.code)" @click="openPage(r.code)">{{ r.name }}</router-link></th>
              <td>{{ r.commune }}</td>
              <td>{{ r.score === null ? '—' : t('explore.card.outOf4', { n: r.score }) }}</td>
              <td>{{ quarterText(r, 'thermal') }}</td>
              <td>{{ quarterText(r, 'pollution') }}</td>
              <td>{{ quarterText(r, 'housing') }}</td>
              <td>{{ quarterText(r, 'access_care') }}</td>
              <td>{{ thirdText(r) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button v-if="listRows.length > listLimit" type="button" class="pill-button" @click="listLimit += 100">{{ t('explore.list.more', { n: nf(Math.min(100, listRows.length - listLimit)) }) }}</button>
    </section>
  </div>
</template>

<style scoped>
.explore {
  display: grid;
  grid-template-columns: 420px minmax(0, 1fr);
  border-top: 1px solid var(--line-soft);
}
.panel {
  padding: 32px 32px 32px var(--page-gutter);
  border-right: 1px solid var(--line-soft);
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow-y: auto;
  max-height: calc(100svh - 88px);
}
.panel-title {
  margin: 0 0 14px;
  font-size: 22px;
}
.themes {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.theme {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 16px;
  border: 2px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
}
.theme:hover {
  background: var(--surface-muted);
}
.theme.active {
  border-color: var(--theme-color);
}
.theme:focus-within {
  outline: 3px solid var(--focus);
  outline-offset: 2px;
}
.theme-ring {
  width: 18px;
  height: 18px;
  margin-top: 3px;
  border-radius: 50%;
  border: 3px solid var(--theme-color);
  flex-shrink: 0;
}
.theme.active .theme-ring {
  background: var(--theme-color);
}
.theme-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.theme-name {
  font-weight: 700;
  font-size: 17px;
}
.theme-desc {
  font-size: 14px;
  color: var(--text-secondary);
}
.filters {
  margin: 0;
  padding: 18px 20px;
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.filters legend {
  padding: 0 8px;
  font-weight: 700;
  font-size: 17px;
}
.filter {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 16px;
  cursor: pointer;
  min-height: 32px;
}
.filter input {
  width: 22px;
  height: 22px;
  margin: 1px 0 0;
  accent-color: var(--text-primary);
  flex-shrink: 0;
}
.filters-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-top: 1px solid var(--line);
  padding-top: 12px;
  font-size: 14px;
}
.count {
  margin: 0;
  font-weight: 700;
}
.list-toggle,
.pill-button {
  align-self: flex-start;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 2px solid var(--control-border);
  background: var(--surface);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.list-toggle:hover,
.pill-button:hover {
  border-color: var(--text-primary);
}
.phone-controls,
.phone-count {
  display: none;
}
.map-area {
  position: relative;
  height: calc(100svh - 88px);
  min-height: 520px;
}
.map {
  position: absolute;
  inset: 0;
  background: #fff;
}
.map:focus {
  outline: none;
}
.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  pointer-events: none;
}
:deep(.place-label) {
  font-size: 14px;
  color: var(--text-secondary);
  pointer-events: none;
  text-shadow: 0 0 3px #fff, 0 0 6px #fff, 0 0 9px #fff;
  white-space: nowrap;
}
:deep(.place-label.paris) {
  font-weight: 700;
  font-size: 17px;
  color: var(--text-primary);
}
.legend {
  position: absolute;
  left: 20px;
  bottom: 20px;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 16px 20px;
  max-width: 380px;
}
.legend-title {
  margin: 0 0 10px;
  font-weight: 700;
}
.legend-items {
  display: flex;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.legend-items li {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  flex: 1 1 0;
  min-width: 56px;
}
.swatch {
  height: 14px;
  border-radius: 4px;
}
.legend-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--text-muted);
}
.map-hint {
  position: absolute;
  left: 50%;
  top: 12px;
  transform: translateX(-50%);
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.85);
  padding: 2px 6px;
  border-radius: 6px;
}
.card {
  position: absolute;
  top: 24px;
  width: 380px;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.16);
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card.side-right {
  right: 24px;
}
.card.side-left {
  left: 24px;
}
.sheet-handle,
.sheet-hint {
  display: none;
}
.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.card-kicker {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
.card-title {
  margin: 2px 0 0;
  font-size: 20px;
  line-height: 1.25;
}
.card-close {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 1.5px solid var(--control-border);
  background: var(--surface);
  cursor: pointer;
}
.card-rows {
  margin: 0;
}
.card-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 9px 0;
  border-top: 1px solid var(--line);
  font-size: 15px;
}
.card-row dt {
  flex-shrink: 0;
}
.card-row dd {
  margin: 0;
  text-align: right;
}
.card-row dd.worst {
  color: #b0004f;
  font-weight: 700;
}
.card-cumul dd {
  font-weight: 700;
}
.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 22px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-weight: 700;
  text-decoration: none;
}
.primary-button:hover {
  background: #00469a;
  color: #fff;
}
.flag {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.list {
  grid-column: 1 / -1;
  padding-top: 40px;
  padding-bottom: 40px;
}
.list h2 {
  margin: 0 0 8px;
}
.list-intro {
  margin: 0 0 16px;
  color: var(--text-secondary);
}
.table-wrap {
  overflow-x: auto;
  margin-bottom: 16px;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 14px;
}
th,
td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
thead th {
  padding: 0;
}
.sort {
  width: 100%;
  min-height: 44px;
  padding: 8px 10px;
  border: none;
  background: none;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}
:deep(.here-marker) {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  border: 4px solid #101010;
  box-shadow: inset 0 0 0 4px #fff, inset 0 0 0 9px #101010;
}

@media (max-width: 1024px) {
  .explore {
    grid-template-columns: 360px minmax(0, 1fr);
  }
  .panel {
    padding-left: 32px;
  }
}

/* Phone (ExplorerMobileD4): full-height map, address and compact controls
   on top, filters in a panel, the card as a sheet from the bottom. */
@media (max-width: 760px) {
  .explore {
    grid-template-columns: minmax(0, 1fr);
  }
  .panel {
    padding: 12px 16px;
    gap: 10px;
    border-right: none;
    max-height: none;
    overflow: visible;
  }
  .themes-desktop {
    display: none;
  }
  .phone-controls {
    display: flex;
    gap: 10px;
  }
  .theme-select-wrap {
    position: relative;
    flex: 1;
    /* A select is as wide as its longest option unless allowed to shrink
       (Safari): without this the filters button left the screen. */
    min-width: 0;
    display: flex;
    align-items: center;
    border: 2px solid var(--theme-color);
    border-radius: 999px;
    padding-left: 14px;
  }
  .theme-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--theme-color);
    flex-shrink: 0;
  }
  .theme-select {
    flex: 1;
    min-width: 0;
    width: 100%;
    text-overflow: ellipsis;
    min-height: 48px;
    border: none;
    background: transparent;
    font: inherit;
    font-weight: 700;
    padding: 0 12px 0 8px;
    color: var(--text-primary);
  }
  .phone-count {
    display: block;
    margin: 0;
    font-size: 14px;
    font-weight: 700;
  }
  .filters-button {
    flex-shrink: 0;
    white-space: nowrap;
    min-height: 48px;
    padding: 0 18px;
    border-radius: 999px;
    border: none;
    background: var(--text-primary);
    color: #fff;
    font: inherit;
    font-weight: 700;
  }
  .filters {
    display: none;
  }
  .filters.open {
    display: flex;
  }
  .list-toggle {
    align-self: stretch;
  }
  .map-area {
    height: 64svh;
    min-height: 380px;
  }
  .legend {
    left: 8px;
    right: 8px;
    bottom: 8px;
    max-width: none;
    padding: 10px 12px;
  }
  .legend-items li {
    min-width: 0;
    flex: 1;
  }
  .legend-note,
  .map-hint {
    display: none;
  }
  .card {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    top: auto;
    width: auto;
    max-height: 46svh;
    overflow-y: auto;
    border-radius: 24px 24px 0 0;
    padding: 10px 16px 18px;
    z-index: 60;
  }
  .card.expanded {
    max-height: 88svh;
  }
  .card.side-left {
    left: 0;
  }
  .card.side-right {
    right: 0;
  }
  .sheet-handle {
    display: flex;
    justify-content: center;
    align-items: center;
    align-self: center;
    width: 64px;
    height: 24px;
    border: none;
    background: none;
    cursor: pointer;
  }
  .sheet-handle span {
    width: 40px;
    height: 5px;
    border-radius: 3px;
    background: #c9c9c9;
  }
  .sheet-hint {
    display: block;
    margin: 0;
    text-align: center;
    font-size: 13px;
    color: var(--text-muted);
  }
}
</style>
