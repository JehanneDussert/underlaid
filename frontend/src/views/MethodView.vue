<script setup>
// Method page, redesign D4 (docs/design/refonte-d4/: 05, MethodeD4): nine
// numbered parts and a sticky table of contents. Filled from the published
// data (key_figures.json), the hypotheses (data/hypotheses.js) and the
// decisions recorded in CLAUDE.md / SCORING.md. The full methodology stays
// on /methode/detail (MethodologyView.vue) and in SCORING.md.
// Anchors kept for links from other pages: #calcul (part 3), #hypotheses,
// #limites, #sources and #corrections (inside part 9), #portee (modes).
import { computed, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import FigureSource from '../components/FigureSource.vue'
import HypothesesResults from '../components/HypothesesResults.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { MODES } from '../data/modes'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, tm, rt, locale } = useI18n()
const route = useRoute()
const router = useRouter()

// Links published before the redesign point to anchors of the former
// methodology page, now at /methode/detail: send them there.
const DETAILS_ANCHORS = ['#access', '#access-rebuilt', '#access-without-car', '#data-licences', '#inclusive-mobility', '#means', '#osm-sidewalks']
onMounted(() => {
  if (DETAILS_ANCHORS.includes(route.hash)) {
    router.replace({ name: localizedRouteName('methodology-details', locale.value), hash: route.hash })
  }
})

useSeoMeta({
  title: { en: 'Sources and method', fr: 'Sources et méthode' },
  description: {
    en: 'How the 2,752 neighbourhoods of Paris and its inner suburbs are compared: themes, access to care, travel times, residents’ resources, tested hypotheses, limits, data and corrections.',
    fr: "Comment les 2 752 quartiers de Paris et de la petite couronne sont comparés : thèmes, accès aux soins, durées de trajet, ressources des habitants, hypothèses testées, limites, données et corrections.",
  },
})

const REPO_URL = 'https://github.com/JehanneDussert/underlaid'
const SCORING_URL = `${REPO_URL}/blob/master/SCORING.md`
const DOI_URL = 'https://doi.org/10.5281/zenodo.23083312'

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
const limits = computed(() => list('method.limits.items'))
const fixes = computed(() => list('method.fixes.items'))
const places = computed(() => list('methodD4.portee.places'))

const PARTS = ['bref', 'quartiers', 'calcul', 'soins', 'portee', 'ressources', 'hypotheses', 'limites', 'donnees']
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
    <header class="method-head container">
      <h1>{{ t('methodD4.title') }}</h1>
      <p class="lead">{{ t('methodD4.lead') }}</p>
    </header>

    <div class="container method-grid">
      <nav class="toc" :aria-label="t('method.tocLabel')">
        <span class="toc-title">{{ t('method.tocLabel') }}</span>
        <ol>
          <li v-for="(id, i) in PARTS" :key="id">
            <a :href="`#${id}`"><span class="toc-num">{{ i + 1 }}</span>{{ t(`methodD4.part.${id}`) }}</a>
          </li>
        </ol>
      </nav>

      <div class="parts">
        <!-- 1. En bref -->
        <section id="bref" class="part" aria-labelledby="t-bref">
          <h2 id="t-bref"><span class="num">1.</span>{{ t('methodD4.part.bref') }}</h2>
          <div class="facts">
            <div class="fact"><strong>{{ nf.format(figures?.n_iris ?? 2752) }}</strong><span>{{ t('methodD4.bref.iris') }}</span></div>
            <div class="fact"><strong>{{ t('methodD4.bref.themesN') }}</strong><span>{{ t('methodD4.bref.themes') }}</span></div>
            <div class="fact"><strong>{{ t('methodD4.bref.modesN') }}</strong><span>{{ t('methodD4.bref.modes') }}</span></div>
          </div>
          <p>{{ t('methodD4.bref.body') }}</p>
        </section>

        <!-- 2. Les quartiers -->
        <section id="quartiers" class="part" aria-labelledby="t-quartiers">
          <h2 id="t-quartiers"><span class="num">2.</span>{{ t('methodD4.part.quartiers') }}</h2>
          <p>{{ t('methodD4.quartiers.p1', { n: nf.format(figures?.n_iris ?? 2752) }) }}</p>
          <p>{{ t('methodD4.quartiers.p2') }}</p>
        </section>

        <!-- 3. Le cadre de vie -->
        <section id="calcul" class="part" aria-labelledby="t-calcul">
          <h2 id="t-calcul"><span class="num">3.</span>{{ t('methodD4.part.calcul') }}</h2>
          <p>{{ t('methodD4.cadre.intro') }}</p>
          <dl class="defs">
            <template v-for="c in criteria" :key="c.name">
              <dt>{{ c.name }}</dt>
              <dd>{{ c.desc }}</dd>
            </template>
          </dl>
          <p v-html="t('methodD4.cadre.cumul')"></p>
          <p>{{ t('methodD4.cadre.rank') }}</p>
          <div v-if="example" class="card">
            <h3>{{ t('method.calc.exampleTitle', { name: example.name, commune: example.commune }) }}</h3>
            <ul class="chips" role="list">
              <li v-for="key in CATEGORY_KEYS" :key="key" :class="['chip', { bad: example.worst_quarter[key] }]">
                {{ t('method.calc.chip', { category: t(`method.calc.cat.${key}`), state: example.worst_quarter[key] ? t('method.calc.unfavourable') : t('method.calc.notUnfavourable') }) }}
              </li>
            </ul>
            <p class="example-score">{{ t('method.calc.exampleScore', { score: example.score }) }}</p>
            <p class="small">{{ t('method.calc.countNotMean') }}</p>
          </div>
          <div v-if="distribution.length" class="card">
            <h3>{{ t('method.calc.distTitle') }}</h3>
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
        </section>

        <!-- 4. L'accès aux soins -->
        <section id="soins" class="part" aria-labelledby="t-soins">
          <h2 id="t-soins"><span class="num">4.</span>{{ t('methodD4.part.soins') }}</h2>
          <p>{{ t('methodD4.soins.p1') }}</p>
          <p>{{ t('methodD4.soins.p2') }}</p>
          <p class="small">{{ t('methodD4.soins.sources') }}</p>
        </section>

        <!-- 5. Ce qui est à portée -->
        <section id="portee" class="part" aria-labelledby="t-portee">
          <h2 id="t-portee"><span class="num">5.</span>{{ t('methodD4.part.portee') }}</h2>
          <p>{{ t('methodD4.portee.intro') }}</p>
          <dl class="defs">
            <template v-for="m in MODES" :key="m">
              <dt><span class="dot" :class="`dot-${m}`" aria-hidden="true"></span>{{ t(`modes.${m}`) }}</dt>
              <dd>{{ t(`nbhd.how.${m}`) }}</dd>
            </template>
          </dl>
          <p>{{ t('methodD4.portee.info') }}</p>
          <div class="table-wrap">
            <table class="places">
              <caption class="sr-only">{{ t('methodD4.portee.tableCaption') }}</caption>
              <thead>
                <tr>
                  <th scope="col">{{ t('methodD4.portee.colPlace') }}</th>
                  <th scope="col">{{ t('methodD4.portee.colSource') }}</th>
                  <th scope="col">{{ t('methodD4.portee.colNote') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in places" :key="p.place">
                  <th scope="row">{{ p.place }}</th>
                  <td>{{ p.source }}</td>
                  <td>{{ p.note }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="small">
            {{ t('methodD4.portee.exclusions') }}
            <a :href="`${SCORING_URL}#excluded-destinations-full-list`" rel="noopener">{{ t('methodD4.portee.exclusionsLink') }}</a>
          </p>
        </section>

        <!-- 6. Les ressources des habitants -->
        <section id="ressources" class="part" aria-labelledby="t-ressources">
          <h2 id="t-ressources"><span class="num">6.</span>{{ t('methodD4.part.ressources') }}</h2>
          <p>{{ t('methodD4.ressources.p1') }}</p>
          <p>{{ t('methodD4.ressources.p2') }}</p>
          <p class="small">{{ t('methodD4.ressources.sources') }}</p>
        </section>

        <!-- 7. Hypothèses et résultats -->
        <section id="hypotheses" class="part" aria-labelledby="t-hypotheses">
          <h2 id="t-hypotheses"><span class="num">7.</span>{{ t('methodD4.part.hypotheses') }}</h2>
          <HypothesesResults />
        </section>

        <!-- 8. Limites -->
        <section id="limites" class="part" aria-labelledby="t-limites">
          <h2 id="t-limites"><span class="num">8.</span>{{ t('methodD4.part.limites') }}</h2>
          <ul class="limits" role="list">
            <li v-for="l in limits" :key="l.name"><strong>{{ l.name }}</strong> {{ l.desc }}</li>
          </ul>
        </section>

        <!-- 9. Données, code et corrections -->
        <section id="donnees" class="part" aria-labelledby="t-donnees">
          <h2 id="t-donnees"><span class="num">9.</span>{{ t('methodD4.part.donnees') }}</h2>
          <p>{{ t('methodD4.donnees.intro') }}</p>
          <div class="links">
            <a class="pill-link" :href="REPO_URL" rel="noopener">{{ t('methodD4.donnees.code') }}</a>
            <a class="pill-link" :href="DOI_URL" rel="noopener">{{ t('methodD4.donnees.data') }}</a>
            <a class="pill-link" :href="SCORING_URL" rel="noopener">{{ t('method.doc.scoring') }}</a>
            <router-link class="pill-link" :to="{ name: localizedRouteName('methodology-details', locale) }">{{ t('method.doc.details') }}</router-link>
            <a class="pill-link" :href="`${REPO_URL}/issues/new`" rel="noopener">{{ t('methodD4.donnees.report') }}</a>
          </div>

          <h3 id="sources">{{ t('method.sources.title') }}</h3>
          <p>{{ t('method.sources.intro') }}</p>
          <div class="table-wrap">
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
                    <span v-if="row.note" class="note">{{ row.note }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="small">{{ t('method.sources.mobilityNotice') }}</p>

          <h3 id="corrections">{{ t('method.fixes.title') }}</h3>
          <p>{{ t('method.fixes.intro') }}</p>
          <ol class="fixes" role="list">
            <li v-for="f in fixes" :key="f.what" class="fix">
              <span class="when">{{ f.when }}</span>
              <span class="fix-text">
                <strong>{{ f.what }}</strong>
                <span>{{ f.why }}</span>
              </span>
            </li>
          </ol>
        </section>
      </div>
    </div>
  </article>
</template>

<style scoped>
.method-head {
  padding-top: 40px;
  padding-bottom: 8px;
}
.method-head h1 {
  margin: 0 0 12px;
  font-size: 46px;
  letter-spacing: -0.02em;
}
.lead {
  margin: 0;
  font-size: 19px;
  line-height: 1.55;
  color: var(--text-secondary);
  max-width: 820px;
}
.method-grid {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 56px;
  padding-top: 32px;
}
.toc {
  align-self: start;
  position: sticky;
  top: 24px;
  border-left: 3px solid var(--primary);
  padding-left: 18px;
}
.toc-title {
  font-size: 13px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.toc ol {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
}
.toc a {
  display: flex;
  gap: 10px;
  padding: 7px 0;
  font-size: 15px;
  text-decoration: none;
  min-height: 36px;
  align-items: center;
}
.toc a:hover {
  text-decoration: underline;
}
.toc-num {
  color: var(--text-muted);
  min-width: 16px;
}
.parts {
  min-width: 0;
}
.part {
  padding-bottom: 64px;
  scroll-margin-top: 24px;
}
.part h2 {
  margin: 0 0 18px;
  font-size: 30px;
}
.num {
  color: var(--primary);
  margin-right: 10px;
}
.part p {
  font-size: 17px;
  line-height: 1.65;
  margin: 0 0 14px;
  max-width: 820px;
}
.part h3 {
  margin: 32px 0 10px;
  font-size: 21px;
  scroll-margin-top: 24px;
}
.small,
.part p.small {
  font-size: 14px;
  color: var(--text-secondary);
}
.facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}
.fact {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.fact strong {
  font-size: 28px;
}
.fact span {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.defs {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 12px 24px;
  margin: 0 0 18px;
  max-width: 900px;
}
.defs dt {
  font-weight: 700;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.defs dd {
  margin: 0;
  line-height: 1.6;
  color: var(--text-secondary);
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 7px;
  flex-shrink: 0;
}
.dot-free {
  background: var(--mode-free);
}
.dot-slow {
  background: var(--mode-slow);
}
.dot-wheelchair {
  background: var(--mode-wheelchair);
}
.card {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 22px 24px;
  margin: 20px 0;
}
.card h3 {
  margin: 0 0 12px;
  font-size: 19px;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 10px;
  padding: 0;
  list-style: none;
}
.chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1.5px solid var(--line-strong);
  font-size: 14px;
}
.chip.bad {
  background: var(--accent-tint);
  border-color: var(--accent);
}
.example-score {
  font-weight: 700;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 15px;
}
.dist {
  max-width: 420px;
}
th,
td {
  text-align: left;
  vertical-align: top;
  padding: 10px 12px 10px 0;
  border-bottom: 1px solid var(--line);
  line-height: 1.5;
}
.table-wrap {
  overflow-x: auto;
  margin: 8px 0 14px;
}
.edition {
  display: block;
  font-weight: 700;
}
.note {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
}
.limits {
  margin: 0;
  padding: 0;
  list-style: none;
  max-width: 900px;
}
.limits li {
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
  line-height: 1.6;
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 8px 0 8px;
}
.pill-link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 2px solid var(--control-border);
  text-decoration: none;
  font-weight: 700;
}
.pill-link:hover {
  border-color: var(--text-primary);
}
.fixes {
  margin: 0;
  padding: 0;
  list-style: none;
  max-width: 900px;
}
.fix {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.when {
  font-weight: 700;
  color: var(--text-secondary);
}
.fix-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.55;
}

@media (max-width: 900px) {
  .method-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
  }
  .toc {
    position: static;
  }
  .facts {
    grid-template-columns: minmax(0, 1fr);
  }
  .defs {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px 0;
  }
  .defs dd {
    margin-bottom: 10px;
  }
  .method-head h1 {
    font-size: 34px;
  }
  .part h2 {
    font-size: 24px;
  }
  .fix {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }
}
</style>
