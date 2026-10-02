<script setup>
// Home page of the redesign (mock-up docs/maquettes/Main.dc.html): the
// address field first, then the main findings, each with its source and
// data date. Figures come from public/data/key_figures.json (computed from
// the published data) or src/data/facts.js (dated audits), never typed in
// the text.
import { computed, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddressSearch from '../components/AddressSearch.vue'
import FigureSource from '../components/FigureSource.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { FACTS } from '../data/facts'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()
const router = useRouter()

useSeoMeta({
  title: { en: 'One city, unequal living conditions', fr: 'Une même ville, des conditions de vie inégales' },
  description: {
    en: 'Heat, air pollution and noise, housing, access to care: the gaps between the 2,752 neighbourhoods of Paris and its inner suburbs, measured from public data.',
    fr: "Chaleur, pollution de l'air et bruit, logement, accès aux soins : les écarts entre les 2 752 quartiers de Paris et de la petite couronne, mesurés à partir de données publiques.",
  },
})

const figures = ref(null)
async function loadFigures() {
  figures.value = await loadStaticJson('/data/key_figures.json')
}
onServerPrefetch(loadFigures)
onMounted(() => {
  if (!figures.value) loadFigures()
})

const fmt = (value, digits = 0) =>
  new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value)
// Locale-aware percentage ("79 %" in French, "79%" in English).
const pct = (value, digits = 0) =>
  new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value / 100)
const DEP_ORDER = ['93', '94', '92', '75']

const exposedBars = computed(() => {
  const shares = figures.value?.highly_exposed_lowest_third_pct
  if (!shares) return []
  return DEP_ORDER.map((d) => ({ dep: d, name: t(`home.dep.${d}`), value: Math.round(shares[d]) }))
})

const careRows = computed(() => {
  const gaps = figures.value?.access_care_by_means
  if (!gaps) return []
  return ['92', '94'].map((d) => ({
    dep: d,
    name: t(`home.dep.${d}`),
    low: Math.round(gaps[d].lowest_third_pct),
    high: Math.round(gaps[d].highest_third_pct),
  }))
})
const wheelchair = computed(() => figures.value?.wheelchair_gp_median)

// Metro question: one answer, announced in a live region.
const answer = ref(null)
const answerText = computed(() => {
  if (!answer.value) return ''
  return answer.value === 'ssd' ? t('home.quiz.right') : t('home.quiz.wrong')
})

function goToAddress({ label, lon, lat }) {
  router.push({ name: localizedRouteName('address', locale.value), query: { lon, lat, label } })
}
</script>

<template>
  <div class="home">
    <section class="container hero">
      <p class="eyebrow">{{ t('home.eyebrow') }}</p>
      <h1>{{ t('home.title') }}</h1>
      <p class="lead">{{ t('home.lead') }}</p>
      <AddressSearch id="home-address" :label="t('address.label')" :placeholder="t('address.placeholder')" @select="goToAddress" />
      <p class="hint">{{ t('home.hint') }}</p>
    </section>

    <section class="band" aria-labelledby="f1">
      <div class="container finding">
        <div class="text">
          <p class="num" aria-hidden="true">01</p>
          <h2 id="f1">{{ t('home.f1.title', { n: figures?.at_max?.length ?? 4 }) }}</h2>
          <p>{{ t('home.f1.body') }}</p>
          <p v-if="figures">{{ t('home.f1.body2', { n: figures.n_three_plus_inhabited }) }}</p>
          <p class="links">
            <router-link :to="{ name: localizedRouteName('map', locale) }">{{ t('home.f1.mapLink') }}</router-link>
            <router-link :to="{ name: localizedRouteName('ranking', locale) }">{{ t('home.f1.listLink', { n: figures?.n_three_plus_inhabited ?? '' }) }}</router-link>
          </p>
        </div>
        <figure class="card map-card">
          <img :src="'/home-map.png'" :alt="t('home.f1.alt')" width="1092" height="899" loading="lazy" />
          <figcaption>
            <span class="legend-title">{{ t('home.f1.legend') }}</span>
            <span class="ramp" aria-hidden="true">
              <span>0</span>
              <i v-for="c in ['#e09ab7', '#d2668f', '#bf336a', '#980f48', '#5f002d']" :key="c" :style="{ background: c }"></i>
              <span>4</span>
            </span>
            <FigureSource :sources="t('home.f1.sources')" anchor="calcul" />
          </figcaption>
        </figure>
      </div>
    </section>

    <section class="band" aria-labelledby="f2">
      <div class="container finding">
        <div class="text">
          <p class="num" aria-hidden="true">02</p>
          <h2 id="f2">{{ t('home.f2.title') }}</h2>
          <p>{{ t('home.f2.body') }}</p>
          <p>{{ t('home.f2.body2', { rho: figures ? fmt(figures.spearman_means_exposure, 2) : '' }) }}</p>
        </div>
        <div class="card chart">
          <h3 class="chart-q">{{ t('home.f2.question') }}</h3>
          <ul class="bars" role="list">
            <li v-for="b in exposedBars" :key="b.dep">
              <span class="bar-label"><span>{{ b.name }}</span><strong>{{ pct(b.value) }}</strong></span>
              <span class="track" aria-hidden="true"><span class="fill" :style="{ width: `${b.value}%` }"></span></span>
            </li>
          </ul>
          <p class="def">{{ t('home.f2.definition') }}</p>
          <FigureSource :sources="t('home.f2.sources')" anchor="calcul" />
        </div>
      </div>
    </section>

    <section class="band dark" aria-labelledby="q1">
      <div class="container quiz">
        <p class="kicker">{{ t('home.quiz.kicker') }}</p>
        <h2 id="q1">{{ t('home.quiz.question') }}</h2>
        <div class="choices" role="group" :aria-labelledby="'q1'">
          <button type="button" :aria-pressed="answer === 'paris'" @click="answer = 'paris'">{{ t('home.dep.75') }}</button>
          <button type="button" :aria-pressed="answer === 'ssd'" @click="answer = 'ssd'">{{ t('home.dep.93') }}</button>
        </div>
        <div aria-live="polite">
          <div v-if="answer" class="verdict">
            <p class="verdict-title">{{ answerText }}</p>
            <p>{{ t('home.quiz.explanation', { ssd: pct(FACTS.metroAccessible.seineSaintDenis), paris: pct(FACTS.metroAccessible.paris, 1) }) }}</p>
          </div>
        </div>
        <FigureSource :sources="t('home.quiz.sources')" anchor="sources" dark />
      </div>
    </section>

    <section class="band" aria-labelledby="f3">
      <div class="container finding">
        <div class="text">
          <p class="num" aria-hidden="true">03</p>
          <h2 id="f3">{{ t('home.f3.title') }}</h2>
          <p>{{ t('home.f3.body') }}</p>
        </div>
        <div class="card chart">
          <h3 class="chart-q">{{ t('home.f3.question') }}</h3>
          <div v-for="r in careRows" :key="r.dep" class="pair">
            <p class="pair-name">{{ r.name }}</p>
            <ul class="bars" role="list">
              <li>
                <span class="bar-label"><span>{{ t('home.f3.lowest') }}</span><strong>{{ pct(r.low) }}</strong></span>
                <span class="track" aria-hidden="true"><span class="fill" :style="{ width: `${r.low}%` }"></span></span>
              </li>
              <li>
                <span class="bar-label"><span>{{ t('home.f3.highest') }}</span><strong>{{ pct(r.high) }}</strong></span>
                <span class="track" aria-hidden="true"><span class="fill muted" :style="{ width: `${r.high}%` }"></span></span>
              </li>
            </ul>
          </div>
          <p class="def">{{ t('home.f3.density', { n92: fmt(FACTS.careGapEqualDensity.hautsDeSeine), n94: fmt(FACTS.careGapEqualDensity.valDeMarne) }) }}</p>
          <p v-if="wheelchair" class="def">{{ t('home.f3.wheelchair', { p: fmt(wheelchair['75'], 1), d92: fmt(wheelchair['92'], 1), d93: fmt(wheelchair['93'], 1), d94: fmt(wheelchair['94'], 1) }) }}</p>
          <FigureSource :sources="t('home.f3.sources')" anchor="calcul" />
        </div>
      </div>
    </section>

    <section class="band" aria-labelledby="f4">
      <div class="container finding">
        <div class="text">
          <p class="num" aria-hidden="true">04</p>
          <h2 id="f4">{{ t('home.f4.title') }}</h2>
          <p>{{ t('home.f4.body') }}</p>
        </div>
        <div>
          <div class="stats">
            <div class="card stat">
              <span class="big">{{ pct(FACTS.sidewalkInfo.paris) }}</span>
              <span>{{ t('home.f4.paris') }}</span>
            </div>
            <div class="card stat">
              <span class="big accent">{{ pct(FACTS.sidewalkInfo.seineSaintDenis) }}</span>
              <span>{{ t('home.f4.ssd') }}</span>
            </div>
          </div>
          <FigureSource :sources="t('home.f4.sources')" anchor="corrections" :show-date="false" />
        </div>
      </div>
    </section>

    <section class="band" aria-labelledby="consult">
      <div class="container consult">
        <h2 id="consult">{{ t('home.consult') }}</h2>
        <AddressSearch id="home-address-2" :label="t('address.label')" hide-label :placeholder="t('address.placeholderShort')" @select="goToAddress" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  padding-top: 96px;
  padding-bottom: 120px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.eyebrow {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
}
h1 {
  margin: 0;
  font-size: clamp(42px, 7vw, 72px);
  line-height: 1.02;
  letter-spacing: -0.035em;
  font-weight: 800;
  max-width: 900px;
}
.lead {
  margin: 0;
  font-size: clamp(18px, 2.2vw, 22px);
  line-height: 1.45;
  color: var(--text-body);
  max-width: 680px;
}
.hint {
  margin: -12px 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.band {
  border-top: 1px solid var(--line);
}
.finding {
  padding-top: 96px;
  padding-bottom: 96px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 64px;
  align-items: center;
}
.text {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.text p {
  margin: 0;
  font-size: 18px;
  line-height: 1.55;
  color: var(--text-body);
}
.text .num {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-secondary);
}
h2 {
  margin: 0;
  font-size: clamp(30px, 4vw, 40px);
  line-height: 1.1;
  letter-spacing: -0.025em;
}
.links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  font-weight: 600;
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 28px;
}
.map-card {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
.map-card img {
  display: block;
  width: 100%;
  height: auto;
}
.map-card figcaption {
  padding: 16px 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.legend-title {
  font-size: 14px;
  color: var(--text-body);
}
.ramp {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 13px;
  color: var(--text-body);
}
.ramp i {
  width: 40px;
  height: 10px;
  border-radius: 3px;
}

.chart {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.chart-q {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
}
.bars {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.bars li {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.bar-label {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 15px;
}
.track {
  height: 14px;
  border-radius: 4px;
  background: var(--line-soft);
}
.fill {
  display: block;
  height: 14px;
  border-radius: 4px;
  background: var(--accent);
}
.fill.muted {
  background: #5b616b;
}
.pair-name {
  margin: 0 0 8px;
  font-weight: 700;
}
.def {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-secondary);
}

.dark {
  background: var(--dark);
  color: var(--text-on-dark);
  border-top: none;
}
.quiz {
  padding-top: 96px;
  padding-bottom: 96px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.quiz h2 {
  max-width: 760px;
}
.kicker {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-on-dark);
}
.choices {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.choices button {
  min-height: 56px;
  padding: 0 28px;
  border-radius: var(--radius-small);
  border: 1.5px solid #ffffff;
  background: transparent;
  color: #ffffff;
  font: inherit;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
}
.choices button[aria-pressed='true'] {
  background: #ffffff;
  color: var(--dark);
}
.dark :focus-visible {
  outline-color: #ffffff;
}
.verdict {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 760px;
}
.verdict p {
  margin: 0;
  font-size: 18px;
  line-height: 1.55;
  color: var(--text-on-dark-secondary);
}
.verdict .verdict-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-on-dark);
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 12px;
}
.stat {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 15px;
  color: var(--text-body);
}
.big {
  font-size: 56px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}
.big.accent {
  color: var(--accent);
}

.consult {
  padding-top: 112px;
  padding-bottom: 112px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  align-items: flex-start;
}
.consult h2 {
  font-size: clamp(36px, 5vw, 56px);
  letter-spacing: -0.03em;
}

@media (max-width: 860px) {
  .finding {
    grid-template-columns: minmax(0, 1fr);
    gap: 32px;
    padding-top: 64px;
    padding-bottom: 64px;
  }
  .hero {
    padding-top: 48px;
    padding-bottom: 72px;
  }
  .quiz,
  .consult {
    padding-top: 64px;
    padding-bottom: 64px;
  }
  .big {
    font-size: 44px;
  }
}
</style>
