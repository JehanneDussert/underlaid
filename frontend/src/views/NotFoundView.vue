<script setup>
// Page not found (no mock-up): prerendered as dist/404.html, which the host
// serves for any unknown address. Bilingual, since an unknown address has
// no language.
import { useHead } from '@unhead/vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'

const { t, locale } = useI18n()
useHead({ title: 'Page introuvable · Page not found | Underlaid', meta: [{ name: 'robots', content: 'noindex' }] })
</script>

<template>
  <article class="simple container">
    <h1>{{ t('notFound.title') }}</h1>
    <p>{{ t('notFound.body') }}</p>
    <ul class="links">
      <li><router-link :to="{ name: localizedRouteName('home', locale) }">{{ t('notFound.home') }}</router-link></li>
      <li><router-link :to="{ name: localizedRouteName('map', locale) }">{{ t('site.nav.map') }}</router-link></li>
      <li><router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('site.nav.methodology') }}</router-link></li>
    </ul>
    <p lang="en" class="other">Page not found. <router-link :to="{ name: 'home-en' }">Go to the English home page</router-link>.</p>
  </article>
</template>

<style scoped>
.simple {
  padding-top: 64px;
  max-width: 760px;
  margin-left: 0;
}
h1 {
  margin: 0 0 16px;
  font-size: 46px;
}
p,
li {
  font-size: 18px;
  line-height: 1.6;
}
.links {
  padding-left: 22px;
}
.other {
  margin-top: 32px;
  color: var(--text-secondary);
}
</style>
