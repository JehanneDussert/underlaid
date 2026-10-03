<script setup>
// Small loading indicator: three dots that pulse in turn, and a text that
// a screen reader announces (role="status"). The text can be shown or kept
// for screen readers only. With reduced motion the dots stay still (the
// text still says it is loading).
defineProps({
  label: { type: String, required: true },
  showLabel: { type: Boolean, default: true },
  // "light" for dots on a dark or blue background (inside a button).
  light: { type: Boolean, default: false },
})
</script>

<template>
  <span class="loading" :class="{ light }" role="status">
    <span class="dots" aria-hidden="true"><span></span><span></span><span></span></span>
    <span :class="{ 'sr-only': !showLabel }">{{ label }}</span>
  </span>
</template>

<style scoped>
.loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}
.dots {
  display: inline-flex;
  gap: 5px;
}
.dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: dot 900ms ease-in-out infinite;
}
.light .dots span {
  background: #fff;
}
.dots span:nth-child(2) {
  animation-delay: 150ms;
}
.dots span:nth-child(3) {
  animation-delay: 300ms;
}
@keyframes dot {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
