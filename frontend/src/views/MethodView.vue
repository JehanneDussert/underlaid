<script setup>
// Short method page of the redesign (mock-up docs/maquettes/Methode.dc.html):
// sources, calculation, limits, corrections. The full methodology stays on
// /methodology/details (MethodologyView.vue) and in SCORING.md.
import { computed, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import FigureSource from '../components/FigureSource.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, tm, rt, locale } = useI18n()
const route = useRoute()
const router = useRouter()

// Links published before the redesign point to anchors of the former
// methodology page, now at /methodology/details: send them there.
const DETAILS_ANCHORS = ['#access', '#access-rebuilt', '#access-without-car', '#data-licences', '#inclusive-mobility', '#means', '#osm-sidewalks']
onMounted(() => {
  if (DETAILS_ANCHORS.includes(route.hash)) {
    router.replace({ name: localizedRouteName('methodology-details', locale.value), hash: route.hash })
  }
})

useSeoMeta({
  title: { en: 'Sources and method', fr: 'Sources et méthode' },
  description: {
    en: 'Where the data comes from, how the cumulative exposure score is computed for 2,752 neighbourhoods of Paris and its inner suburbs, its limits and the corrections made.',
    fr: "D'où viennent les données, comment le score de cumul est calculé pour 2 752 quartiers de Paris et de la petite couronne, ses limites et les corrections apportées.",
  },
})

const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const SCORING_URL = `${REPO_URL}/blob/master/SCORING.md`
const DOI_URL = 'https://doi.org/10.5281/zenodo.23083312'

// Computed from the published data by scripts/35_key_figures.py.
const figures = ref(null)
async function loadFigures() {
  figures.value = await loadStaticJson('/data/key_figures.json')
}
onServerPrefetch(loadFigures)
onMounted(() => {
  if (!figures.value) loadFigures()
})

const nf = computed(() => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB'))
const list = (key) => tm(key).map((item) => Object.fromEntries(Object.entries(item).map(([k, v]) => [k, typeof v === 'boolean' ? v : rt(v)])))

const sources = computed(() => list('method.sources.rows'))
const criteria = computed(() => list('method.calc.criteria'))
const measures = computed(() => list('method.measures.items'))
const limits = computed(() => list('method.limits.items'))
const fixes = computed(() => list('method.fixes.items'))

const CATEGORY_KEYS = ['thermal', 'pollution', 'housing', 'access_care']
const example = computed(() => figures.value?.example)
const distribution = computed(() => {
  if (!figures.value) return []
  const total = figures.value.n_iris
  return Object.entries(figures.value.distribution).map(([score, count]) => ({
    score,
    count: nf.value.format(count),
    share: new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { style: 'percent', maximumFractionDigits: 1 }).format(count / total),
  }))
})
</script>

<template>
  <article class="method">
    <section class="container intro">
      <p class="eyebrow">{{ t('method.eyebrow') }}</p>
      <h1>{{ t('method.title') }}</h1>
      <p class="lead">{{ t('method.lead') }}</p>
      <nav class="toc" :aria-label="t('method.tocLabel')">
        <a href="#sources">1. {{ t('method.sources.short') }}</a>
        <a href="#calcul">2. {{ t('method.calc.short') }}</a>
        <a href="#limites">3. {{ t('method.limits.short') }}</a>
        <a href="#corrections">4. {{ t('method.fixes.short') }}</a>
      </nav>
    </section>

    <section id="sources" class="band" aria-labelledby="sources-title">
      <div class="container stack">
        <h2 id="sources-title">1. {{ t('method.sources.title') }}</h2>
        <p class="body">{{ t('method.sources.intro') }}</p>
        <div class="card table-card">
          <table>
            <caption class="sr-only">{{ t('method.sources.title') }}</caption>
            <thead>
              <tr>
                <th scope="col">{{ t('method.sources.colWhat') }}</th>
                <th scope="col">{{ t('method.sources.colWho') }}</th>
                <th scope="col">{{ t('method.sources.colWhen') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in sources" :key="row.what">
                <th scope="row">{{ row.what }}</th>
                <td>{{ row.who }}</td>
                <td>
                  <span class="edition">{{ row.when }}</span>
                  <span v-if="row.note" class="note"><span class="dot" aria-hidden="true"></span>{{ row.note }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p class="legend"><span class="dot" aria-hidden="true"></span>{{ t('method.sources.legend') }}</p>
        </div>
        <p class="body small">{{ t('method.sources.mobilityNotice') }}</p>
      </div>
    </section>

    <section id="calcul" class="band" aria-labelledby="calc-title">
      <div class="container stack">
        <h2 id="calc-title">2. {{ t('method.calc.title') }}</h2>
        <p class="body">{{ t('method.calc.intro') }}</p>
        <div class="criteria">
          <div v-for="(c, i) in criteria" :key="c.name" class="card criterion">
            <span class="kicker">{{ t('method.calc.criterion', { n: i + 1 }) }}</span>
            <h3>{{ c.name }}</h3>
            <p>{{ c.desc }}</p>
          </div>
          <div class="card criterion result">
            <span class="kicker">{{ t('method.calc.resultKicker') }}</span>
            <h3>{{ t('method.calc.resultName') }}</h3>
            <p>{{ t('method.calc.resultDesc') }}</p>
          </div>
        </div>

        <div v-if="example" class="card example">
          <h3 class="example-title">{{ t('method.calc.exampleTitle', { name: example.name, commune: example.commune }) }}</h3>
          <ul class="chips" role="list">
            <li v-for="key in CATEGORY_KEYS" :key="key" :class="['chip', { bad: example.worst_quarter[key] }]">
              {{ t('method.calc.chip', { category: t(`method.calc.cat.${key}`), state: example.worst_quarter[key] ? t('method.calc.unfavourable') : t('method.calc.notUnfavourable') }) }}
            </li>
          </ul>
          <p class="example-score">{{ t('method.calc.exampleScore', { score: example.score }) }}</p>
          <p class="body small">{{ t('method.calc.countNotMean') }}</p>
        </div>

        <div v-if="distribution.length" class="card">
          <h3 class="example-title">{{ t('method.calc.distTitle') }}</h3>
          <table class="dist">
            <caption class="sr-only">{{ t('method.calc.distTitle') }}</caption>
            <thead>
              <tr>
                <th scope="col">{{ t('method.calc.distScore') }}</th>
                <th scope="col">{{ t('method.calc.distCount') }}</th>
                <th scope="col">{{ t('method.calc.distShare') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in distribution" :key="row.score">
                <th scope="row">{{ t('method.calc.outOf4', { score: row.score }) }}</th>
                <td>{{ row.count }}</td>
                <td>{{ row.share }}</td>
              </tr>
            </tbody>
          </table>
          <FigureSource :sources="t('method.calc.distSources')" />
        </div>

        <h3 class="sub">{{ t('method.measures.title') }}</h3>
        <p class="body">{{ t('method.measures.intro') }}</p>
        <div class="measures">
          <div v-for="m in measures" :key="m.name" class="card measure">
            <h4>{{ m.name }}</h4>
            <p class="status">{{ m.status }}</p>
            <p>{{ m.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section id="limites" class="band" aria-labelledby="limits-title">
      <div class="container stack">
        <h2 id="limits-title">3. {{ t('method.limits.title') }}</h2>
        <ul class="limits" role="list">
          <li v-for="l in limits" :key="l.name" class="card limit"><strong>{{ l.name }}</strong> {{ l.desc }}</li>
        </ul>
      </div>
    </section>

    <section id="corrections" class="band" aria-labelledby="fixes-title">
      <div class="container stack">
        <h2 id="fixes-title">4. {{ t('method.fixes.title') }}</h2>
        <p class="body">{{ t('method.fixes.intro') }}</p>
        <ol class="fixes" role="list">
          <li v-for="f in fixes" :key="f.what" class="card fix">
            <span class="when">{{ f.when }}</span>
            <span class="fix-text">
              <strong>{{ f.what }}</strong>
              <span>{{ f.why }}</span>
            </span>
          </li>
        </ol>
      </div>
    </section>

    <section class="band dark-band" aria-labelledby="doc-title">
      <div class="container doc">
        <div>
          <h2 id="doc-title">{{ t('method.doc.title') }}</h2>
          <p>{{ t('method.doc.body') }}</p>
        </div>
        <div class="doc-links">
          <router-link class="btn primary" :to="{ name: localizedRouteName('methodology-details', locale) }">{{ t('method.doc.details') }}</router-link>
          <a class="btn" :href="SCORING_URL" rel="noopener">{{ t('method.doc.scoring') }}</a>
          <a class="btn" :href="REPO_URL" rel="noopener">{{ t('method.doc.code') }}</a>
          <a class="btn" :href="DOI_URL" rel="noopener">{{ t('method.doc.cite') }}</a>
        </div>
      </div>
    </section>
  </article>
</template>

<style scoped>
.intro {
  padding-top: 72px;
  padding-bottom: 56px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.eyebrow {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
h1 {
  margin: 0;
  font-size: clamp(40px, 6vw, 60px);
  line-height: 1.04;
  letter-spacing: -0.035em;
  font-weight: 800;
  max-width: 820px;
}
.lead {
  margin: 0;
  font-size: 20px;
  line-height: 1.5;
  color: var(--text-body);
  max-width: 700px;
}
.toc {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.toc a {
  padding: 10px 16px;
  border-radius: 999px;
  background: var(--surface);
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
}

.band {
  border-top: 1px solid var(--line);
}
.stack {
  padding-top: 72px;
  padding-bottom: 72px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
h2 {
  margin: 0;
  font-size: 36px;
  letter-spacing: -0.025em;
}
.sub {
  margin: 24px 0 0;
  font-size: 26px;
  letter-spacing: -0.02em;
}
.body {
  margin: 0;
  font-size: 18px;
  line-height: 1.55;
  color: var(--text-body);
  max-width: 720px;
}
.body.small {
  font-size: 15px;
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px 28px;
}

.table-card {
  padding: 8px 28px;
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 16px;
}
thead th {
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 18px 16px 18px 0;
  border-bottom: 1px solid var(--line-soft);
}
tbody th,
tbody td {
  text-align: left;
  vertical-align: top;
  padding: 16px 16px 16px 0;
  border-bottom: 1px solid var(--line-soft);
}
tbody th {
  font-weight: 600;
}
tbody td {
  color: var(--text-body);
}
.edition {
  display: block;
  color: var(--text-primary);
}
.note {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin-top: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: #8a5300;
  display: inline-block;
}
.legend {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin: 0;
  padding: 16px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.criteria {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}
.criterion {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.criterion h3 {
  margin: 0;
  font-size: 20px;
}
.criterion p {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-body);
}
.kicker {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
}
.result {
  background: var(--dark);
  color: var(--text-on-dark);
}
.result .kicker {
  color: var(--accent-on-dark);
}
.result p {
  color: var(--text-on-dark-secondary);
}

.example {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.example-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.chip {
  padding: 10px 16px;
  border-radius: 999px;
  border: 1.5px solid var(--control-border);
  font-size: 15px;
  font-weight: 600;
}
.chip.bad {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}
.example-score {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.dist {
  max-width: 460px;
}

.measures {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.measure h4 {
  margin: 0 0 4px;
  font-size: 20px;
}
.measure .status {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
}
.measure p {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-body);
}

.limits,
.fixes {
  margin: 0;
  padding: 0;
  list-style: none;
}
.limits {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.limit {
  padding: 20px 24px;
  font-size: 16px;
  line-height: 1.5;
}
.fixes {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.fix {
  padding: 20px 24px;
  display: flex;
  gap: 24px;
  align-items: baseline;
}
.when {
  width: 120px;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}
.fix-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 15px;
  color: var(--text-body);
}
.fix-text strong {
  font-size: 17px;
  color: var(--text-primary);
}

.dark-band {
  background: var(--dark);
  color: var(--text-on-dark);
  border-top: none;
}
.doc {
  padding-top: 64px;
  padding-bottom: 64px;
  display: flex;
  justify-content: space-between;
  gap: 32px;
  align-items: center;
  flex-wrap: wrap;
}
.doc h2 {
  font-size: 30px;
}
.doc p {
  margin: 8px 0 0;
  font-size: 16px;
  color: var(--text-on-dark-secondary);
}
.doc-links {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.btn {
  min-height: 48px;
  padding: 0 20px;
  display: inline-flex;
  align-items: center;
  border-radius: var(--radius-small);
  border: 1.5px solid #ffffff;
  color: #ffffff;
  font-weight: 600;
  text-decoration: none;
}
.btn.primary {
  background: #ffffff;
  color: var(--dark);
}
.btn:hover {
  color: var(--accent-on-dark);
}
.btn.primary:hover {
  color: var(--accent);
}
.dark-band :focus-visible {
  outline-color: #ffffff;
}

@media (max-width: 1000px) {
  .criteria {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 640px) {
  .criteria,
  .measures,
  .limits {
    grid-template-columns: minmax(0, 1fr);
  }
  .fix {
    flex-direction: column;
    gap: 6px;
  }
  .stack {
    padding-top: 48px;
    padding-bottom: 48px;
  }
  .card {
    padding: 20px;
  }
  .table-card {
    padding: 4px 16px;
  }
  /* Sources table only: rows become stacked blocks on a phone. */
  .table-card thead {
    display: none;
  }
  .table-card tbody tr {
    display: block;
    padding: 12px 0;
    border-bottom: 1px solid var(--line-soft);
  }
  .table-card tbody th,
  .table-card tbody td {
    display: block;
    padding: 2px 0;
    border: none;
  }
}
</style>
