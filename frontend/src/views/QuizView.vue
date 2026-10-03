<script setup>
// Quiz (mock-up docs/maquettes/Devinez.dc.html): one question at a time,
// phone-sized, answers that run against common assumptions. Every answer
// comes from a dated, sourced figure (src/data/facts.js or
// key_figures.json) and is worded with the exact definition (stop points,
// not stations). The train-station question (14 of 459 "on one's own")
// was removed: it could not be cross-checked (see src/data/facts.js).
// The verdict is announced in a live region; focus moves to the next
// question's heading.
import { computed, nextTick, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import FigureSource from '../components/FigureSource.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { FACTS } from '../data/facts'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()

useSeoMeta({
  title: { en: 'Quiz: four questions on unequal living conditions', fr: 'Quiz : quatre questions sur des conditions de vie inégales' },
  description: {
    en: 'Four questions on wheelchair access to public transport, public data and exposure in Paris and its inner suburbs, with the sourced answer to each.',
    fr: "Quatre questions sur l'accès en fauteuil roulant aux transports, les données publiques et l'exposition à Paris et en petite couronne, avec la réponse sourcée de chacune.",
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

const pct = (value, digits = 0) =>
  new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { style: 'percent', minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value / 100)
const nf = (value) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB').format(value)

const questions = computed(() => {
  const m = FACTS.metroAccessible
  const sw = FACTS.sidewalkInfo
  const ssdExposed = Math.round(figures.value?.highly_exposed_lowest_third_pct?.['93'] ?? 0)
  return [
    {
      id: 'metro',
      options: [
        { id: '75', label: t('home.dep.75') },
        { id: '92', label: t('home.dep.92') },
        { id: '93', label: t('home.dep.93'), right: true },
        { id: '94', label: t('home.dep.94') },
      ],
      explanation: t('quiz.q.metro.explanation', { p: pct(m.paris, 1), d92: pct(m.hautsDeSeine, 1), d93: pct(m.seineSaintDenis), d94: pct(m.valDeMarne, 1) }),
      sources: t('quiz.q.metro.sources'),
      anchor: 'sources',
    },
    {
      id: 'sidewalks',
      options: [
        { id: 'a', label: pct(sw.seineSaintDenis), right: true },
        { id: 'b', label: pct(61) },
        { id: 'c', label: pct(sw.paris) },
      ],
      explanation: t('quiz.q.sidewalks.explanation', { ssd: pct(sw.seineSaintDenis), paris: pct(sw.paris) }),
      sources: t('quiz.q.sidewalks.sources'),
      anchor: 'corrections',
      ownDate: true,
    },
    {
      id: 'exposed',
      options: [
        { id: 'a', label: pct(29) },
        { id: 'b', label: pct(52) },
        { id: 'c', label: pct(ssdExposed), right: true },
      ],
      explanation: t('quiz.q.exposed.explanation', { v: pct(ssdExposed), paris: pct(Math.round(figures.value?.highly_exposed_lowest_third_pct?.['75'] ?? 0)) }),
      sources: t('quiz.q.exposed.sources'),
      anchor: 'calcul',
    },
    {
      id: 'care',
      options: [
        { id: 'better', label: t('quiz.q.care.better') },
        { id: 'same', label: t('quiz.q.care.same') },
        { id: 'worse', label: t('quiz.q.care.worse'), right: true },
      ],
      explanation: t('quiz.q.care.explanation', {
        gap: nf(Math.round(figures.value?.access_care_gap_equal_density?.['92'] ?? 23)),
        low: pct(Math.round(figures.value?.access_care_by_means?.['92']?.lowest_third_pct ?? 41)),
        high: pct(Math.round(figures.value?.access_care_by_means?.['92']?.highest_third_pct ?? 24)),
      }),
      sources: t('quiz.q.care.sources'),
      anchor: 'calcul',
    },
  ]
})

const index = ref(0)
const picks = ref([])
const finished = ref(false)
const heading = ref(null)

const current = computed(() => questions.value[index.value])
const picked = computed(() => picks.value[index.value] ?? null)
const score = computed(() => picks.value.filter((p, i) => questions.value[i]?.options.find((o) => o.id === p)?.right).length)
const isRight = computed(() => current.value.options.find((o) => o.id === picked.value)?.right === true)
const rightLabel = computed(() => current.value.options.find((o) => o.right).label)

function choose(optionId) {
  if (picked.value) return
  picks.value[index.value] = optionId
}

async function next() {
  if (index.value < questions.value.length - 1) index.value++
  else finished.value = true
  await nextTick()
  heading.value?.focus()
}

async function restart() {
  index.value = 0
  picks.value = []
  finished.value = false
  await nextTick()
  heading.value?.focus()
}

function optionState(option) {
  if (!picked.value) return ''
  if (option.right) return 'right'
  if (option.id === picked.value) return 'wrong'
  return 'off'
}
</script>

<template>
  <div class="quiz-page">
    <div class="quiz-card">
      <template v-if="!finished">
        <div class="progress-row">
          <span>{{ t('quiz.progress', { n: index + 1, total: questions.length }) }}</span>
          <span>{{ t('quiz.score', { n: score }) }}</span>
        </div>
        <div class="progress" aria-hidden="true"><span :style="{ width: `${(100 * (index + (picked ? 1 : 0))) / questions.length}%` }"></span></div>
        <p class="kicker">{{ t('site.nav.quiz') }}</p>
        <h1 ref="heading" tabindex="-1">{{ t(`quiz.q.${current.id}.question`) }}</h1>
        <div class="options" role="group" :aria-label="t('quiz.optionsLabel')">
          <button
            v-for="o in current.options"
            :key="o.id"
            type="button"
            :class="['option', optionState(o)]"
            :aria-pressed="picked === o.id"
            :aria-disabled="picked ? 'true' : undefined"
            @click="choose(o.id)"
          >{{ o.label }}</button>
        </div>
        <div aria-live="polite">
          <div v-if="picked" class="answer">
            <p class="verdict">{{ isRight ? t('quiz.right') : t('quiz.wrong', { answer: rightLabel }) }}</p>
            <p>{{ current.explanation }}</p>
            <FigureSource :sources="current.sources" :anchor="current.anchor" :show-date="!current.ownDate" dark />
          </div>
        </div>
        <button v-if="picked" type="button" class="next" @click="next">
          {{ index < questions.length - 1 ? t('quiz.next') : t('quiz.seeResult') }}
        </button>
      </template>

      <template v-else>
        <p class="kicker">{{ t('site.nav.quiz') }}</p>
        <h1 ref="heading" tabindex="-1">{{ t('quiz.result', { n: score, total: questions.length }) }}</h1>
        <p class="end-text">{{ t('quiz.endText') }}</p>
        <div class="end-links">
          <router-link class="next" :to="{ name: localizedRouteName('address', locale) }">{{ t('quiz.toAddress') }}</router-link>
          <router-link class="secondary" :to="{ name: localizedRouteName('methodology', locale) }">{{ t('quiz.toMethod') }}</router-link>
          <button type="button" class="secondary" @click="restart">{{ t('quiz.restart') }}</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.quiz-page {
  padding: 32px 16px 48px;
  display: flex;
  justify-content: center;
}
.quiz-card {
  width: 100%;
  max-width: 480px;
  min-height: 640px;
  box-sizing: border-box;
  background: var(--dark);
  color: #ffffff;
  border-radius: 24px;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.progress-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #bfc3ca;
}
.progress {
  height: 6px;
  border-radius: 3px;
  background: #2c3036;
}
.progress span {
  display: block;
  height: 6px;
  border-radius: 3px;
  background: var(--accent-on-dark);
  transition: width 300ms;
}
.kicker {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-on-dark);
}
h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.18;
  letter-spacing: -0.02em;
}
h1:focus {
  outline: none;
}
.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option {
  min-height: 56px;
  border-radius: 12px;
  padding: 0 18px;
  text-align: left;
  font: inherit;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  background: transparent;
  color: #ffffff;
  border: 1.5px solid #868b94;
}
.option.right {
  background: #ffffff;
  color: var(--dark);
  border-color: #ffffff;
}
.option.wrong {
  color: #bfc3ca;
  border-style: dashed;
  border-color: #bfc3ca;
}
.option.off {
  color: #bfc3ca;
}
.option[aria-disabled='true'] {
  cursor: default;
}
.answer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border-radius: 16px;
  background: #22262c;
}
.answer p {
  margin: 0;
  font-size: 15px;
  line-height: 1.5;
  color: #d4d7dc;
}
.answer .verdict {
  font-size: 19px;
  font-weight: 700;
  color: #ffffff;
}
.next {
  margin-top: auto;
  min-height: 52px;
  border-radius: 12px;
  border: none;
  background: #ffffff;
  color: var(--dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font: inherit;
  font-weight: 700;
  font-size: 16px;
  text-decoration: none;
  cursor: pointer;
}
.end-text {
  margin: 0;
  font-size: 16px;
  line-height: 1.5;
  color: #d4d7dc;
}
.end-links {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.secondary {
  min-height: 48px;
  border-radius: 12px;
  border: 1.5px solid #ffffff;
  background: transparent;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font: inherit;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}
.quiz-card :focus-visible {
  outline-color: #ffffff;
}
</style>
