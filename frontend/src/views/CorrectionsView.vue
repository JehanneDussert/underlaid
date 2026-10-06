<script setup>
// Corrections (no mock-up): every change of method made since the site went
// online, dated, with its reason — the list also shown in part 9 of the
// method page.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'

const { t, tm, rt, locale } = useI18n()
useSeoMeta({
  title: { en: 'Method corrections', fr: 'Corrections de méthode' },
  description: { en: 'Changes of method made since the site went online, dated, with their reason.', fr: 'Les changements de méthode apportés depuis la mise en ligne, datés, avec leur raison.' },
})
const fixes = computed(() => tm('method.fixes.items').map((f) => ({ when: rt(f.when), what: rt(f.what), why: rt(f.why) })).reverse())
const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
</script>

<template>
  <article class="simple container">
    <h1>{{ t('corrections.title') }}</h1>
    <p class="lead">{{ t('corrections.lead') }}</p>
    <ol class="fixes" role="list">
      <li v-for="f in fixes" :key="f.what" class="fix">
        <span class="when">{{ f.when }}</span>
        <span class="text"><strong>{{ f.what }}</strong><span>{{ f.why }}</span></span>
      </li>
    </ol>
    <p class="note">
      {{ t('corrections.report') }}
      <a :href="`${REPO_URL}/issues/new`" rel="noopener">{{ t('methodD4.donnees.report') }}</a> ·
      <router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('site.footerSources') }}</router-link>
    </p>
  </article>
</template>

<style scoped>
.simple {
  padding-top: 40px;
  max-width: 1000px;
  margin-left: 0;
}
h1 {
  margin: 0 0 12px;
  font-size: 46px;
  letter-spacing: -0.02em;
}
.lead {
  margin: 0 0 32px;
  font-size: 19px;
  line-height: 1.55;
  color: var(--text-secondary);
}
.fixes {
  margin: 0 0 24px;
  padding: 0;
  list-style: none;
}
.fix {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
}
.when {
  font-weight: 700;
  color: var(--text-secondary);
}
.text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.55;
}
.note {
  color: var(--text-secondary);
}
@media (max-width: 760px) {
  h1 {
    font-size: 32px;
  }
  .fix {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }
}
</style>
