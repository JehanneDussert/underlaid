<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="about-banner">
    <p class="banner-intro">{{ t('about.intro') }}</p>

    <section>
      <h3>{{ t('about.orsInerisTitle') }}</h3>
      <p>{{ t('about.orsInerisBody') }}</p>
      <p class="source">
        <a href="https://cartoviz.institutparisregion.fr" target="_blank" rel="noopener noreferrer">cartoviz.institutparisregion.fr</a>
      </p>
    </section>

    <section>
      <h3>{{ t('about.adaptTitle') }}</h3>
      <p>{{ t('about.adaptBody') }}</p>
      <p class="source">
        <a href="https://adaptaville.fr" target="_blank" rel="noopener noreferrer">adaptaville.fr</a>
      </p>
    </section>

    <section>
      <h3>{{ t('about.ejTitle') }}</h3>
      <p>{{ t('about.ejBody') }}</p>
    </section>

    <section>
      <h3>{{ t('about.hccTitle') }}</h3>
      <p>{{ t('about.hccBody') }}</p>
      <p class="source">{{ t('about.hccSource') }}</p>
    </section>
  </div>
</template>

<style scoped>
.about-banner {
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-size: 13px;
  color: var(--text-primary);
}

.banner-intro {
  color: var(--text-secondary);
  font-size: 12px;
  margin: 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--gridline);
}

section h3 {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 8px;
}

section p {
  margin: 0 0 6px;
  line-height: 1.5;
}

.source {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}
.source a {
  color: var(--cyan);
}
</style>
