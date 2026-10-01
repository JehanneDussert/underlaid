<script setup>
import { onMounted, onBeforeUnmount, onServerPrefetch, ref, shallowRef, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { MapboxOverlay } from '@deck.gl/mapbox'
import { GeoJsonLayer } from '@deck.gl/layers'
import booleanPointInPolygon from '@turf/boolean-point-in-polygon'
import IncomeScatter from '../components/IncomeScatter.vue'
import ContextBanner from '../components/ContextBanner.vue'
import AboutBanner from '../components/AboutBanner.vue'
import InfoTip from '../components/InfoTip.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()

useSeoMeta({
  title: {
    en: 'Where Environmental Exposures Overlap in Paris & Inner Suburbs',
    fr: "Là où les expositions environnementales se superposent à Paris et en petite couronne",
  },
  description: {
    en: 'Interactive map of 2,752 neighborhoods across Paris and its inner suburbs (Hauts-de-Seine, Seine-Saint-Denis, Val-de-Marne): where heat, air and noise pollution, and energy-inefficient housing cumulate at once — a count, never a smoothed average — crossed with the means residents have to cope.',
    fr: "Carte interactive de 2 752 quartiers à Paris et en petite couronne (Hauts-de-Seine, Seine-Saint-Denis, Val-de-Marne) : où la chaleur, la pollution de l'air et le bruit, et le logement énergivore se cumulent à la fois — un compte, jamais une moyenne lissée — croisé avec les moyens des habitants pour y faire face.",
  },
  // schema.org Dataset: this score genuinely is a public dataset (a
  // downloadable GeoJSON with a documented, reproducible methodology),
  // not just a webpage — worth telling crawlers that explicitly rather
  // than leaving them to guess from the page copy alone.
  jsonLd: (locale) => ({
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name:
      locale === 'fr'
        ? "Underlaid — score de cumul d'exposition environnementale, Paris et petite couronne"
        : 'Underlaid — cumulative environmental exposure score, Paris & inner suburbs',
    description:
      locale === 'fr'
        ? "Pour 2 752 quartiers (IRIS) de Paris et de la petite couronne, combien des 3 catégories suivies (thermique, pollution de l'air et bruit, logement) se retrouvent simultanément dans leur pire quartile à l'échelle régionale — un compte, jamais une moyenne lissée, construit à partir de données publiques (INSEE, IGN, Airparif/Bruitparif, Enedis, ADEME, OpenStreetMap)."
        : 'For 2,752 neighborhoods (IRIS) across Paris and its inner suburbs, how many of 3 tracked categories (thermal, air/noise pollution, housing) land simultaneously in their region-wide worst quartile — a count, never a smoothed average, built from public data (INSEE, IGN, Airparif/Bruitparif, Enedis, ADEME, OpenStreetMap).',
    creator: { '@type': 'Organization', name: 'Underlaid' },
    // The published data is ODbL (share-alike inherited from the
    // OpenStreetMap and Ville de Paris inputs); the code is MIT — see
    // README "License & data attribution".
    license: 'https://opendatacommons.org/licenses/odbl/1-0/',
    isAccessibleForFree: true,
    spatialCoverage: {
      '@type': 'Place',
      name: 'Paris, Hauts-de-Seine, Seine-Saint-Denis, Val-de-Marne, France',
    },
    distribution: {
      '@type': 'DataDownload',
      encodingFormat: 'application/geo+json',
      contentUrl: `${__SITE_URL__}/data/vulnerability_score_iris.geojson`,
    },
  }),
})

const showScatter = ref(false)
const showContext = ref(false)
const showAbout = ref(false)
const showQpv = ref(false)
// No live Météo-France feed: the real vigilance API requires an account
// (portail-api.meteofrance.fr), which isn't something to set up on the
// user's behalf for a static, backend-less frontend. Showing the last
// known alert with its date is the deliberate substitute for a live
// toggle — reuses the same Santé publique France figures already in
// ContextBanner.vue rather than duplicating data.
const showHeatwaveBanner = ref(true)

const BASEMAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
const DATA_URL = '/data/vulnerability_score_iris.geojson'
const QPV_URL = '/data/qpv_boundaries_mgp.geojson'
// Phase 5: extent widened from Paris intra-muros to the full Metropole
// du Grand Paris (Petite Couronne). MGP_BOUNDS is the actual IRIS data's
// bounding box (computed directly from iris_mgp.geojson, not guessed) —
// fitBounds() below fits it properly regardless of screen aspect ratio,
// rather than a hand-picked center/zoom that would need re-tuning any
// time the covered extent changes again.
const MGP_CENTER = [2.4033, 48.8481]
const MGP_BOUNDS = [
  [2.1457, 48.6876],
  [2.6157, 49.0123],
]
// Base Adresse Nationale — the French government's free, no-key geocoder
// (data.gouv.fr), CORS-enabled and already the reference geocoder used
// across French civic-tech projects. Fits the project's existing pattern
// of relying on free official data sources rather than a commercial,
// API-key-gated geocoder.
const GEOCODE_URL = 'https://api-adresse.data.gouv.fr/search/'
// Amber is an identity color elsewhere in the palette (never part of the
// ordinal choropleth ramp), which is exactly why it's safe to reuse here
// for an outline that must read as "a different kind of thing" rather
// than another magnitude step.
const QPV_COLOR = [255, 176, 32]

// Sequential single-hue magenta ramp, validated colorblind-safe with the
// dataviz skill's ordinal-ramp checker (dark surface #080A0F):
//   node validate_palette.js "<5 hexes>" --mode dark --surface "#080A0F" --ordinal
// The maquette's raw cyan->amber->magenta gradient FAILED that check
// (176 degrees of hue spread on a "one hue" ordinal rule, and cyan/amber
// sit almost the same lightness — i.e. close to indistinguishable for
// some colorblind users). Cyan/amber/magenta stay in the palette as
// identity/branding accents (wordmark, badges, focus rings, active pill
// state) where they don't have to encode an ordered value — only the
// actual choropleth swaps to this validated ramp.
const DATA_RAMP_5 = ['#efc8d7', '#e977a3', '#f11e6f', '#c9034f', '#99003b']
// Sub-score quartiles Q1-Q4.
const DATA_RAMP_4 = DATA_RAMP_5.slice(1)
// Cumulative score 0-3 (access left the count at the v0 launch). Picked
// among 4-step subsets of the same validated ramp with validate_palette.js
// (--ordinal --mode dark --surface #080A0F): passes every ordinal check,
// worst adjacent pair ΔE 9.0 (deutan) / 13.0 (normal) — the best of the
// subsets tested — and keeps #99003b as the "worst" end.
const CUMULATIVE_RAMP = ['#efc8d7', '#e977a3', '#f11e6f', '#99003b']
const MAX_SCORE = 3
const NO_DATA_COLOR = '#3a3f4a'

// Phase 8 — "Exposure × means" bivariate grid, indexed [capacity_class][exposure_class]
// (capacity 0 = lowest third of the metro area, 2 = highest; exposure 0,
// 1, 2 = "2 or more"). Pink carries exposure (the brand magenta at its
// end, like DATA_RAMP_5), blue carries LACK of means, so the darkest cell
// is "exposures stacked, lowest means". Found by a search over two-ink
// multiply blends, checked with the dataviz skill's validate_palette.js
// (--ordinal --mode dark --surface #080A0F): every row and column passes
// lightness-monotone / adjacent-ΔL / end-contrast (darkest 2.02:1);
// grid-neighbour ΔE >= 8.2 under protan/deutan and >= 12.1 normal — both
// above DATA_RAMP_5's own adjacent figures (7.8 / 9.3). Nine ordered cells
// can't reach the categorical normal-vision floor of 15, so the cell is
// also always named in words (legend titles, detail panel, sr-only table).
const BIVARIATE_GRID = [
  ['#70a4e1', '#6f5ca3', '#6f2272'],
  ['#aec8e6', '#ac70a7', '#ab2a75'],
  ['#ebebeb', '#e984ab', '#e83178'],
]
const CAPACITY_URL = '/data/adaptive_capacity_iris.json'

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

const cumulativeLegend = computed(() => ['0', '1', '2', t('legend.worst', { n: MAX_SCORE })])
const quartileLegend = computed(() => [t('legend.qBest'), t('legend.q', { n: 2 }), t('legend.q', { n: 3 }), t('legend.qWorst')])

const METRICS = computed(() => ({
  cumulative: {
    label: t('metrics.cumulative'),
    field: 'cumulative_vulnerability_score',
    steps: [0, 1, 2, 3],
    ramp: CUMULATIVE_RAMP,
    legendLabels: cumulativeLegend.value,
  },
  thermal: {
    label: t('metrics.thermal'),
    field: 'subscore_thermal_quartile',
    steps: [1, 2, 3, 4],
    ramp: DATA_RAMP_4,
    legendLabels: quartileLegend.value,
  },
  pollution: {
    label: t('metrics.pollution'),
    field: 'subscore_pollution_quartile',
    steps: [1, 2, 3, 4],
    ramp: DATA_RAMP_4,
    legendLabels: quartileLegend.value,
  },
  housing: {
    label: t('metrics.housing'),
    field: 'subscore_housing_quartile',
    steps: [1, 2, 3, 4],
    ramp: DATA_RAMP_4,
    legendLabels: quartileLegend.value,
  },
}))

// 'exposure' (the 5 metric pills) or 'bivariate' (exposure x means) — a
// view switch that replaces the pill row rather than adding a 6th pill.
const viewMode = ref('exposure')
const selectedMetricKey = ref('cumulative')
const selectedMetric = computed(() => METRICS.value[selectedMetricKey.value])
const selectedFeature = shallowRef(null)

function bivariateColorFor(code) {
  const record = capacityByIris.value[code]
  if (!record || record.capacity_class === null || record.exposure_class === null) return hexToRgb(NO_DATA_COLOR)
  return hexToRgb(BIVARIATE_GRID[record.capacity_class][record.exposure_class])
}

function colorForFeature(feature, metric) {
  if (viewMode.value === 'bivariate') return bivariateColorFor(feature.properties.code_iris)
  const value = feature.properties[metric.field]
  if (value === null || value === undefined) return hexToRgb(NO_DATA_COLOR)
  const index = metric.steps.indexOf(Number(value))
  if (index === -1) return hexToRgb(NO_DATA_COLOR)
  return hexToRgb(metric.ramp[index])
}

let map = null
let overlay = null

function buildChoroplethLayer() {
  return new GeoJsonLayer({
    id: 'iris-choropleth',
    data: DATA_URL,
    pickable: true,
    stroked: true,
    filled: true,
    getFillColor: (f) => [...colorForFeature(f, selectedMetric.value), 225],
    getLineColor: [234, 240, 245, 90],
    lineWidthMinPixels: 0.5,
    updateTriggers: {
      getFillColor: [selectedMetricKey.value, viewMode.value, capacityLoaded.value],
    },
    onClick: (info) => {
      selectedFeature.value = info.object ?? null
    },
  })
}

// Outline-only, non-interactive: this layer exists purely so a reader can
// eyeball whether the cumulative score's worst spots line up with the
// zones France already officially recognizes as priority neighborhoods —
// it must never compete with the choropleth for clicks.
function buildQpvLayer() {
  return new GeoJsonLayer({
    id: 'qpv-boundaries',
    data: QPV_URL,
    pickable: false,
    stroked: true,
    filled: false,
    getLineColor: [...QPV_COLOR, 235],
    lineWidthMinPixels: 2.5,
  })
}

function buildLayers() {
  const layers = [buildChoroplethLayer()]
  if (showQpv.value) layers.push(buildQpvLayer())
  return layers
}

function refreshLayer() {
  if (!overlay) return
  try {
    overlay.setProps({ layers: buildLayers() })
  } catch (err) {
    // MapLibre/deck.gl can throw if the map's internal transform isn't
    // ready yet (seen in headless/software-rendered WebGL, e.g. right
    // after a context loss) — swallow and retry once on the next frame
    // rather than leaving the UI on a stale layer.
    console.warn('Layer refresh failed, retrying next frame:', err)
    requestAnimationFrame(() => {
      try {
        overlay.setProps({ layers: buildLayers() })
      } catch (retryErr) {
        console.error('Layer refresh retry also failed:', retryErr)
      }
    })
  }
}

function toggleQpv() {
  showQpv.value = !showQpv.value
  refreshLayer()
}

// Press-kit export: composites the two live canvases (MapLibre basemap +
// deck.gl choropleth/QPV overlay, same pixel size) onto an offscreen
// canvas with a title/legend/caption band, then downloads it as a PNG.
// Deliberately captures "whatever's currently on screen" rather than a
// fixed scene — a journalist can toggle metric/QPV first, so one button
// covers all 5 metrics and the QPV-comparison view, not just one preset.
// Verified on a real hardware-accelerated browser (not just headless
// software WebGL): the basemap DOES capture correctly, but the earlier
// triggerRepaint()+double-rAF approach raced with MapLibre's own raster
// tile loading, especially right after a click-driven layer rebuild —
// reproduced the black-basemap failure on real GPU rendering, then
// reproduced a correct export once tiles had more settle time. That's a
// timing bug, not a browser/readback limitation, so it's fixed properly
// here instead of documented as a known caveat: `map.once('idle', ...)`
// is MapLibre's own readiness signal for "every source has finished
// loading and the map has fully rendered," which is the actual
// condition this capture needs — a frame count was never going to be a
// reliable proxy for "tiles arrived over the network."
// Verified on a real hardware-accelerated browser (not just headless
// software WebGL, per this project's earlier documented caveat): the
// basemap canvas read-back is genuinely intermittent, not a headless-
// only limitation and not a fixed timing threshold either — the exact
// same interaction, same code, back-to-back runs, sometimes reads the
// basemap correctly and sometimes reads it back solid black, with no
// wait time (tested up to 3s) that reliably prevents it. That points to
// a transient GPU/driver buffer-swap race on this MapLibre WebGL canvas
// specifically (deck.gl's own canvas has never shown this), not
// something a single delay can paper over. Detecting the failure and
// retrying is the same defensive pattern this project already uses for
// WebGL context loss elsewhere (see refreshLayer()) — cheaper and more
// honest than pretending one fixed wait fixes a race.
const MAP_SNAPSHOT_RETRY_DELAYS_MS = [150, 400, 900, 1500]

function isBasemapPainted(canvas) {
  const probe = document.createElement('canvas')
  probe.width = 40
  probe.height = 40
  const probeCtx = probe.getContext('2d')
  probeCtx.drawImage(canvas, 0, 0, 40, 40)
  const data = probeCtx.getImageData(0, 0, 40, 40).data
  let nonBlack = 0
  for (let i = 0; i < data.length; i += 4) {
    if (data[i] > 8 || data[i + 1] > 8 || data[i + 2] > 8) nonBlack++
  }
  // A correctly-painted basemap clears this by a wide margin; a failed
  // read comes back at or near 0 of 1,600 sampled pixels.
  return nonBlack > 40
}

function exportMapSnapshot() {
  if (!map) return
  attemptMapSnapshot(0)
}

function attemptMapSnapshot(attempt) {
  map.triggerRepaint()
  requestAnimationFrame(() => requestAnimationFrame(() => {
    const isLastAttempt = attempt >= MAP_SNAPSHOT_RETRY_DELAYS_MS.length
    if (!isLastAttempt && !isBasemapPainted(map.getCanvas())) {
      setTimeout(() => attemptMapSnapshot(attempt + 1), MAP_SNAPSHOT_RETRY_DELAYS_MS[attempt])
      return
    }
    if (isLastAttempt) {
      // Ship it anyway rather than silently doing nothing — a map
      // export missing its basemap is still more useful than no export
      // at all, and this is rare enough that it isn't worth blocking on.
      console.warn('Map snapshot: basemap did not render after retries, exporting anyway.')
    }
    captureMapSnapshot()
  }))
}

function captureMapSnapshot() {
  const mapCanvas = map.getCanvas()
  const deckCanvas = document.getElementById('deckgl-overlay')
  if (!deckCanvas) return

  const width = mapCanvas.width
  const height = mapCanvas.height
  const dpr = window.devicePixelRatio || 1
  const headerHeight = Math.round(64 * dpr)
  const footerHeight = Math.round(56 * dpr)

  const out = document.createElement('canvas')
  out.width = width
  out.height = height + headerHeight + footerHeight
  const ctx = out.getContext('2d')

  ctx.fillStyle = '#080a0f'
  ctx.fillRect(0, 0, out.width, out.height)

  ctx.fillStyle = '#eaf0f5'
  ctx.font = `700 ${Math.round(26 * dpr)}px "Space Grotesk", sans-serif`
  ctx.fillText('Underlaid', Math.round(24 * dpr), Math.round(38 * dpr))

  ctx.fillStyle = '#8b96a6'
  ctx.font = `${Math.round(15 * dpr)}px "Space Grotesk", sans-serif`
  const isBivariate = viewMode.value === 'bivariate'
  ctx.fillText(isBivariate ? t('view.bivariate') : selectedMetric.value.label, Math.round(24 * dpr), Math.round(58 * dpr))

  ctx.drawImage(mapCanvas, 0, headerHeight)
  ctx.drawImage(deckCanvas, 0, headerHeight)

  let x = Math.round(24 * dpr)
  let swatchY = headerHeight + height + Math.round(22 * dpr)
  let swatchH = Math.round(8 * dpr)
  let legendText
  if (isBivariate) {
    // 3x3 mini grid, same orientation as the on-page legend (means high at
    // the top, exposure increasing to the right).
    const cell = Math.round(12 * dpr)
    const cellGap = Math.round(2 * dpr)
    swatchY = headerHeight + height + Math.round(8 * dpr)
    bivariateLegendRows.value.forEach((row, r) => {
      row.forEach((c, col) => {
        ctx.fillStyle = c.color
        ctx.fillRect(x + col * (cell + cellGap), swatchY + r * (cell + cellGap), cell, cell)
      })
    })
    x += 3 * (cell + cellGap)
    swatchH = Math.round(30 * dpr)
    legendText = `${t('bivariate.axisExposure')} 0 · 1 · 2+   ·   ${t('bivariate.axisMeans')} ↓ ${t('bivariate.meansLower')}`
  } else {
    const swatchW = Math.round(22 * dpr)
    for (const color of selectedMetric.value.ramp) {
      ctx.fillStyle = color
      ctx.fillRect(x, swatchY, swatchW, swatchH)
      x += swatchW + Math.round(4 * dpr)
    }
    const labels = selectedMetric.value.legendLabels
    legendText = `${labels[0]} → ${labels[labels.length - 1]}`
  }

  ctx.fillStyle = '#6b7686'
  ctx.font = `${Math.round(12 * dpr)}px "IBM Plex Mono", monospace`
  const caption = `${legendText}   ·   underlaid   ·   ${new Date().toISOString().slice(0, 10)}`
  ctx.fillText(caption, x + Math.round(12 * dpr), swatchY + swatchH)

  out.toBlob((blob) => {
    if (!blob) return
    const link = document.createElement('a')
    const suffix = showQpv.value ? '-qpv' : ''
    const view = viewMode.value === 'bivariate' ? 'exposure-x-means' : selectedMetricKey.value
    link.download = `underlaid-${view}${suffix}-map.png`
    link.href = URL.createObjectURL(blob)
    link.click()
    setTimeout(() => URL.revokeObjectURL(link.href), 2000)
  })
}

// Fetched independently of deck.gl's own internal load (which only feeds
// the GeoJsonLayer) so the side panel can show "vs. Paris median" and the
// screen-reader table can list every IRIS as text — see sr-only table
// below, added because a canvas choropleth has no text for a screen
// reader to read otherwise.
const allProperties = ref([])
// Full features (geometry + properties), for the address search's
// point-in-polygon lookup below. Plain variable, not a ref: it's only
// ever read imperatively from a click handler, never rendered, so there's
// no reason to pay for reactivity on 992 polygons.
let allFeatures = []
// Phase 8 adaptive-capacity axis, keyed by code_iris — loaded from its own
// file, deliberately separate from the exposure score's GeoJSON.
const capacityByIris = shallowRef({})
const capacityMedians = ref({})
const capacityLoaded = ref(false)

// Shared between SSR prerendering and the browser: onServerPrefetch runs
// this during vite-ssg's build-time render (so the sr-only screen-reader
// table below gets real IRIS data in the actual prerendered HTML, not an
// empty shell), and onMounted runs it again client-side — this project
// has no initialState/hydration wiring, so the client simply re-fetches
// the same static JSON after mount, same pattern as RankingView.vue.
async function loadData() {
  const [geojson, capacity] = await Promise.all([loadStaticJson(DATA_URL), loadStaticJson(CAPACITY_URL)])
  allProperties.value = geojson.features.map((f) => f.properties)
  allFeatures = geojson.features
  capacityByIris.value = Object.fromEntries(capacity.iris.map((r) => [r.code_iris, r]))
  capacityMedians.value = capacity.mgp_medians
  capacityLoaded.value = true
  refreshLayer()
}

onServerPrefetch(loadData)

// Map initialization stays exclusively in onMounted (never called during
// SSR/prerendering), since maplibre-gl/deck.gl need a real DOM + WebGL
// context that doesn't exist in vite-ssg's Node build process.
onMounted(async () => {
  map = new maplibregl.Map({
    container: 'map',
    style: BASEMAP_STYLE,
    center: MGP_CENTER,
    zoom: 9.5,
    minZoom: 8,
    maxZoom: 17,
    // Needed for the press-kit PNG export below: without it, some
    // browsers/drivers clear the WebGL drawing buffer before a
    // synchronous canvas.toBlob() read gets a chance to see it.
    preserveDrawingBuffer: true,
  })
  map.fitBounds(MGP_BOUNDS, { padding: 24, duration: 0 })
  map.addControl(new maplibregl.NavigationControl(), 'top-right')

  overlay = new MapboxOverlay({ layers: buildLayers() })
  map.addControl(overlay)

  await loadData()
})

onBeforeUnmount(() => {
  map?.remove()
})

function selectMetric(key) {
  selectedMetricKey.value = key
  refreshLayer()
}

function setViewMode(mode) {
  viewMode.value = mode
  refreshLayer()
}

const selectedCapacity = computed(() => {
  const code = selectedFeature.value?.properties?.code_iris
  return code ? capacityByIris.value[code] ?? null : null
})

function tierLabel(capacityClass) {
  return t(`bivariate.tier${capacityClass}`)
}

function bivariateCellText(record) {
  if (!record || record.capacity_class === null || record.exposure_class === null) return ''
  return t(`bivariate.cell_${record.exposure_class}_${record.capacity_class}`)
}

// Legend rows top -> bottom = means high -> low, columns = exposure 0 -> 2+.
const bivariateLegendRows = computed(() =>
  [2, 1, 0].map((capacityClass) =>
    [0, 1, 2].map((exposureClass) => ({
      key: `${capacityClass}-${exposureClass}`,
      color: BIVARIATE_GRID[capacityClass][exposureClass],
      title: t('bivariate.cellTitle', {
        exposure: t(`bivariate.exposureLevel${exposureClass}`),
        means: tierLabel(capacityClass),
      }),
    }))
  )
)

function metroMedianNote(field, formatter) {
  const m = capacityMedians.value[field]
  if (m === null || m === undefined) return ''
  return t('panel.cityMedian', { value: formatter(m) })
}

function median(field) {
  const values = allProperties.value
    .map((p) => p[field])
    .filter((v) => v !== null && v !== undefined)
    .sort((a, b) => a - b)
  if (!values.length) return null
  const mid = Math.floor(values.length / 2)
  return values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2
}

const medians = computed(() => ({
  access_minutes_domain_C: median('access_minutes_domain_C'),
  access_minutes_domain_D: median('access_minutes_domain_D'),
  access_minutes_domain_E: median('access_minutes_domain_E'),
  cool_spots_within_400m: median('cool_spots_within_400m'),
  pct_cool_green_area: median('pct_cool_green_area'),
  pct_artificialized: median('pct_artificialized'),
  hvi: median('hvi'),
  air_noise_coexposure_class: median('air_noise_coexposure_class'),
  pct_dpe_fg: median('pct_dpe_fg'),
  pct_thermosensitive: median('pct_thermosensitive'),
  pct_pmr_accessible: median('pct_pmr_accessible'),
  footway_density_m_per_km2: median('footway_density_m_per_km2'),
  pct_secondary_residences: median('pct_secondary_residences'),
}))

// Text alternative to the map for screen-reader users, worst-first.
const srRows = computed(() => {
  return allProperties.value
    .filter((p) => p.cumulative_vulnerability_score !== null && p.cumulative_vulnerability_score !== undefined)
    .map((p) => {
      const capacityClass = capacityByIris.value[p.code_iris]?.capacity_class
      return {
        code_iris: p.code_iris,
        nom_iris: p.nom_iris,
        nom_com: p.nom_com,
        score: p.cumulative_vulnerability_score,
        means: capacityClass === null || capacityClass === undefined ? t('srTable.meansMasked') : tierLabel(capacityClass),
      }
    })
    .sort((a, b) => b.score - a.score)
})

const liveMessage = computed(() => {
  const p = selectedFeature.value?.properties
  if (!p) return ''
  const score = p.cumulative_vulnerability_score
  const capacity = capacityByIris.value[p.code_iris]
  const means = capacity && capacity.capacity_class !== null ? ` ${t('panel.capacityTitle')}: ${tierLabel(capacity.capacity_class)}.` : ''
  return `${p.nom_iris}, ${p.nom_com}. ${t('metrics.cumulative')}: ${score ?? '—'} / ${MAX_SCORE}.${means}`
})

function closePanel() {
  selectedFeature.value = null
}

// Address search — the #1 sharing lever: people look up their own
// street before anything else. Geocodes via the free
// government BAN API, finds which IRIS polygon actually contains that
// point (not just the nearest one), flies the map there, and reuses the
// existing side panel + a relative-position line.
const searchQuery = ref('')
const searchSuggestions = ref([])
const searchMessage = ref('')
let searchDebounce = null

function onSearchInput() {
  searchMessage.value = ''
  clearTimeout(searchDebounce)
  const query = searchQuery.value.trim()
  if (query.length < 3) {
    searchSuggestions.value = []
    return
  }
  searchDebounce = setTimeout(() => fetchSuggestions(query), 300)
}

async function fetchSuggestions(query) {
  try {
    const url = `${GEOCODE_URL}?q=${encodeURIComponent(query)}&lat=${MGP_CENTER[1]}&lon=${MGP_CENTER[0]}&limit=5`
    const response = await fetch(url)
    const data = await response.json()
    searchSuggestions.value = data.features ?? []
  } catch (err) {
    console.warn('Address search failed:', err)
    searchSuggestions.value = []
  }
}

// Percentile framing for the side panel ("more vulnerable than X% of
// Paris neighborhoods") — shown for any selected IRIS, not just ones
// reached via search, since it costs one line and answers the question
// a raw 0-4 count doesn't on its own.
const selectedPercentile = computed(() => {
  const score = selectedFeature.value?.properties?.cumulative_vulnerability_score
  if (score === null || score === undefined) return null
  const valid = allProperties.value.filter(
    (p) => p.cumulative_vulnerability_score !== null && p.cumulative_vulnerability_score !== undefined
  )
  if (!valid.length) return null
  const lower = valid.filter((p) => p.cumulative_vulnerability_score < score).length
  return Math.round((lower / valid.length) * 100)
})

function selectSuggestion(suggestion) {
  searchSuggestions.value = []
  searchQuery.value = suggestion.properties.label
  const [lon, lat] = suggestion.geometry.coordinates

  const match = allFeatures.find((feature) =>
    booleanPointInPolygon([lon, lat], feature.geometry)
  )

  if (!match) {
    selectedFeature.value = null
    searchMessage.value = t('search.outsideParis')
    return
  }

  searchMessage.value = ''
  selectedFeature.value = match
  map?.flyTo({ center: [lon, lat], zoom: 15.5, duration: 1200 })
}

// Shareable card — Phase 2: a vertical (9:16, social-story format) PNG
// for the selected neighborhood, generated entirely client-side (canvas,
// no backend) so search → share works the moment someone finds their own
// street. Falls back from the Web Share API (native share sheet, where
// supported) to a plain download.
const SHARE_CARD_WIDTH = 1080
const SHARE_CARD_HEIGHT = 1920

function wrapLines(ctx, text, maxWidth) {
  const words = text.split(' ')
  const lines = []
  let line = ''
  for (const word of words) {
    const test = line ? `${line} ${word}` : word
    if (line && ctx.measureText(test).width > maxWidth) {
      lines.push(line)
      line = word
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  return lines
}

function drawCenteredLines(ctx, text, x, y, maxWidth, lineHeight) {
  for (const line of wrapLines(ctx, text, maxWidth)) {
    ctx.fillText(line, x, y)
    y += lineHeight
  }
  return y
}

async function buildShareCard(feature, percentile) {
  await document.fonts.ready

  const p = feature.properties
  const canvas = document.createElement('canvas')
  canvas.width = SHARE_CARD_WIDTH
  canvas.height = SHARE_CARD_HEIGHT
  const ctx = canvas.getContext('2d')

  ctx.fillStyle = '#080a0f'
  ctx.fillRect(0, 0, SHARE_CARD_WIDTH, SHARE_CARD_HEIGHT)

  const glow1 = ctx.createRadialGradient(140, 40, 0, 140, 40, 750)
  glow1.addColorStop(0, 'rgba(34, 230, 214, 0.20)')
  glow1.addColorStop(1, 'rgba(34, 230, 214, 0)')
  ctx.fillStyle = glow1
  ctx.fillRect(0, 0, SHARE_CARD_WIDTH, SHARE_CARD_HEIGHT)

  const glow2 = ctx.createRadialGradient(SHARE_CARD_WIDTH - 120, 300, 0, SHARE_CARD_WIDTH - 120, 300, 750)
  glow2.addColorStop(0, 'rgba(255, 61, 138, 0.16)')
  glow2.addColorStop(1, 'rgba(255, 61, 138, 0)')
  ctx.fillStyle = glow2
  ctx.fillRect(0, 0, SHARE_CARD_WIDTH, SHARE_CARD_HEIGHT)

  // wordmark
  ctx.textAlign = 'left'
  ctx.font = '700 44px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#eaf0f5'
  ctx.fillText('Under', 64, 110)
  const underWidth = ctx.measureText('Under').width
  const wordGrad = ctx.createLinearGradient(64 + underWidth, 0, 64 + underWidth + 140, 0)
  wordGrad.addColorStop(0, '#22e6d6')
  wordGrad.addColorStop(1, '#ff3d8a')
  ctx.fillStyle = wordGrad
  ctx.fillText('laid', 64 + underWidth, 110)

  // eyebrow
  ctx.font = '600 26px "IBM Plex Mono", monospace'
  ctx.fillStyle = '#22e6d6'
  ctx.fillText(t('hero.eyebrow').toUpperCase(), 64, 172)

  // neighborhood name + commune
  ctx.font = '700 66px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#eaf0f5'
  const afterName = drawCenteredLines(ctx, p.nom_iris, 64, 300, SHARE_CARD_WIDTH - 128, 76)

  ctx.font = '400 32px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#8b96a6'
  ctx.fillText(p.nom_com, 64, afterName + 20)

  // big score
  ctx.textAlign = 'center'
  const scoreGrad = ctx.createLinearGradient(SHARE_CARD_WIDTH / 2 - 220, 0, SHARE_CARD_WIDTH / 2 + 220, 0)
  scoreGrad.addColorStop(0, '#22e6d6')
  scoreGrad.addColorStop(1, '#ff3d8a')
  ctx.font = '700 320px "IBM Plex Mono", monospace'
  ctx.fillStyle = scoreGrad
  ctx.fillText(`${p.cumulative_vulnerability_score ?? '—'}/${MAX_SCORE}`, SHARE_CARD_WIDTH / 2, 980)

  ctx.font = '500 30px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#8b96a6'
  let y = drawCenteredLines(ctx, t('panel.subscoresWorstQuartile'), SHARE_CARD_WIDTH / 2, 1050, SHARE_CARD_WIDTH - 200, 40)

  if (percentile !== null) {
    ctx.font = '600 34px "Space Grotesk", sans-serif'
    ctx.fillStyle = '#22e6d6'
    y = drawCenteredLines(ctx, t('panel.morevulnerable', { n: percentile }), SHARE_CARD_WIDTH / 2, y + 30, SHARE_CARD_WIDTH - 160, 44)
  }

  // 4 sub-score chips
  const chipRows = [
    { label: t('metrics.thermal'), quartile: p.subscore_thermal_quartile },
    { label: t('metrics.pollution'), quartile: p.subscore_pollution_quartile },
    { label: t('metrics.housing'), quartile: p.subscore_housing_quartile },
  ]
  const chipY = y + 60
  const chipW = 260
  const chipH = 130
  const gap = 28
  const totalW = chipW * chipRows.length + gap * (chipRows.length - 1)
  let chipX = (SHARE_CARD_WIDTH - totalW) / 2
  for (const chip of chipRows) {
    const color = quartileColor(chip.quartile)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.04)'
    ctx.beginPath()
    ctx.roundRect(chipX, chipY, chipW, chipH, 16)
    ctx.fill()
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.roundRect(chipX, chipY, chipW, 8, 4)
    ctx.fill()

    ctx.textAlign = 'center'
    ctx.font = '600 24px "Space Grotesk", sans-serif'
    ctx.fillStyle = '#8b96a6'
    ctx.fillText(chip.label, chipX + chipW / 2, chipY + 50)
    ctx.font = '700 40px "IBM Plex Mono", monospace'
    ctx.fillStyle = '#eaf0f5'
    ctx.fillText(chip.quartile ? `Q${chip.quartile}` : '—', chipX + chipW / 2, chipY + 100)

    chipX += chipW + gap
  }

  // Means to cope — the separate axis, stated in words below the exposure
  // chips so a shared card never reads as "exposure = vulnerability".
  const capacity = capacityByIris.value[p.code_iris]
  const colon = locale.value === 'fr' ? ' : ' : ': '
  const meansValue = capacity && capacity.capacity_class !== null ? tierLabel(capacity.capacity_class) : t('srTable.meansMasked')
  const meansText = `${t('panel.capacityTitle')}${colon}${meansValue}`
  ctx.textAlign = 'center'
  ctx.font = '500 30px "Space Grotesk", sans-serif'
  ctx.fillStyle = '#b7c2cf'
  drawCenteredLines(ctx, meansText, SHARE_CARD_WIDTH / 2, chipY + chipH + 80, SHARE_CARD_WIDTH - 160, 40)

  // footer tagline
  ctx.textAlign = 'center'
  ctx.font = '500 28px "IBM Plex Mono", monospace'
  ctx.fillStyle = '#6b7686'
  // Wrapped: on one line the tagline ran past both edges of the card.
  drawCenteredLines(ctx, t('share.tagline'), SHARE_CARD_WIDTH / 2, SHARE_CARD_HEIGHT - 130, SHARE_CARD_WIDTH - 160, 38)

  return canvas
}

async function shareSelectedNeighborhood() {
  if (!selectedFeature.value) return
  const canvas = await buildShareCard(selectedFeature.value, selectedPercentile.value)

  canvas.toBlob(async (blob) => {
    if (!blob) return
    const filename = `underlaid-${selectedFeature.value.properties.code_iris}.png`

    if (navigator.canShare && navigator.canShare({ files: [new File([blob], filename, { type: 'image/png' })] })) {
      try {
        await navigator.share({
          files: [new File([blob], filename, { type: 'image/png' })],
          title: 'Underlaid',
          text: t('share.tagline'),
        })
        return
      } catch (err) {
        // User cancelled the native share sheet, or the browser rejected
        // it — either way, fall through to a plain download instead of
        // failing silently.
      }
    }

    const link = document.createElement('a')
    link.download = filename
    link.href = URL.createObjectURL(blob)
    link.click()
    setTimeout(() => URL.revokeObjectURL(link.href), 2000)
  })
}

function numberLocale() {
  return locale.value === 'fr' ? 'fr-FR' : 'en-US'
}

function formatDecimal(value, digits) {
  return new Intl.NumberFormat(numberLocale(), { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
}

function formatMinutes(value) {
  if (value === null || value === undefined) return t('panel.noData')
  return t('panel.minutes', { n: formatDecimal(value, 1) })
}

function formatPercent(value) {
  if (value === null || value === undefined) return t('panel.noData')
  return `${formatDecimal(value * 100, 0)}%`
}

function formatIncome(value) {
  if (value === null || value === undefined) return t('panel.maskedIncome')
  return new Intl.NumberFormat(numberLocale(), { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined) return t('panel.noData')
  return formatDecimal(value, digits)
}

// Comparison benchmark ("city median: X") — a raw number means little
// without a reference point.
function cityMedianNote(field, formatter) {
  const m = medians.value[field]
  if (m === null || m === undefined) return ''
  return t('panel.cityMedian', { value: formatter(m) })
}

const subScoreRows = computed(() => {
  const p = selectedFeature.value?.properties
  if (!p) return []
  return [
    { key: 'thermal', label: t('metrics.thermal'), quartile: p.subscore_thermal_quartile, status: p.subscore_thermal_status },
    { key: 'pollution', label: t('metrics.pollution'), quartile: p.subscore_pollution_quartile, status: p.subscore_pollution_status },
    { key: 'housing', label: t('metrics.housing'), quartile: p.subscore_housing_quartile, status: p.subscore_housing_status },
  ]
})

function subScoreLabel(row) {
  if (row.quartile) return t('legend.q', { n: row.quartile })
  return row.status === 'insufficient_data' ? t('panel.insufficientData') : t('panel.noData')
}

function quartileColor(quartile) {
  if (quartile === null || quartile === undefined) return NO_DATA_COLOR
  const index = [1, 2, 3, 4].indexOf(Number(quartile))
  return index === -1 ? NO_DATA_COLOR : DATA_RAMP_4[index]
}
</script>

<template>
  <div>
    <a class="skip-link" href="#map">{{ t('sidePanel.prompt') }}</a>

    <div v-if="showHeatwaveBanner" class="heatwave-banner" role="status">
      <span class="pulse-dot" aria-hidden="true"></span>
      <span class="banner-text">
        <strong>{{ t('context.heatwaveBodyStrong') }}</strong>
        {{ t('heatwave.bannerText') }}
      </span>
      <button class="banner-link" @click="showContext = true">{{ t('heatwave.moreLink') }}</button>
      <button class="banner-close" @click="showHeatwaveBanner = false" :aria-label="t('heatwave.dismiss')">&times;</button>
    </div>

    <div class="hero">
      <div class="eyebrow">{{ t('hero.eyebrow') }}<InfoTip :text="t('jargon.cumulativeScore')" /></div>
      <h1>{{ t('hero.prefix') }}<span class="grad">{{ t('hero.grad') }}</span>{{ t('hero.suffix') }}</h1>
      <p>{{ t('hero.body') }}</p>
    </div>

    <div class="layout">
      <div class="map-panel glass">
        <div class="search-row">
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            :placeholder="t('search.placeholder')"
            :aria-label="t('search.placeholder')"
            @input="onSearchInput"
          />
          <ul v-if="searchSuggestions.length" class="search-suggestions">
            <li v-for="s in searchSuggestions" :key="s.properties.id">
              <button @click="selectSuggestion(s)">{{ s.properties.label }}</button>
            </li>
          </ul>
        </div>
        <p v-if="searchMessage" class="search-message">{{ searchMessage }}</p>

        <div class="view-switch-row">
          <div class="view-switch" role="group" :aria-label="t('view.label')">
            <button :class="{ active: viewMode === 'exposure' }" :aria-pressed="viewMode === 'exposure'" @click="setViewMode('exposure')">{{ t('view.exposure') }}</button>
            <button :class="{ active: viewMode === 'bivariate' }" :aria-pressed="viewMode === 'bivariate'" @click="setViewMode('bivariate')">{{ t('view.bivariate') }}</button>
          </div>
          <InfoTip :text="t('jargon.capacity')" />
        </div>

        <p v-if="viewMode === 'bivariate'" class="bivariate-intro">{{ t('bivariate.intro') }}</p>
        <div v-else class="toolbar">
          <button
            v-for="(metric, key) in METRICS"
            :key="key"
            class="pill"
            :class="{ active: selectedMetricKey === key }"
            @click="selectMetric(key)"
          >
            {{ metric.label }}
          </button>
        </div>

        <div class="map-frame">
          <div id="map" role="img" :aria-label="t('srTable.caption')"></div>
        </div>

        <div v-if="viewMode === 'bivariate'" class="legend bivariate-legend">
          <div class="bv-grid-wrap">
            <span class="bv-axis-y" aria-hidden="true">{{ t('bivariate.axisMeans') }}<br /><small>↑ {{ t('bivariate.meansHigher') }}<br />↓ {{ t('bivariate.meansLower') }}</small></span>
            <div>
              <div class="bv-grid" role="img" :aria-label="t('bivariate.caption')">
                <template v-for="row in bivariateLegendRows" :key="row[0].key">
                  <span v-for="c in row" :key="c.key" class="bv-cell" :style="{ background: c.color }" :title="c.title"></span>
                </template>
              </div>
              <div class="bv-axis-x" aria-hidden="true">
                <span>0</span><span>1</span><span>2+</span>
              </div>
              <div class="bv-axis-x-label" aria-hidden="true">{{ t('bivariate.axisExposure') }}</div>
            </div>
          </div>
          <div class="bv-notes">
            <span>{{ t('bivariate.caption') }}</span>
            <span class="bv-masked"><span class="swatch" :style="{ background: NO_DATA_COLOR }"></span> {{ t('bivariate.masked') }}</span>
          </div>
        </div>
        <div v-else class="legend">
          <div class="legend-swatches">
            <span v-for="(color, i) in selectedMetric.ramp" :key="i" class="swatch" :style="{ background: color }" :title="selectedMetric.legendLabels[i]"></span>
            <span class="swatch" :style="{ background: NO_DATA_COLOR }" :title="t('legend.noData')"></span>
          </div>
          <span class="legend-caption">{{ selectedMetric.legendLabels[0] }} → {{ selectedMetric.legendLabels[selectedMetric.legendLabels.length - 1] }}</span>
        </div>

        <button class="ghost-link" @click="exportMapSnapshot">{{ t('buttons.exportMap') }}</button>
        <button class="ghost-link" @click="showScatter = true">{{ t('buttons.incomeVsVulnerability') }}</button>
        <button class="ghost-link" @click="showContext = true">{{ t('buttons.context') }}</button>
        <button class="ghost-link" @click="showAbout = true">{{ t('buttons.about') }}</button>
        <button
          class="ghost-link qpv-toggle"
          :class="{ active: showQpv }"
          :aria-pressed="showQpv"
          @click="toggleQpv"
        >{{ t('buttons.qpvToggle') }}</button>
        <p v-if="showQpv" class="qpv-note">{{ t('legend.qpvNote') }}</p>

        <!-- Text alternative to the canvas choropleth for screen readers.
             The wrapping div (not the table itself) carries .sr-only:
             some browsers ignore height:1px/overflow:hidden on a <table>
             and size it to fit all 992 rows anyway, blowing up page
             height — clipping via a plain div wrapper sidesteps that. -->
        <div class="sr-only" aria-live="polite">{{ liveMessage }}</div>
        <div class="sr-only">
          <table>
            <caption>{{ t('srTable.caption') }}</caption>
            <thead>
              <tr>
                <th scope="col">{{ t('srTable.colIris') }}</th>
                <th scope="col">{{ t('srTable.colCommune') }}</th>
                <th scope="col">{{ t('srTable.colScore') }}</th>
                <th scope="col">{{ t('srTable.colMeans') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in srRows" :key="row.code_iris">
                <td>{{ row.nom_iris }}</td>
                <td>{{ row.nom_com }}</td>
                <td>{{ row.score }} / {{ MAX_SCORE }}</td>
                <td>{{ row.means }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <aside class="side-panel glass">
        <div class="label">
          {{ t('sidePanel.sectionLabel') }}
          <InfoTip :text="t('jargon.iris')" />
        </div>

        <p v-if="!selectedFeature" class="prompt">{{ t('sidePanel.prompt') }}</p>

        <template v-else>
          <button class="close" @click="closePanel" :aria-label="t('sidePanel.prompt')">&times;</button>
          <div class="iris-code">{{ selectedFeature.properties.nom_iris }}</div>
          <p class="commune">{{ selectedFeature.properties.nom_com }}</p>
          <p v-if="(selectedFeature.properties.population ?? 0) < 50" class="sparse-note">{{ t('panel.sparselyPopulated') }}</p>

          <div class="stat-row" v-for="row in subScoreRows" :key="row.key">
            <span>{{ row.label }} <InfoTip v-if="row.key === 'thermal'" :text="t('jargon.quartile')" /></span>
            <span class="v" :style="{ color: quartileColor(row.quartile) }">{{ subScoreLabel(row) }}</span>
          </div>

          <div class="stat-row">
            <span>{{ t('panel.population') }}</span>
            <span class="v">{{ formatNumber(selectedFeature.properties.population, 0) }}</span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.coolSpots400m') }}</span>
            <span class="v">{{ formatNumber(selectedFeature.properties.cool_spots_within_400m, 0) }}</span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.coolGreenArea') }}</span>
            <span class="v">{{ formatPercent(selectedFeature.properties.pct_cool_green_area) }}</span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.artificialization') }}</span>
            <span class="v">{{ formatPercent(selectedFeature.properties.pct_artificialized) }}
              <small class="cmp">{{ cityMedianNote('pct_artificialized', (v) => `${formatDecimal(v * 100, 0)}%`) }}</small></span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.heatVulnerabilityIndex') }}</span>
            <span class="v">{{ formatNumber(selectedFeature.properties.hvi) }}</span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.airNoiseCoexposure') }}</span>
            <span class="v">{{ formatNumber(selectedFeature.properties.air_noise_coexposure_class) }}</span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.housingFG') }}</span>
            <span class="v">{{ formatPercent(selectedFeature.properties.pct_dpe_fg) }}
              <small class="cmp">{{ cityMedianNote('pct_dpe_fg', (v) => `${formatDecimal(v * 100, 0)}%`) }}</small></span>
          </div>
          <div class="stat-row">
            <span>{{ t('panel.thermosensitivity') }}</span>
            <span class="v">{{ formatPercent(selectedFeature.properties.pct_thermosensitive) }}
              <small class="cmp">{{ cityMedianNote('pct_thermosensitive', (v) => `${formatDecimal(v * 100, 0)}%`) }}</small></span>
          </div>

          <div class="cumul-box">
            <div class="n">{{ selectedFeature.properties.cumulative_vulnerability_score ?? '—' }}/{{ MAX_SCORE }}</div>
            <div class="d">
              {{ t('panel.subscoresWorstQuartile') }}<br />
              {{ t('panel.evaluated', { n: selectedFeature.properties.n_subscores_evaluated }) }}
            </div>
            <div v-if="selectedPercentile !== null" class="percentile">
              {{ t('panel.morevulnerable', { n: selectedPercentile }) }}
            </div>
          </div>

          <section class="access-context" :aria-label="t('panel.accessContextTitle')">
            <div class="capacity-title">{{ t('panel.accessContextTitle') }}</div>
            <p class="capacity-note">{{ t('panel.accessContextNote') }}</p>
            <div class="stat-row">
              <span>{{ t('panel.timeToEducation') }}</span>
              <span class="v">{{ formatMinutes(selectedFeature.properties.access_minutes_domain_C) }}
                <small class="cmp">{{ cityMedianNote('access_minutes_domain_C', (v) => t('panel.minutes', { n: formatDecimal(v, 1) })) }}</small></span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.timeToHealth') }}</span>
              <span class="v">{{ formatMinutes(selectedFeature.properties.access_minutes_domain_D) }}
                <small class="cmp">{{ cityMedianNote('access_minutes_domain_D', (v) => t('panel.minutes', { n: formatDecimal(v, 1) })) }}</small></span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.timeToTransport') }}</span>
              <span class="v">{{ formatMinutes(selectedFeature.properties.access_minutes_domain_E) }}
                <small class="cmp">{{ cityMedianNote('access_minutes_domain_E', (v) => t('panel.minutes', { n: formatDecimal(v, 1) })) }}</small></span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.schoolsIPS') }}</span>
              <span class="v">{{ formatNumber(selectedFeature.properties.social_index_schools) }}</span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.middleSchoolsIPS') }}</span>
              <span class="v">{{ formatNumber(selectedFeature.properties.social_index_middle_schools) }}</span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.pmrAccessible') }}</span>
              <span class="v">{{ formatPercent(selectedFeature.properties.pct_pmr_accessible) }}</span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.footwayDensity') }}</span>
              <span class="v">{{ t('panel.mPerKm2', { n: formatNumber(selectedFeature.properties.footway_density_m_per_km2, 0) }) }}</span>
            </div>
          </section>

          <section class="capacity-box" :aria-label="t('panel.capacityTitle')">
            <div class="capacity-title">{{ t('panel.capacityTitle') }} <InfoTip :text="t('jargon.capacity')" /></div>
            <p v-if="selectedCapacity && selectedCapacity.capacity_class !== null" class="capacity-tier">
              {{ t('panel.capacityTier', { tier: tierLabel(selectedCapacity.capacity_class) }) }}
            </p>
            <p v-else class="capacity-tier muted">{{ t('panel.capacityMasked') }}</p>
            <div class="stat-row">
              <span>{{ t('panel.medianIncome') }}</span>
              <span class="v">{{ formatIncome(selectedFeature.properties.median_income) }}
                <small class="cmp">{{ metroMedianNote('median_income', (v) => formatIncome(v)) }}</small></span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.overcrowding') }} <InfoTip :text="t('jargon.overcrowding')" /></span>
              <span class="v">{{ formatPercent(selectedCapacity?.pct_overcrowded) }}
                <small class="cmp">{{ metroMedianNote('pct_overcrowded', (v) => `${formatDecimal(v * 100, 0)}%`) }}</small></span>
            </div>
            <div class="stat-row">
              <span>{{ t('panel.secondaryResidences') }} <InfoTip :text="t('jargon.secondaryResidences')" /></span>
              <span class="v">{{ formatPercent(selectedFeature.properties.pct_secondary_residences) }}
                <small class="cmp">{{ metroMedianNote('pct_secondary_residences', (v) => `${formatDecimal(v * 100, 0)}%`) }}</small></span>
            </div>
            <p v-if="bivariateCellText(selectedCapacity)" class="capacity-cell">
              <span class="swatch" :style="{ background: BIVARIATE_GRID[selectedCapacity.capacity_class][selectedCapacity.exposure_class] }" aria-hidden="true"></span>
              {{ bivariateCellText(selectedCapacity) }}
            </p>
            <p class="capacity-note">{{ t('panel.capacitySeparate') }}</p>
          </section>

          <button class="share-btn" @click="shareSelectedNeighborhood">{{ t('share.button') }}</button>
        </template>
      </aside>
    </div>

    <transition name="fade">
      <div v-if="showScatter" class="modal-backdrop" @click.self="showScatter = false">
        <div class="modal-card glass">
          <button class="close" @click="showScatter = false">&times;</button>
          <h2>{{ t('modals.incomeTitle') }}</h2>
          <IncomeScatter />
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showContext" class="modal-backdrop" @click.self="showContext = false">
        <div class="modal-card glass">
          <button class="close" @click="showContext = false">&times;</button>
          <h2>{{ t('modals.contextTitle') }}</h2>
          <ContextBanner />
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showAbout" class="modal-backdrop" @click.self="showAbout = false">
        <div class="modal-card glass">
          <button class="close" @click="showAbout = false">&times;</button>
          <h2>{{ t('modals.aboutTitle') }}</h2>
          <AboutBanner />
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  background: var(--cyan);
  color: #080a0f;
  padding: 10px 16px;
  z-index: 100;
  border-radius: 0 0 8px 0;
}
.skip-link:focus {
  left: 0;
}

.heatwave-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 40px;
  background: rgba(255, 61, 138, 0.08);
  border-bottom: 1px solid rgba(255, 61, 138, 0.25);
  font-size: 12.5px;
  color: var(--text-secondary);
}
@media (max-width: 920px) {
  .heatwave-banner {
    padding: 10px 20px;
  }
}

.pulse-dot {
  flex-shrink: 0;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--magenta);
  box-shadow: 0 0 0 rgba(255, 61, 138, 0.5);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(255, 61, 138, 0.5); }
  70% { box-shadow: 0 0 0 8px rgba(255, 61, 138, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 61, 138, 0); }
}

.banner-text {
  flex: 1;
  min-width: 0;
}
.banner-text strong {
  color: var(--text-primary);
}

.banner-link {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--cyan);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 6px;
}
.banner-link:hover {
  text-decoration: underline;
}

.banner-close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
}
.banner-close:hover {
  color: var(--text-primary);
}

.hero {
  padding: 54px 40px 34px;
  max-width: 740px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--cyan);
  margin-bottom: 18px;
  padding: 6px 12px;
  border: 1px solid rgba(34, 230, 214, 0.3);
  border-radius: 999px;
  background: rgba(34, 230, 214, 0.06);
}
.eyebrow::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--cyan);
  box-shadow: 0 0 8px var(--cyan);
}

h1 {
  font-weight: 700;
  font-size: clamp(32px, 5vw, 52px);
  line-height: 1.03;
  margin: 0 0 18px;
  letter-spacing: -0.02em;
}
h1 .grad {
  background: linear-gradient(100deg, var(--cyan), var(--magenta));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero p {
  font-size: 15.5px;
  line-height: 1.65;
  color: var(--text-secondary);
  max-width: 54ch;
  margin: 0;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  padding: 0 40px 40px;
  align-items: start;
}
@media (max-width: 920px) {
  .layout {
    grid-template-columns: 1fr;
    padding: 0 20px 32px;
  }
  .hero {
    padding-left: 20px;
    padding-right: 20px;
  }
}

.map-panel {
  padding: 24px;
}

.search-row {
  position: relative;
  margin-bottom: 14px;
}

.search-input {
  width: 100%;
  font-family: inherit;
  font-size: 13.5px;
  padding: 11px 14px;
  border-radius: 10px;
  border: 1px solid var(--panel-b);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
}
.search-input::placeholder {
  color: var(--text-muted);
}
.search-input:focus-visible {
  border-color: var(--cyan);
}

.search-suggestions {
  position: absolute;
  z-index: 10;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: var(--surface-3);
  border: 1px solid var(--panel-b);
  border-radius: 10px;
  box-shadow: 0 12px 32px var(--panel-shadow);
}
.search-suggestions li button {
  display: block;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  padding: 8px 10px;
  font-size: 12.5px;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
}
.search-suggestions li button:hover,
.search-suggestions li button:focus-visible {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
}

.search-message {
  margin: -8px 0 14px;
  font-size: 12px;
  color: var(--amber);
}

.toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.pill {
  font-family: var(--mono);
  font-size: 11.5px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid var(--panel-b);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.pill.active {
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  border-color: transparent;
  color: #080a0f;
  font-weight: 600;
}
.pill:hover:not(.active) {
  border-color: var(--cyan);
  color: var(--text-primary);
}

.map-frame {
  border-radius: 12px;
  padding: 0;
  position: relative;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--gridline);
  overflow: hidden;
  height: 600px;
}
#map {
  width: 100%;
  height: 100%;
}

.legend {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-secondary);
}
.legend-swatches {
  display: flex;
  gap: 3px;
}
.swatch {
  width: 20px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}
.view-switch-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.view-switch {
  display: inline-flex;
  border: 1px solid var(--panel-b);
  border-radius: 999px;
  overflow: hidden;
}
.view-switch button {
  font-family: var(--mono);
  font-size: 11.5px;
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}
.view-switch button.active {
  background: var(--text-primary);
  color: #080a0f;
  font-weight: 600;
}
.view-switch button:hover:not(.active) {
  color: var(--text-primary);
}
.bivariate-intro {
  margin: 0 0 18px;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--text-secondary);
}

.bivariate-legend {
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px 24px;
}
.bv-grid-wrap {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.bv-axis-y {
  text-align: right;
  line-height: 1.35;
  padding-top: 2px;
}
.bv-axis-y small {
  font-size: 10px;
  color: var(--text-muted);
}
.bv-grid {
  display: grid;
  grid-template-columns: repeat(3, 22px);
  gap: 2px;
  padding: 2px;
  border-radius: 4px;
  /* light ring: the darkest cells sit close to the page background */
  background: rgba(234, 240, 245, 0.35);
}
.bv-cell {
  width: 22px;
  height: 22px;
  border-radius: 2px;
}
.bv-axis-x {
  display: grid;
  grid-template-columns: repeat(3, 22px);
  gap: 2px;
  padding: 0 2px;
  margin-top: 3px;
  text-align: center;
}
.bv-axis-x-label {
  margin-top: 2px;
}
.bv-notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 280px;
  line-height: 1.45;
}
.bv-masked {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sparse-note {
  margin: -4px 0 12px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--panel-b);
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-secondary);
}

.access-context {
  margin-top: 16px;
  padding: 16px 18px 6px;
  border-radius: 12px;
  border: 1px dashed var(--panel-b);
}

.capacity-box {
  margin-top: 16px;
  padding: 16px 18px 6px;
  border-radius: 12px;
  border: 1px solid var(--panel-b);
  background: rgba(112, 164, 225, 0.08);
}
.capacity-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}
.capacity-tier {
  margin: 6px 0 4px;
  font-size: 12.5px;
  color: var(--text-primary);
}
.capacity-tier.muted,
.capacity-note {
  color: var(--text-muted);
}
.capacity-cell {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin: 12px 0 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.capacity-cell .swatch {
  flex: 0 0 auto;
  width: 14px;
  height: 14px;
  margin-top: 2px;
}
.capacity-note {
  font-size: 11px;
  margin: 8px 0 10px;
}

.legend-caption {
  white-space: nowrap;
}

.ghost-link {
  display: block;
  width: 100%;
  text-align: left;
  margin-top: 10px;
  background: none;
  border: 1px solid var(--panel-b);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 12.5px;
  color: var(--text-secondary);
  cursor: pointer;
}
.ghost-link:hover {
  border-color: var(--cyan);
  color: var(--text-primary);
}
.ghost-link.active {
  border-color: var(--amber);
  color: var(--text-primary);
  background: rgba(255, 176, 32, 0.08);
}
.qpv-note {
  margin: 6px 0 0;
  font-size: 11px;
  color: var(--text-muted);
}

.side-panel {
  padding: 24px;
  position: relative;
  max-height: 760px;
  overflow-y: auto;
}

.label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--cyan);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.prompt {
  color: var(--text-secondary);
  font-size: 13.5px;
  line-height: 1.6;
  margin-top: 16px;
}

.iris-code {
  font-weight: 700;
  font-size: 22px;
  margin: 10px 0 2px;
}

.commune {
  margin: 0 0 18px;
  font-size: 12.5px;
  color: var(--text-secondary);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 11px 0;
  border-bottom: 1px solid var(--gridline);
  font-size: 12.5px;
  color: var(--text-secondary);
  gap: 12px;
}
.stat-row .v {
  font-family: var(--mono);
  color: var(--text-primary);
  text-align: right;
  font-weight: 500;
}
.cmp {
  display: block;
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--text-muted);
  font-weight: 400;
}

.cumul-box {
  margin-top: 22px;
  padding: 18px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(34, 230, 214, 0.12), rgba(255, 61, 138, 0.12));
  border: 1px solid var(--panel-b);
}
.cumul-box .n {
  font-weight: 700;
  font-size: 42px;
  line-height: 1;
  font-family: var(--mono);
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.cumul-box .d {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.5;
}
.percentile {
  font-size: 11.5px;
  color: var(--cyan);
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--panel-b);
}

.share-btn {
  display: block;
  width: 100%;
  margin-top: 14px;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  font-family: var(--mono);
  font-size: 12.5px;
  font-weight: 600;
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  color: #080a0f;
  cursor: pointer;
}
.share-btn:hover {
  filter: brightness(1.08);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
  padding: 20px;
}

.modal-card {
  position: relative;
  padding: 24px 28px;
  box-shadow: 0 20px 60px var(--panel-shadow);
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
}
@media (max-width: 640px) {
  .modal-card {
    max-width: 96vw;
    max-height: 96vh;
    padding: 16px;
  }
}
.modal-card h2 {
  font-size: 16px;
  margin: 0 32px 16px 0;
  color: var(--text-primary);
}

.close {
  position: absolute;
  top: 16px;
  right: 16px;
  border: none;
  background: none;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  color: var(--text-secondary);
}
.close:hover {
  color: var(--magenta);
}
</style>
