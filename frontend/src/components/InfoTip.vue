<script setup>
defineProps({
  text: { type: String, required: true },
})
</script>

<template>
  <span class="info-tip">
    <button type="button" class="info-dot" :aria-label="text">i</button>
    <span class="info-bubble" role="tooltip">{{ text }}</span>
  </span>
</template>

<style scoped>
.info-tip {
  position: relative;
  display: inline-flex;
  vertical-align: middle;
  margin-left: 5px;
}

.info-dot {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  border: 1px solid var(--ink-dim);
  background: transparent;
  color: var(--ink-dim);
  font-family: var(--mono);
  font-size: 10px;
  line-height: 1;
  cursor: help;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.info-dot:hover,
.info-dot:focus-visible {
  border-color: var(--cyan);
  color: var(--cyan);
}

.info-bubble {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--surface-2);
  border: 1px solid var(--border-color);
  color: var(--ink);
  font-size: 11px;
  font-family: "Space Grotesk", sans-serif;
  padding: 8px 10px;
  border-radius: 8px;
  width: max-content;
  max-width: 220px;
  line-height: 1.4;
  box-shadow: 0 4px 12px var(--panel-shadow);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
  z-index: 40;
}

.info-dot:hover + .info-bubble,
.info-dot:focus-visible + .info-bubble {
  opacity: 1;
}
</style>
