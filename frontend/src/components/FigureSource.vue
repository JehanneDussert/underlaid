<script setup>
// The line under every figure of the redesigned pages: where it comes
// from, the date of the data, and a link to how it is computed — so a
// figure can be quoted without guessing (CLAUDE.md, redesign).
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'

const props = defineProps({
  sources: { type: String, required: true },
  // Anchor on the method page (e.g. "calcul"); no link when already there.
  anchor: { type: String, default: '' },
  dark: { type: Boolean, default: false },
  // False when the source text carries its own date (audits, datasets
  // with their own edition date) rather than the score's data date.
  showDate: { type: Boolean, default: true },
})

const { t, locale } = useI18n()
const dataDate = inject('dataDate')
const dateLabel = computed(() => (props.showDate && dataDate?.value ? t('figure.dataAt', { date: dataDate.value }) : ''))
</script>

<template>
  <p class="figure-source" :class="{ dark }">
    {{ t('figure.sources', { sources: props.sources }) }}<template v-if="dateLabel"> · {{ dateLabel }}</template><template v-if="props.anchor"> ·
      <router-link :to="{ name: localizedRouteName('methodology', locale), hash: `#${props.anchor}` }">{{ t('figure.howComputed') }}</router-link></template>
  </p>
</template>

<style scoped>
.figure-source {
  margin: 0;
  padding-top: 12px;
  border-top: 1px solid var(--line-soft);
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.figure-source.dark {
  border-top-color: #2c3036;
  color: var(--text-on-dark-secondary);
}
.figure-source.dark a {
  color: var(--text-on-dark);
}
</style>
