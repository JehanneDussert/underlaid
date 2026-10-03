<script setup>
// Part 3 of the neighbourhood page ("Les deux à la fois", VotreQuartierD4):
// every inhabited neighbourhood as a dot — across, its number of exposures
// in the most affected quarter (0 to 3, spread a little so the dots do not
// pile up); up, its access to care (higher = easier). The pink zone is
// "highly exposed (2 of 3 or more) and access to care in the most difficult
// quarter". It describes the situation; it tests nothing (decision of
// 3 October 2026): the sentence beside it says so.
// The drawing is an image with a text alternative; the sentence next to it
// carries the information.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  // [[code, exposures 0-3, care rank 0-1 (1 = most difficult)], ...]
  points: { type: Array, default: () => [] },
  current: { type: String, default: null },
})
const { t } = useI18n()

const W = 480
const H = 320
const M = { l: 44, r: 12, t: 12, b: 40 }
const cw = W - M.l - M.r
const ch = H - M.t - M.b

// Deterministic spread within each column, from the neighbourhood code.
function jitter(code) {
  let h = 0
  for (const c of code) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return (h % 1000) / 1000 - 0.5
}
const x = (n, code) => M.l + ((n + 0.5 + 0.7 * jitter(code)) / 4) * cw
// Up = easier access: rank 0 (easiest) at the top.
const y = (rank) => M.t + rank * ch

const dots = computed(() => props.points.filter((p) => p[0] !== props.current).map((p) => ({ code: p[0], cx: x(p[1], p[0]), cy: y(p[2]) })))
const me = computed(() => {
  const p = props.points.find((q) => q[0] === props.current)
  return p ? { cx: x(p[1], p[0]), cy: y(p[2]) } : null
})
const zone = { x: M.l + (2 / 4) * cw, y: M.t + 0.75 * ch, w: (2 / 4) * cw, h: 0.25 * ch }
</script>

<template>
  <figure class="scatter">
    <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="t('nbhd.scatter.alt')">
      <rect :x="zone.x" :y="zone.y" :width="zone.w" :height="zone.h" fill="#fbd3e7" />
      <text :x="zone.x + zone.w - 6" :y="zone.y + 14" text-anchor="end" font-size="11" fill="#8e0050">{{ t('nbhd.scatter.zone') }}</text>
      <g fill="#b9b9b9">
        <circle v-for="d in dots" :key="d.code" :cx="d.cx" :cy="d.cy" r="2.2" />
      </g>
      <line :x1="M.l" :y1="H - M.b" :x2="W - M.r" :y2="H - M.b" stroke="#101010" stroke-width="1.5" />
      <line :x1="M.l" :y1="M.t" :x2="M.l" :y2="H - M.b" stroke="#101010" stroke-width="1.5" />
      <text v-for="n in 4" :key="n" :x="M.l + ((n - 0.5) / 4) * cw" :y="H - M.b + 16" text-anchor="middle" font-size="12" fill="#3c3c3c">{{ n - 1 }}</text>
      <text :x="W - M.r" :y="H - 4" text-anchor="end" font-size="12" fill="#3c3c3c">{{ t('nbhd.scatter.xAxis') }}</text>
      <text :x="14" :y="M.t" text-anchor="end" font-size="12" fill="#3c3c3c" :transform="`rotate(-90 14 ${M.t})`">{{ t('nbhd.scatter.yAxis') }}</text>
      <g v-if="me">
        <circle :cx="me.cx" :cy="me.cy" r="8" fill="#fff" stroke="#101010" stroke-width="3" />
        <circle :cx="me.cx" :cy="me.cy" r="3" fill="#101010" />
        <text :x="me.cx - 12" :y="me.cy + 4" text-anchor="end" font-size="13" font-weight="700" fill="#101010">{{ t('nbhd.scatter.you') }}</text>
      </g>
    </svg>
    <figcaption>{{ t('nbhd.scatter.caption') }}</figcaption>
  </figure>
</template>

<style scoped>
.scatter {
  margin: 0;
}
svg {
  width: 100%;
  height: auto;
  font-family: inherit;
}
figcaption {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
