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
  font-family: "Schibsted Grotesk", sans-serif;
  padding: 8px 10px;
  border-radius: 8px;
  width: max-content;
  max-width: 220px;
  line-height: 1.4;
  /* Reset what the bubble would otherwise inherit from its host (the
     hero eyebrow pill is uppercase, letter-spaced, monospace). */
  text-transform: none;
  letter-spacing: normal;
  font-weight: 400;
  text-align: left;
  box-shadow: 0 4px 12px var(--panel-shadow);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
  z-index: 40;
}

/* :focus as well as :focus-visible — a tap on a touch screen focuses the
   button without matching :focus-visible, so the bubble never opened. */
.info-dot:hover + .info-bubble,
.info-dot:focus + .info-bubble,
.info-dot:focus-visible + .info-bubble {
  opacity: 1;
}

/* Phone widths: a bubble centred on a dot near the screen edge was cut
   off when shown, and — even hidden (opacity 0) — widened the page
   into a sideways scroll at 320px. Pinned to the bottom of the viewport
   instead: always fully readable, and fixed boxes don't add scroll width. */
@media (max-width: 600px) {
  .info-bubble {
    position: fixed;
    left: 16px;
    right: 16px;
    bottom: calc(16px + env(safe-area-inset-bottom, 0px));
    transform: none;
    width: auto;
    max-width: none;
    font-size: 13px;
  }
}
</style>
