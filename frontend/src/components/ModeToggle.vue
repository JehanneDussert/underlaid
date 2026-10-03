<script setup>
// The three travel modes (docs/design/refonte-d4/, IdentiteD4): no mode by
// default anywhere; a click picks a mode, a second click on the same
// button deselects it. Toggle buttons (aria-pressed) in a labelled group,
// and the choice is announced in a polite live region. An active mode is
// shown by its colour (border + pale background) AND a check mark in the
// text colour, so colour is never the only cue (WCAG 1.4.1;
// the orange and green borders alone are below 3:1 on their tint).
import { computed, useId } from 'vue'
import { useI18n } from 'vue-i18n'
import { MODES } from '../data/modes'

const props = defineProps({
  modelValue: { type: String, default: null },
  // Visible group label, e.g. "Comment vous déplacez-vous ? (facultatif)".
  label: { type: String, required: true },
  // Modes that cannot be chosen here (e.g. the current one in "Compare with").
  exclude: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

// useId: the same id on the server and in the browser (hydration).
const uid = useId()
const shown = computed(() => MODES.filter((m) => !props.exclude.includes(m)))
const announcement = computed(() =>
  props.modelValue ? t('modes.chosen', { mode: t(`modes.${props.modelValue}`) }) : t('modes.none')
)

function pick(mode) {
  emit('update:modelValue', props.modelValue === mode ? null : mode)
}
</script>

<template>
  <div class="mode-toggle">
    <p :id="`${uid}-label`" class="mode-label">{{ label }}</p>
    <div class="mode-buttons" role="group" :aria-labelledby="`${uid}-label`">
      <button
        v-for="mode in shown"
        :key="mode"
        type="button"
        class="mode-button"
        :class="`mode-${mode}`"
        :aria-pressed="modelValue === mode ? 'true' : 'false'"
        @click="pick(mode)"
      >
        <svg v-if="modelValue === mode" class="mode-check" aria-hidden="true" width="14" height="14" viewBox="0 0 14 14">
          <path d="M2 7.5 5.5 11 12 3.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span v-else class="mode-dot" aria-hidden="true"></span>
        {{ t(`modes.${mode}`) }}
      </button>
    </div>
    <p class="sr-only" aria-live="polite">{{ announcement }}</p>
  </div>
</template>

<style scoped>
.mode-label {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--text-secondary);
}
.mode-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.mode-button {
  --mode-color: var(--mode-free);
  --mode-bg: var(--mode-free-bg);
  min-height: 44px;
  padding: 0 16px 0 14px;
  border-radius: 999px;
  border: 2px solid var(--control-border);
  background: var(--surface);
  color: var(--text-primary);
  font: inherit;
  font-size: 16px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 200ms ease, border-color 200ms ease;
}
.mode-slow {
  --mode-color: var(--mode-slow);
  --mode-bg: var(--mode-slow-bg);
}
.mode-wheelchair {
  --mode-color: var(--mode-wheelchair);
  --mode-bg: var(--mode-wheelchair-bg);
}
.mode-button:hover {
  border-color: var(--text-primary);
}
.mode-button[aria-pressed='true'] {
  border-color: var(--mode-color);
  background: var(--mode-bg);
}
.mode-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--mode-color);
}
/* The check mark is drawn in the text colour: it must stay readable on
   the pale background whatever the mode colour. */
.mode-check {
  flex-shrink: 0;
  color: var(--text-primary);
}
</style>
