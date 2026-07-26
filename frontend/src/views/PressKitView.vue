<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'
import { useSeoMeta } from '../composables/useSeoMeta'

const { t, locale } = useI18n()

useSeoMeta({
  title: {
    en: 'Press Kit — Data, Sources, and a Printable One-Page Summary',
    fr: 'Kit presse — données, sources et résumé imprimable en une page',
  },
  description: {
    en: 'A condensed, one-page methodology summary for journalists covering urban environmental exposure in Paris and its inner suburbs, with full source attribution.',
    fr: "Un résumé méthodologique condensé en une page pour les journalistes couvrant l'exposition environnementale urbaine à Paris et en petite couronne, avec attribution complète des sources.",
  },
})

// Same static facts as MethodologyView.vue — see SCORING.md.
const DISTRIBUTION = [
  { score: 0, count: 874, share: 0.318 },
  { score: 1, count: 1230, share: 0.447 },
  { score: 2, count: 586, share: 0.213 },
  { score: 3, count: 58, share: 0.021 },
  { score: 4, count: 4, share: 4 / 2752 },
]

const CATEGORY_LINES = ['thermalLine', 'pollutionLine', 'accessLine', 'housingLine']
const CAVEATS = ['caveat1', 'caveat2', 'caveat3', 'caveat4']

function numberLocale() {
  return locale.value === 'fr' ? 'fr-FR' : 'en-US'
}

function formatShare(value) {
  return new Intl.NumberFormat(numberLocale(), { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)
}

const distributionRows = computed(() =>
  DISTRIBUTION.map((row) => ({ ...row, shareLabel: formatShare(row.share) }))
)

function print() {
  window.print()
}
</script>

<template>
  <div class="press-kit">
    <div class="no-print toolbar">
      <router-link class="back-link" :to="{ name: localizedRouteName('methodology', locale) }">{{ t('press.backToMethodology') }}</router-link>
      <button class="print-btn" @click="print">{{ t('press.printButton') }}</button>
    </div>

    <div class="sheet">
      <h1>{{ t('press.title') }}</h1>
      <p class="subtitle">{{ t('press.subtitle') }}</p>

      <section>
        <h2>{{ t('press.whatTitle') }}</h2>
        <p>{{ t('press.whatBody') }}</p>
      </section>

      <section>
        <h2>{{ t('press.countTitle') }}</h2>
        <p>{{ t('press.countBody') }}</p>
      </section>

      <section>
        <h2>{{ t('press.categoriesTitle') }}</h2>
        <ul>
          <li v-for="key in CATEGORY_LINES" :key="key">{{ t(`press.${key}`) }}</li>
        </ul>
      </section>

      <section>
        <h2>{{ t('press.caveatsTitle') }}</h2>
        <ul>
          <li v-for="key in CAVEATS" :key="key">{{ t(`press.${key}`) }}</li>
        </ul>
      </section>

      <section>
        <h2>{{ t('press.distributionTitle') }}</h2>
        <table>
          <tbody>
            <tr v-for="row in distributionRows" :key="row.score">
              <td>{{ row.score }} / 4</td>
              <td>{{ row.count }}</td>
              <td>{{ row.shareLabel }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <footer>
        <p>{{ t('press.sourceLine') }}</p>
        <p>{{ t('press.dataSources') }}</p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 760px;
  margin: 0 auto;
  padding: 20px 40px 0;
}
@media (max-width: 640px) {
  .toolbar {
    padding: 20px 20px 0;
  }
}

.back-link {
  font-size: 12.5px;
  color: var(--text-secondary);
  text-decoration: none;
}
.back-link:hover {
  color: var(--cyan);
}

.print-btn {
  font-family: var(--mono);
  font-size: 12px;
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid var(--panel-b);
  background: linear-gradient(90deg, var(--cyan), var(--magenta));
  color: #080a0f;
  font-weight: 600;
  cursor: pointer;
}

.sheet {
  max-width: 700px;
  margin: 24px auto 64px;
  padding: 32px 36px;
  background: var(--panel);
  border: 1px solid var(--panel-b);
  border-radius: 16px;
}

h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 6px;
}

.subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 22px;
}

section {
  margin-bottom: 16px;
}

h2 {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--cyan);
  margin: 0 0 6px;
}

section p {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 0;
}

section ul {
  margin: 0;
  padding-left: 16px;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--text-secondary);
}
section ul li {
  margin-bottom: 4px;
}

table {
  border-collapse: collapse;
  font-size: 12px;
  font-family: var(--mono);
}
table td {
  padding: 3px 12px 3px 0;
  color: var(--text-secondary);
}
table td:first-child {
  color: var(--text-primary);
  font-weight: 600;
}

footer {
  margin-top: 20px;
  padding-top: 14px;
  border-top: 1px solid var(--gridline);
}
footer p {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0 0 4px;
}

/* One printable page, light background (dark-mode backgrounds waste ink
   and look wrong on paper), no app chrome — just the sheet. */
@media print {
  @page {
    size: A4;
    margin: 14mm;
  }
  .no-print {
    display: none !important;
  }
  .press-kit {
    background: #fff !important;
  }
  .sheet {
    max-width: none;
    margin: 0;
    padding: 0;
    background: #fff;
    border: none;
    border-radius: 0;
  }
  h1,
  h2 {
    color: #0a0a0a !important;
    -webkit-print-color-adjust: exact;
  }
  .subtitle,
  section p,
  section ul,
  table td,
  footer p {
    color: #333 !important;
  }
  table td:first-child {
    color: #0a0a0a !important;
  }
  footer {
    border-top-color: #ccc;
  }
}
</style>
