<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const DATA_URL = '/data/vulnerability_score_iris.geojson'

// Same validated (colorblind-safe, single-hue) magenta ramp as the map's
// choropleth — see App.vue's DATA_RAMP_5 comment for how/why it was
// picked over the maquette's raw cyan->amber->magenta gradient.
// Same 0-4 ramp as the map's cumulative score (MapView.vue CUMULATIVE_RAMP).
const RAMP = ['#e09ab7', '#d2668f', '#bf336a', '#980f48', '#5f002d']
const MAX_SCORE = 4

const WIDTH = 720
const HEIGHT = 440
const MARGIN = { top: 20, right: 24, bottom: 56, left: 56 }
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom

const points = ref([])
const hovered = ref(null)
const loading = ref(true)

// Deterministic per-IRIS jitter (not Math.random()) so the same point
// always renders at the same Y offset across re-renders/hovers.
function jitterFor(code) {
  let hash = 0
  for (let i = 0; i < code.length; i++) hash = (hash * 31 + code.charCodeAt(i)) >>> 0
  return ((hash % 1000) / 1000 - 0.5) * 0.6 // +/-0.3 around the integer score
}

onMounted(async () => {
  const response = await fetch(DATA_URL)
  const geojson = await response.json()

  points.value = geojson.features
    .map((f) => f.properties)
    .filter((p) => p.median_income != null && p.cumulative_vulnerability_score != null)
    .map((p) => ({
      code_iris: p.code_iris,
      nom_iris: p.nom_iris,
      nom_com: p.nom_com,
      income: p.median_income,
      score: p.cumulative_vulnerability_score,
      jitteredScore: p.cumulative_vulnerability_score + jitterFor(p.code_iris),
    }))

  loading.value = false
})

const incomeExtent = computed(() => {
  if (!points.value.length) return [0, 1]
  const incomes = points.value.map((p) => p.income)
  const min = Math.floor(Math.min(...incomes) / 5000) * 5000
  const max = Math.ceil(Math.max(...incomes) / 5000) * 5000
  return [min, max]
})

function xScale(income) {
  const [min, max] = incomeExtent.value
  return ((income - min) / (max - min)) * PLOT_WIDTH
}

function yScale(score) {
  // score 0 near the bottom, the top score (3) near the top
  return PLOT_HEIGHT - (score / MAX_SCORE) * PLOT_HEIGHT
}

const xTicks = computed(() => {
  const [min, max] = incomeExtent.value
  const step = (max - min) / 5
  return Array.from({ length: 6 }, (_, i) => Math.round(min + step * i))
})

const yTicks = [0, 1, 2, 3, 4]

// Direct-label the IRIS at the highest cumulative score actually present
// in the data (not hardcoded — the top score has moved before, and
// moved again when access left the count at the v0 launch). Only label when that top group is small; per
// marks-and-anatomy.md, labeling every point in a 45-IRIS cluster would
// be noise, not signal — the tooltip carries per-point detail instead.
const outliers = computed(() => {
  if (!points.value.length) return []
  const maxScore = Math.max(...points.value.map((p) => p.score))
  if (maxScore < 3) return [] // not a meaningfully extreme group
  const topGroup = points.value.filter((p) => p.score === maxScore)
  return topGroup.length <= 5 ? topGroup : []
})

function formatIncome(value) {
  const localeCode = locale.value === 'fr' ? 'fr-FR' : 'en-US'
  return new Intl.NumberFormat(localeCode, { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
}

const svgRef = ref(null)

// Press-kit export: the chart is already an SVG, so this serializes it,
// draws it into a canvas at 2x for a crisper export than the on-screen
// size, and downloads a PNG — no server, no rasterizing library.
function exportPng() {
  const svgEl = svgRef.value
  if (!svgEl) return
  let svgString = new XMLSerializer().serializeToString(svgEl)
  if (!svgString.includes('xmlns=')) {
    svgString = svgString.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
  }
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(svgBlob)
  const img = new Image()
  img.onload = () => {
    const scale = 2
    const canvas = document.createElement('canvas')
    canvas.width = WIDTH * scale
    canvas.height = HEIGHT * scale
    const ctx = canvas.getContext('2d')
    ctx.scale(scale, scale)
    // The SVG itself has no background rect (it inherits the page's
    // dark surface) — fill it explicitly so the exported PNG isn't
    // transparent where the chart background should be.
    ctx.fillStyle = '#0d0f15'
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    ctx.drawImage(img, 0, 0, WIDTH, HEIGHT)
    URL.revokeObjectURL(url)
    canvas.toBlob((blob) => {
      if (!blob) return
      const link = document.createElement('a')
      link.download = 'underlaid-income-vs-vulnerability.png'
      link.href = URL.createObjectURL(blob)
      link.click()
      setTimeout(() => URL.revokeObjectURL(link.href), 2000)
    })
  }
  img.src = url
}
</script>

<template>
  <div class="scatter-wrapper">
    <p v-if="loading" class="loading">{{ t('scatter.loading') }}</p>
    <div v-else class="scatter-scroll">
    <svg ref="svgRef" :width="WIDTH" :height="HEIGHT" role="img" :aria-label="t('scatter.yAxis') + ' / ' + t('scatter.xAxis')">
      <g :transform="`translate(${MARGIN.left},${MARGIN.top})`">
        <!-- horizontal gridlines, one per score level -->
        <line
          v-for="tick in yTicks"
          :key="'grid-' + tick"
          :x1="0" :x2="PLOT_WIDTH"
          :y1="yScale(tick)" :y2="yScale(tick)"
          class="gridline"
        />

        <!-- axes -->
        <line :x1="0" :x2="PLOT_WIDTH" :y1="PLOT_HEIGHT" :y2="PLOT_HEIGHT" class="axis-line" />
        <line :x1="0" :x2="0" :y1="0" :y2="PLOT_HEIGHT" class="axis-line" />

        <!-- x ticks -->
        <g v-for="tick in xTicks" :key="'xtick-' + tick">
          <text :x="xScale(tick)" :y="PLOT_HEIGHT + 20" class="tick-label" text-anchor="middle">
            {{ (tick / 1000).toFixed(0) }}k
          </text>
        </g>
        <text :x="PLOT_WIDTH / 2" :y="PLOT_HEIGHT + 44" class="axis-label" text-anchor="middle">{{ t('scatter.xAxis') }}</text>

        <!-- y ticks -->
        <g v-for="tick in yTicks" :key="'ytick-' + tick">
          <text :x="-12" :y="yScale(tick)" class="tick-label" text-anchor="end" dominant-baseline="middle">
            {{ tick }}
          </text>
        </g>
        <text
          :x="-PLOT_HEIGHT / 2" y="-40"
          class="axis-label" text-anchor="middle"
          :transform="`rotate(-90, ${-PLOT_HEIGHT / 2}, -40)`"
        >{{ t('scatter.yAxis') }}</text>

        <!-- points -->
        <g v-for="p in points" :key="p.code_iris">
          <circle
            :cx="xScale(p.income)" :cy="yScale(p.jitteredScore)"
            r="5"
            :fill="RAMP[p.score]"
            class="point"
            @pointerenter="hovered = p"
            @pointerleave="hovered = null"
          />
          <!-- larger transparent hit target, per interaction.md -->
          <circle
            :cx="xScale(p.income)" :cy="yScale(p.jitteredScore)"
            r="12" fill="transparent"
            @pointerenter="hovered = p"
            @pointerleave="hovered = null"
          />
        </g>

        <!-- direct labels for the score=4 outliers -->
        <text
          v-for="p in outliers" :key="'label-' + p.code_iris"
          :x="xScale(p.income) + 9" :y="yScale(p.jitteredScore) - 6"
          class="outlier-label"
        >{{ p.nom_iris }}</text>
      </g>
    </svg>
    </div>

    <div v-if="hovered" class="tooltip">
      <strong>{{ hovered.nom_iris }}</strong>
      <span class="tooltip-sub">{{ hovered.nom_com }}</span>
      <span>{{ t('scatter.tooltipIncome') }} <strong>{{ formatIncome(hovered.income) }}</strong></span>
      <span>{{ t('scatter.tooltipScore') }} <strong>{{ hovered.score }}</strong> {{ t('scatter.tooltipScoreSuffix') }}</span>
    </div>

    <p class="caption">{{ t('scatter.caption', { n: points.length }) }}</p>
    <button v-if="!loading" class="export-btn" @click="exportPng">{{ t('scatter.exportPng') }}</button>
  </div>
</template>

<style scoped>
.scatter-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

/* On narrow screens the 720px-wide chart doesn't shrink (labels would
   become illegible) — it scrolls horizontally inside its own container
   instead, per the dataviz skill's wide-content rule. */
.scatter-scroll {
  max-width: 100%;
  overflow-x: auto;
}

.loading {
  color: var(--text-secondary);
  font-size: 13px;
  padding: 40px;
}

.gridline {
  stroke: var(--gridline);
  stroke-width: 1;
}

.axis-line {
  stroke: var(--text-muted);
  stroke-width: 1;
}

.tick-label {
  font-size: 11px;
  fill: var(--text-muted);
}

.axis-label {
  font-size: 12px;
  fill: var(--text-secondary);
  font-weight: 600;
}

.point {
  stroke: var(--surface-2);
  stroke-width: 2;
  cursor: pointer;
}

.outlier-label {
  font-size: 11px;
  fill: var(--text-primary);
  font-weight: 600;
}

.tooltip {
  position: absolute;
  top: 12px;
  right: 12px;
  background: var(--surface-2);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-shadow: 0 4px 12px var(--panel-shadow);
  color: var(--text-primary);
}

.tooltip-sub {
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.caption {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 640px;
  text-align: center;
  margin: 0;
}

.export-btn {
  font-size: 12px;
  color: var(--text-secondary);
  background: none;
  border: 1px solid var(--panel-b);
  border-radius: 10px;
  padding: 8px 14px;
  cursor: pointer;
}
.export-btn:hover {
  border-color: var(--cyan);
  color: var(--text-primary);
}
</style>
