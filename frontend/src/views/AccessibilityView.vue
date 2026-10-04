<script setup>
// Accessibility statement (no mock-up; decision of 3 October 2026): target
// RGAA 4.1, level AA; "partiellement conforme" until the manual tests
// listed in docs/accessibilite.md have been carried out and dated.
import { useI18n } from 'vue-i18n'
import { useSeoMeta } from '../composables/useSeoMeta'

const { t } = useI18n()
useSeoMeta({
  title: { en: 'Accessibility', fr: 'Accessibilité' },
  description: { en: 'Accessibility statement: partially compliant with RGAA 4.1 (WCAG 2.1 AA), what is checked, what is not yet, and how to report a problem.', fr: "Déclaration d'accessibilité : partiellement conforme au RGAA 4.1 (WCAG 2.1 AA), ce qui est vérifié, ce qui ne l'est pas encore, et comment signaler un problème." },
})
const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const CONTACT_PARTS = ['research.jehannedussert', 'gmail.com']
function writeTo(e) {
  e.preventDefault()
  window.location.href = `mailto:${CONTACT_PARTS.join('@')}`
}
</script>

<template>
  <article class="simple container">
    <h1>{{ t('a11y.title') }}</h1>
    <p class="status"><strong>{{ t('a11y.statusLabel') }}</strong> {{ t('a11y.status') }}</p>
    <p>{{ t('a11y.intro') }}</p>

    <h2>{{ t('a11y.doneTitle') }}</h2>
    <ul>
      <li v-for="i in 6" :key="i">{{ t(`a11y.done.${i - 1}`) }}</li>
    </ul>

    <h2>{{ t('a11y.pendingTitle') }}</h2>
    <p>{{ t('a11y.pendingIntro') }}</p>
    <ul>
      <li v-for="i in 5" :key="i">{{ t(`a11y.pending.${i - 1}`) }}</li>
    </ul>

    <h2>{{ t('a11y.knownTitle') }}</h2>
    <ul>
      <li v-for="i in 3" :key="i">{{ t(`a11y.known.${i - 1}`) }}</li>
    </ul>

    <h2>{{ t('a11y.contactTitle') }}</h2>
    <p>{{ t('a11y.contact') }}</p>
    <p class="links">
      <a :href="`${REPO_URL}/discussions`" rel="noopener" @click="writeTo">{{ t('about.collab.write') }}</a> ·
      <a :href="`${REPO_URL}/issues/new`" rel="noopener">{{ t('methodD4.donnees.report') }}</a> ·
      <a :href="`${REPO_URL}/blob/master/docs/accessibilite.md`" rel="noopener">{{ t('a11y.testsLink') }}</a>
    </p>
    <p class="small">{{ t('a11y.date') }}</p>
  </article>
</template>

<style scoped>
.simple {
  padding-top: 40px;
  max-width: 900px;
  margin-left: 0;
}
h1 {
  margin: 0 0 16px;
  font-size: 46px;
  letter-spacing: -0.02em;
}
h2 {
  margin: 36px 0 10px;
  font-size: 24px;
}
p,
li {
  font-size: 17px;
  line-height: 1.65;
}
ul {
  padding-left: 22px;
}
.status {
  padding: 14px 18px;
  border-radius: 12px;
  background: var(--surface-muted);
}
.small {
  font-size: 14px;
  color: var(--text-secondary);
}
@media (max-width: 760px) {
  h1 {
    font-size: 32px;
  }
}
</style>
