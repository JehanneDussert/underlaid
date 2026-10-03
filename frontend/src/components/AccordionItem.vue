<script setup>
// One disclosure of an accordion (pattern "Disclosure", WAI-ARIA APG): a
// real button inside the heading, aria-expanded + aria-controls, the
// chevron turns, the panel opens in 200 ms (none with reduced motion,
// style.css). Each item is independent: opening one never closes another
// (the needs of "Votre quartier" sit in two independent columns).
import { ref, useId, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  // Heading level of the button's wrapper, to keep the page outline right.
  level: { type: Number, default: 3 },
})
const emit = defineEmits(['update:open'])

const uid = useId()
const expanded = ref(props.open)
watch(
  () => props.open,
  (v) => (expanded.value = v)
)

function toggle() {
  expanded.value = !expanded.value
  emit('update:open', expanded.value)
}
</script>

<template>
  <div class="accordion-item" :class="{ 'is-open': expanded }">
    <component :is="`h${level}`" class="accordion-heading">
      <button :id="`${uid}-button`" type="button" class="accordion-button" :aria-expanded="expanded ? 'true' : 'false'" :aria-controls="`${uid}-panel`" @click="toggle">
        <span class="accordion-title"><slot name="title" /></span>
        <svg class="accordion-chevron" aria-hidden="true" width="16" height="16" viewBox="0 0 16 16">
          <path d="M3 6l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </component>
    <div :id="`${uid}-panel`" class="accordion-panel" role="region" :aria-labelledby="`${uid}-button`" :hidden="!expanded">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.accordion-item {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
}
.accordion-heading {
  margin: 0;
  font-size: inherit;
}
.accordion-button {
  width: 100%;
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  border: none;
  background: none;
  border-radius: var(--radius);
  font: inherit;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}
.accordion-title {
  flex: 1;
}
.accordion-chevron {
  flex-shrink: 0;
  transition: transform 200ms ease;
}
.is-open .accordion-chevron {
  transform: rotate(180deg);
}
.accordion-panel {
  padding: 0 20px 18px;
  animation: accordion-open 200ms ease-out;
}
@keyframes accordion-open {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
</style>
