<script setup>
// The network illustration of the home page (docs/design/refonte-d4/,
// IdentiteD4 and AccueilMobileBD4): six everyday destinations as stations
// on coloured lines around "you are here". It is an illustration, not a
// map — the geography is invented; the durations shown on it are real:
// medians of the metropolis's neighbourhoods for the chosen mode
// (routes_summary.json, script 38). No mode chosen: no duration.
//
// Desktop: curved lines drawn in SVG, labels in HTML on top. Phone: one
// vertical line. In both, the information is a real list (ul > li) that a
// screen reader reads; the drawing itself is aria-hidden.
//
// Animations (CSS only, transform / opacity / stroke-dashoffset): lines
// drawn in 2 s, 200 ms apart; stations pop (0 -> 1.15 -> 1) in 400 ms;
// labels fade in 500 ms; durations cross-fade in about 250 ms; "you are
// here" pulses three times then stops (WCAG 2.2.2). None with reduced
// motion (style.css).
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  mode: { type: String, default: null },
  // { free: { town_hall: 12, ... }, slow: {...}, wheelchair: {...} }
  medians: { type: Object, default: null },
})
const { t } = useI18n()

// Positions in the mock-up's 1280 x 860 frame; the drawing shows the part
// x 560-1280, y 88-800 (right of the text, below the header).
const VIEW = { x: 560, y: 88, w: 720, h: 712 }
const DESTS = [
  { type: 'emergency', color: 'var(--line-pink)', x: 1167, y: 463, side: 't', delay: 2200 },
  { type: 'town_hall', color: 'var(--line-orange)', x: 881, y: 192, side: 'l', delay: 2320 },
  { type: 'post_office', color: 'var(--line-orange)', x: 1172, y: 302, side: 'l', delay: 2440 },
  { type: 'france_services', color: 'var(--line-blue)', x: 1103, y: 566, side: 'b', delay: 2560 },
  { type: 'caf', color: 'var(--line-purple)', x: 736, y: 654, side: 'b', delay: 2680 },
  { type: 'employment', color: 'var(--line-green)', x: 787, y: 524, side: 'b', delay: 2800 },
]
// Phone: one vertical line, nearest first in the mock-up's order.
const PHONE_ORDER = ['post_office', 'town_hall', 'france_services', 'employment', 'emergency', 'caf']
const PHONE_COLORS = ['var(--line-cyan)', 'var(--line-blue)', 'var(--line-green)', 'var(--line-purple)', 'var(--line-pink)', 'var(--line-orange)']
const LINES = [
  { d: 'M580 220 C 780 200, 860 260, 940 380 C 1020 500, 1120 640, 1320 620', color: 'var(--line-blue)', delay: 0 },
  { d: 'M700 820 C 780 660, 860 560, 980 520 C 1100 480, 1200 470, 1320 380', color: 'var(--line-pink)', delay: 200 },
  { d: 'M1160 40 C 1140 200, 1080 300, 980 400 C 880 500, 780 560, 620 520', color: 'var(--line-green)', delay: 400 },
  { d: 'M820 30 C 840 180, 920 260, 1030 290 C 1140 320, 1240 300, 1320 250', color: 'var(--line-orange)', delay: 600 },
  { d: 'M590 620 C 740 640, 860 700, 940 760 C 1020 820, 1080 860, 1120 860', color: 'var(--line-purple)', delay: 800 },
]
const HERE = { x: 975, y: 430 }

const pct = (v, origin, size) => `${(100 * (v - origin)) / size}%`
const minutes = (type) => {
  if (!props.mode || !props.medians) return ''
  const v = props.medians[props.mode]?.[type]
  return v === null || v === undefined ? t('plan.over90') : t('plan.minutes', { n: v })
}
const listLabel = computed(() => (props.mode ? t('plan.listLabelMode', { mode: t(`modes.${props.mode}`) }) : t('plan.listLabel')))
const phoneItems = computed(() => PHONE_ORDER.map((type, i) => ({ type, color: PHONE_COLORS[i] })))
</script>

<template>
  <div class="plan">
    <!-- Desktop drawing -->
    <div class="plan-desktop">
      <svg class="plan-svg" aria-hidden="true" :viewBox="`${VIEW.x} ${VIEW.y} ${VIEW.w} ${VIEW.h}`" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="plan-fade" x1="0" x2="1">
            <stop offset="0" stop-color="#fff" stop-opacity="0" />
            <stop offset="1" stop-color="#fff" stop-opacity="1" />
          </linearGradient>
          <mask id="plan-mask">
            <rect x="560" y="0" width="160" height="900" fill="url(#plan-fade)" />
            <rect x="720" y="0" width="620" height="900" fill="#fff" />
          </mask>
        </defs>
        <g fill="none" stroke-linecap="round" stroke-width="14" mask="url(#plan-mask)">
          <path v-for="line in LINES" :key="line.d" class="plan-line" :d="line.d" :stroke="line.color" :style="{ animationDelay: `${line.delay}ms` }" />
        </g>
        <g fill="#fff" stroke="#101010" stroke-width="5">
          <circle
            v-for="dest in DESTS"
            :key="dest.type"
            class="plan-station"
            :cx="dest.x"
            :cy="dest.y"
            r="13"
            :style="{ transformOrigin: `${dest.x}px ${dest.y}px`, animationDelay: `${dest.delay - 200}ms` }"
          />
        </g>
        <circle class="plan-pulse" :cx="HERE.x" :cy="HERE.y" r="10" fill="#101010" :style="{ transformOrigin: `${HERE.x}px ${HERE.y}px` }" />
        <circle :cx="HERE.x" :cy="HERE.y" r="12" fill="#fff" stroke="#101010" stroke-width="4" />
        <circle :cx="HERE.x" :cy="HERE.y" r="5" fill="#101010" />
      </svg>
      <ul class="plan-labels" :aria-label="listLabel">
        <li
          v-for="dest in DESTS"
          :key="dest.type"
          class="plan-label"
          :class="`side-${dest.side}`"
          :style="{ left: pct(dest.x, VIEW.x, VIEW.w), top: pct(dest.y, VIEW.y, VIEW.h), animationDelay: `${dest.delay}ms` }"
        >
          <span class="plan-dot" :style="{ borderColor: dest.color }" aria-hidden="true"></span>
          <span>{{ t(`plan.dest.${dest.type}`) }}</span>
          <Transition name="plan-time" mode="out-in">
            <strong v-if="mode" :key="`${mode}-${dest.type}`" class="plan-time">{{ minutes(dest.type) }}</strong>
          </Transition>
        </li>
      </ul>
    </div>

    <!-- Phone: one vertical line -->
    <div class="plan-phone">
      <ol class="phone-line" :aria-label="listLabel">
        <li class="phone-stop phone-here">
          <span class="phone-node here" aria-hidden="true"><span></span></span>
          <span class="phone-name muted">{{ t('plan.here') }}</span>
        </li>
        <li v-for="item in phoneItems" :key="item.type" class="phone-stop" :style="{ '--seg': item.color }">
          <span class="phone-node" aria-hidden="true"></span>
          <span class="phone-name">{{ t(`plan.dest.${item.type}`) }}</span>
          <Transition name="plan-time" mode="out-in">
            <strong v-if="mode" :key="`${mode}-${item.type}`" class="phone-time">{{ minutes(item.type) }}</strong>
          </Transition>
        </li>
      </ol>
    </div>
  </div>
</template>

<style scoped>
.plan-desktop {
  position: relative;
  width: 100%;
  aspect-ratio: 720 / 712;
}
.plan-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.plan-line {
  stroke-dasharray: 1600;
  animation: plan-draw 2000ms ease-out both;
}
.plan-station {
  animation: plan-pop 400ms both;
}
.plan-pulse {
  opacity: 0;
  animation: plan-pulse 1600ms ease-out 2600ms 3;
}
.plan-labels {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}
.plan-label {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  background: var(--surface);
  border: 1.5px solid var(--line);
  border-radius: 999px;
  padding: 6px 12px 6px 10px;
  font-size: 15px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  animation: plan-fade 500ms ease-out both;
}
.side-t {
  transform: translate(-50%, calc(-100% - 20px));
}
.side-l {
  transform: translate(calc(-100% - 20px), -50%);
}
.side-b {
  transform: translate(-50%, 20px);
}
.plan-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid;
  flex-shrink: 0;
}
.plan-time {
  font-size: 16px;
}

.plan-phone {
  display: none;
}
.phone-line {
  margin: 0;
  padding: 0;
  list-style: none;
}
.phone-stop {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 46px;
  font-size: 18px;
}
/* The coloured segment above each station. */
.phone-stop:not(.phone-here)::before {
  content: '';
  position: absolute;
  left: 9px;
  bottom: 50%;
  height: 46px;
  width: 6px;
  margin-bottom: 8px;
  background: var(--seg);
}
.phone-node {
  position: relative;
  z-index: 1;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 4px solid var(--text-primary);
  background: var(--surface);
  flex-shrink: 0;
}
.phone-node.here {
  display: flex;
  align-items: center;
  justify-content: center;
}
.phone-node.here span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-primary);
}
.phone-name {
  flex: 1;
}
.phone-name.muted {
  font-size: 16px;
  color: var(--text-secondary);
}
.phone-time {
  font-size: 17px;
}

.plan-time-enter-active,
.plan-time-leave-active {
  transition: opacity 125ms ease;
}
.plan-time-enter-from,
.plan-time-leave-to {
  opacity: 0;
}

@keyframes plan-draw {
  from {
    stroke-dashoffset: 1600;
  }
  to {
    stroke-dashoffset: 0;
  }
}
@keyframes plan-pop {
  0% {
    transform: scale(0);
  }
  80% {
    transform: scale(1.15);
  }
  100% {
    transform: scale(1);
  }
}
@keyframes plan-pulse {
  0% {
    transform: scale(1);
    opacity: 0.55;
  }
  100% {
    transform: scale(3.8);
    opacity: 0;
  }
}
@keyframes plan-fade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 900px) {
  .plan-desktop {
    display: none;
  }
  .plan-phone {
    display: block;
  }
}
</style>
