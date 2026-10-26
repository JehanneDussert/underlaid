<script setup>
// Emergency departments by departure time (pre-registered on 22 October
// 2026, docs/preregistrations/2026-10-22-courbe-urgences-heure-depart.md):
// a typical Tuesday, every 2 hours, without constraint and in a wheelchair.
// At 0:00, 2:00 and 4:00 the wheelchair time is shown as a range between
// the two hypotheses on stops and trips of unknown accessibility (not
// accessible: the line; accessible: the other end of the range). Sunday
// 10:00 stays the weekend reference, shown apart. A value of null means
// more than 90 minutes: drawn on a separate band above the plot, never as
// a number. Hover (or focus) shows the values of a departure time; the
// same values are in the table below the chart.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  // { free: [12], wheelchair: [12], wheelchair_unknown_yes: [3] }
  curve: { type: Object, required: true },
  // { free, wheelchair } at Sunday 10:00, or null
  sunday: { type: Object, default: null },
})
const { t } = useI18n()

const HOURS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
const NIGHT = [0, 2, 4]
// Drawing size follows the screen, so that text keeps a readable size:
// wide (ordinary screens) or narrow (phones, a label every 4 hours).
const narrow = ref(false)
let media = null
const onMedia = () => (narrow.value = media.matches)
onMounted(() => {
  media = window.matchMedia('(max-width: 600px)')
  onMedia()
  media.addEventListener('change', onMedia)
})
onBeforeUnmount(() => media?.removeEventListener('change', onMedia))
const W = computed(() => (narrow.value ? 360 : 960))
const H = computed(() => (narrow.value ? 240 : 280))
const PAD = { left: 40, right: 14, top: 34, bottom: 30 }
const shownHours = computed(() => (narrow.value ? HOURS.filter((h) => h % 4 === 0) : HOURS))
const OVER_Y = 14 // band for "more than 90 min"

const fmt = (v) => (v === null || v === undefined ? t('nbhd.over90') : t('plan.minutes', { n: v }))

const all = computed(() => [...props.curve.free, ...props.curve.wheelchair, ...(props.curve.wheelchair_unknown_yes ?? [])].filter((v) => v !== null))
const yMax = computed(() => {
  const m = Math.max(10, ...all.value)
  return Math.min(90, Math.ceil((m + 2) / 10) * 10)
})
const ticks = computed(() => {
  const step = yMax.value > 50 ? 20 : 10
  const out = []
  for (let v = 0; v <= yMax.value; v += step) out.push(v)
  return out
})
const x = (h) => PAD.left + ((W.value - PAD.left - PAD.right) * h) / 22
const y = (v) => (v === null ? OVER_Y : PAD.top + (H.value - PAD.top - PAD.bottom) * (1 - v / yMax.value))
const anyOver = computed(() => [...props.curve.free, ...props.curve.wheelchair, ...(props.curve.wheelchair_unknown_yes ?? [])].some((v) => v === null))

function path(values) {
  // Line through the reached points; a gap where the value is "> 90 min".
  let d = ''
  let pen = false
  values.forEach((v, i) => {
    if (v === null) {
      pen = false
      return
    }
    d += `${pen ? 'L' : 'M'}${x(HOURS[i]).toFixed(1)},${y(v).toFixed(1)}`
    pen = true
  })
  return d
}
const ranges = computed(() =>
  NIGHT.map((h, i) => {
    const a = props.curve.wheelchair[i]
    const b = props.curve.wheelchair_unknown_yes?.[i]
    return { h, a, b, show: b !== undefined && a !== b }
  }),
)
const yesFor = (h) => {
  const i = NIGHT.indexOf(h)
  return i < 0 ? undefined : props.curve.wheelchair_unknown_yes?.[i]
}
// Night wheelchair value: one figure when both hypotheses agree, else the
// range from the shorter to the longer ("more than 90 min" is the longest).
const cell = (h, i) => {
  const wc = props.curve.wheelchair[i]
  const yes = yesFor(h)
  if (yes === undefined || yes === wc) return fmt(wc)
  const [lo, hi] = [wc, yes].sort((a, b) => (a === null ? 1 : b === null ? -1 : a - b))
  return hi === null ? t('nbhd.curve.rangeOver', { a: lo }) : t('nbhd.curve.range', { a: lo, b: hi })
}

const hover = ref(null)
const hoverIndex = computed(() => (hover.value === null ? null : HOURS.indexOf(hover.value)))
function onMove(event) {
  const svg = event.currentTarget
  const r = svg.getBoundingClientRect()
  const px = ((event.clientX - r.left) / r.width) * W.value
  const h = Math.round(((px - PAD.left) / (W.value - PAD.left - PAD.right)) * 11) * 2
  hover.value = Math.max(0, Math.min(22, h))
}
const label = (h) => t('nbhd.curve.hour', { h })
const summary = computed(() =>
  t('nbhd.curve.alt', {
    freeDay: fmt(props.curve.free[5]),
    wcDay: fmt(props.curve.wheelchair[5]),
    freeNight: fmt(props.curve.free[1]),
    wcNight: cell(2, 1),
  }),
)
</script>

<template>
  <div class="curve">
    <figure>
      <div class="legend" aria-hidden="true">
        <span class="key"><span class="swatch free"></span>{{ t('modes.free') }}</span>
        <span class="key"><span class="swatch wheelchair"></span>{{ t('modes.wheelchair') }}</span>
        <span class="key"><span class="swatch range"></span>{{ t('nbhd.curve.rangeKey') }}</span>
      </div>
      <svg
        :viewBox="`0 0 ${W} ${H}`"
        role="img"
        :aria-label="summary"
        @mousemove="onMove"
        @mouseleave="hover = null"
      >
        <!-- grid and axes (recessive) -->
        <g class="grid">
          <line v-for="v in ticks" :key="v" :x1="PAD.left" :x2="W - PAD.right" :y1="y(v)" :y2="y(v)" />
        </g>
        <g class="axis">
          <text v-for="v in ticks" :key="v" :x="PAD.left - 8" :y="y(v) + 4" text-anchor="end">{{ v }}</text>
          <text v-for="h in shownHours" :key="h" :x="x(h)" :y="H - 8" text-anchor="middle">{{ label(h) }}</text>
          <text v-if="anyOver" :x="W - PAD.right" :y="OVER_Y - 4" text-anchor="end" class="over-label">{{ t('nbhd.over90') }}</text>
          <line v-if="anyOver" :x1="PAD.left" :x2="W - PAD.right" :y1="OVER_Y + 8" :y2="OVER_Y + 8" class="over-line" />
        </g>
        <!-- night range (wheelchair, two hypotheses) -->
        <g class="ranges">
          <line v-for="r in ranges.filter((r) => r.show)" :key="r.h" :x1="x(r.h)" :x2="x(r.h)" :y1="y(r.a)" :y2="y(r.b)" />
          <circle v-for="r in ranges.filter((r) => r.show)" :key="`b${r.h}`" :cx="x(r.h)" :cy="y(r.b)" r="4" class="range-end" />
        </g>
        <path class="line free" :d="path(curve.free)" />
        <path class="line wheelchair" :d="path(curve.wheelchair)" />
        <g>
          <circle v-for="(v, i) in curve.free" :key="`f${i}`" :cx="x(HOURS[i])" :cy="y(v)" r="4" class="pt free" :class="{ over: v === null }" />
          <circle v-for="(v, i) in curve.wheelchair" :key="`w${i}`" :cx="x(HOURS[i])" :cy="y(v)" r="4" class="pt wheelchair" :class="{ over: v === null }" />
        </g>
        <!-- hover layer -->
        <g v-if="hoverIndex !== null" class="hover">
          <line :x1="x(hover)" :x2="x(hover)" :y1="PAD.top - 6" :y2="H - PAD.bottom" />
        </g>
      </svg>
      <div v-if="hoverIndex !== null" class="tip" :style="{ left: `${(100 * x(hover)) / W}%` }" aria-hidden="true">
        <strong>{{ label(hover) }}</strong>
        <span><span class="swatch free"></span>{{ fmt(curve.free[hoverIndex]) }}</span>
        <span><span class="swatch wheelchair"></span>{{ cell(hover, hoverIndex) }}</span>
      </div>
      <figcaption>{{ t('nbhd.curve.caption') }}</figcaption>
    </figure>

    <p v-if="sunday" class="sunday">
      {{ t('nbhd.curve.sunday', { free: fmt(sunday.free), wc: fmt(sunday.wheelchair) }) }}
    </p>
    <p class="note">{{ t('nbhd.curve.night') }}</p>

    <details class="values">
      <summary>{{ t('nbhd.curve.tableToggle') }}</summary>
      <div class="table-wrap" tabindex="0" role="region" :aria-label="t('nbhd.curve.tableCaption')">
        <table>
          <caption>{{ t('nbhd.curve.tableCaption') }}</caption>
          <thead>
            <tr>
              <th scope="col">{{ t('nbhd.curve.departure') }}</th>
              <th scope="col">{{ t('modes.free') }}</th>
              <th scope="col">{{ t('modes.wheelchair') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(h, i) in HOURS" :key="h">
              <th scope="row">{{ label(h) }}</th>
              <td>{{ fmt(curve.free[i]) }}</td>
              <td>{{ cell(h, i) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>

    <p class="emergency-call">
      {{ t('nbhd.curve.call1') }}
      <a href="https://www.info.urgence114.fr/" rel="noopener">114</a>{{ t('nbhd.curve.call2') }}
    </p>
    <p class="note">{{ t('nbhd.curve.limit') }}</p>
  </div>
</template>

<style scoped>
.curve {
  margin-top: 8px;
}
figure {
  margin: 0;
  position: relative;
}
svg {
  width: 100%;
  height: auto;
  display: block;
  touch-action: pan-y;
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  font-size: 0.9rem;
  color: var(--text-2, #3c3c3c);
  margin-bottom: 4px;
}
.key {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.swatch {
  display: inline-block;
  width: 14px;
  height: 3px;
  border-radius: 2px;
  vertical-align: middle;
  margin-right: 4px;
}
.swatch.free {
  background: var(--mode-free);
}
.swatch.wheelchair {
  background: var(--mode-wheelchair);
}
.swatch.range {
  width: 3px;
  height: 14px;
  background: var(--mode-wheelchair);
  opacity: 0.45;
}
.grid line {
  stroke: #e2e2e2;
  stroke-width: 1;
}
.axis text {
  font-size: 12px;
  fill: #6a6a6a;
}
.axis .over-label {
  font-size: 11px;
}
.over-line {
  stroke: #d6d6d6;
  stroke-dasharray: 3 3;
}
.line {
  fill: none;
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}
.line.free {
  stroke: var(--mode-free);
}
.line.wheelchair {
  stroke: var(--mode-wheelchair);
}
.pt {
  stroke: #fff;
  stroke-width: 2;
}
.pt.free {
  fill: var(--mode-free);
}
.pt.wheelchair {
  fill: var(--mode-wheelchair);
}
.pt.over {
  fill: #fff;
  stroke-width: 2;
}
.pt.free.over {
  stroke: var(--mode-free);
}
.pt.wheelchair.over {
  stroke: var(--mode-wheelchair);
}
.ranges line {
  stroke: var(--mode-wheelchair);
  stroke-opacity: 0.45;
  stroke-width: 6;
  stroke-linecap: round;
}
.range-end {
  fill: #fff;
  stroke: var(--mode-wheelchair);
  stroke-width: 2;
}
.hover line {
  stroke: #6a6a6a;
  stroke-width: 1;
}
.tip {
  position: absolute;
  top: 28px;
  transform: translateX(-50%);
  background: #fff;
  border: 1px solid #d6d6d6;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
figcaption,
.note {
  font-size: 0.9rem;
  color: #3c3c3c;
}
.sunday {
  margin: 10px 0 4px;
}
.values summary {
  cursor: pointer;
  padding: 12px 0;
}
.values table {
  border-collapse: collapse;
  font-size: 0.9rem;
}
.values th,
.values td {
  padding: 4px 12px 4px 0;
  text-align: left;
  border-bottom: 1px solid #e2e2e2;
}
.values caption {
  text-align: left;
  font-size: 0.85rem;
  color: #3c3c3c;
  padding-bottom: 4px;
}
.emergency-call {
  margin-top: 12px;
  padding: 10px 12px;
  border-left: 3px solid #e4007c;
  background: #fafafa;
}
</style>
