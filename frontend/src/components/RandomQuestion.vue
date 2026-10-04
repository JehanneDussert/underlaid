<script setup>
// "Une question au hasard" (home page, docs/design/refonte-d4/,
// AccueilQuizD4): one question drawn from a short pool, three answers,
// then the right answer, an explanation and its source. Every value comes
// from the published data (key_figures.json, routes_summary.json) or a
// dated audit (data/facts.js); only the wrong answers are fixed.
// Texts validated by the project owner on 3 October 2026.
//
// The prerendered page shows the first question (readable without
// JavaScript); a random one is drawn in the browser. The verdict is
// written in words ("Réponse exacte" / "inexacte", "votre réponse") and
// announced in a live region: colour is never the only cue.
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'
import { FACTS } from '../data/facts'

const props = defineProps({
  figures: { type: Object, default: null },
  routes: { type: Object, default: null },
})
const { t, locale } = useI18n()

const nf = (v, digits = 0) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(v)
const pct = (v, digits = 0) => `${nf(v, digits)}${locale.value === 'fr' ? ' %' : '%'}`

// Each question: id, options (one right), explanation, note, sources.
const questions = computed(() => {
  const f = props.figures
  const r = props.routes
  const out = []
  const m = FACTS.metroAccessible
  out.push({
    id: 'metro',
    options: [
      { label: t('question.metro.pair', { paris: pct(m.paris, 1), ssd: pct(m.seineSaintDenis) }), right: true },
      { label: t('question.metro.pair', { paris: pct(m.seineSaintDenis), ssd: pct(m.paris, 1) }) },
      { label: t('question.metro.same') },
    ],
    explanation: t('question.metro.explanation', { paris: pct(m.paris, 1), ssd: pct(m.seineSaintDenis), d92: pct(m.hautsDeSeine, 1), d94: pct(m.valDeMarne, 1) }),
    note: t('question.metro.note'),
    sources: t('question.metro.sources'),
  })
  if (f) {
    const ssd = Math.round(f.highly_exposed_lowest_third_pct['93'])
    out.push({
      id: 'exposed',
      options: [{ label: pct(29) }, { label: pct(52) }, { label: pct(ssd), right: true }],
      explanation: t('question.exposed.explanation', { v: pct(ssd), paris: pct(Math.round(f.highly_exposed_lowest_third_pct['75'])) }),
      note: t('question.exposed.note'),
      sources: t('question.exposed.sources'),
    })
    const care = f.access_care_shares_equal_density?.['92']
    if (care) {
      out.push({
        id: 'care',
        options: [{ label: t('question.care.more'), right: true }, { label: t('question.care.same') }, { label: t('question.care.less') }],
        explanation: t('question.care.explanation', {
          a: Math.round(care.lowest_third_pct / 10),
          b: Math.round(care.highest_third_pct / 10),
          low: pct(Math.round(care.lowest_third_pct)),
          high: pct(Math.round(care.highest_third_pct)),
        }),
        note: t('question.care.note'),
        sources: t('question.care.sources'),
      })
    }
  }
  if (r) {
    const n = r.night_emergency.free
    const paris = pct(Math.round(n['75'].over30_pct))
    const inner = pct(Math.round(n.inner_suburbs.over30_pct))
    out.push({
      id: 'night',
      options: [
        { label: t('question.night.pair', { paris, inner }), right: true },
        { label: t('question.night.pair', { paris: inner, inner: paris }) },
        { label: t('question.night.same') },
      ],
      explanation: t('question.night.explanation', { paris, inner, mp: n['75'].median, mi: n.inner_suburbs.median }),
      note: t('question.night.note'),
      sources: t('question.night.sources'),
    })
  }
  return out
})

const index = ref(0)
const answer = ref(null)
const current = computed(() => questions.value[index.value % Math.max(1, questions.value.length)])
const verdict = computed(() => {
  if (answer.value === null || !current.value) return ''
  return current.value.options[answer.value].right ? t('question.right') : t('question.wrong')
})
const questionHeading = ref(null)

onMounted(() => {
  if (questions.value.length) index.value = Math.floor(Math.random() * questions.value.length)
})

function choose(i) {
  if (answer.value !== null) return
  answer.value = i
}
async function another() {
  const n = questions.value.length
  if (n > 1) index.value = (index.value + 1 + Math.floor(Math.random() * (n - 1))) % n
  answer.value = null
  await nextTick()
  questionHeading.value?.focus()
}
function optionState(i, option) {
  if (answer.value === null) return ''
  if (option.right) return 'right'
  if (i === answer.value) return 'wrong'
  return 'other'
}
</script>

<template>
  <section class="question-section container" aria-labelledby="question-title">
    <div class="question-intro">
      <p class="question-kicker"><span class="kicker-dot" aria-hidden="true"></span>{{ t('question.kicker') }}</p>
      <h2 id="question-title" class="question-title">{{ t('question.title') }}</h2>
      <p class="question-lead">{{ t('question.lead') }}</p>
    </div>
    <div v-if="current" class="question-card">
      <h3 ref="questionHeading" class="question-text" tabindex="-1">{{ t(`question.${current.id}.question`) }}</h3>
      <ul class="question-options">
        <li v-for="(option, i) in current.options" :key="`${current.id}-${i}`">
          <button
            type="button"
            class="question-option"
            :class="optionState(i, option)"
            :aria-disabled="answer !== null ? 'true' : undefined"
            @click="choose(i)"
          >
            <span>{{ option.label }}</span>
            <span v-if="answer !== null && option.right" class="option-tag">
              <svg aria-hidden="true" width="14" height="14" viewBox="0 0 14 14"><path d="M2 7.5 5.5 11 12 3.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg>
              {{ t('question.rightTag') }}
            </span>
            <span v-else-if="answer === i" class="option-tag">{{ t('question.yourAnswer') }}</span>
          </button>
        </li>
      </ul>
      <p class="sr-only" aria-live="polite">{{ verdict }}</p>
      <div v-if="answer !== null" class="question-answer">
        <p class="question-verdict">{{ verdict }}</p>
        <p class="question-explanation">{{ current.explanation }}</p>
        <p class="question-note">{{ current.note }} {{ t('figure.sources', { sources: current.sources }) }}</p>
      </div>
      <div class="question-actions">
        <button type="button" class="pill-button" @click="another">{{ t('question.another') }}</button>
        <router-link class="question-map" :to="{ name: localizedRouteName('map', locale) }">{{ t('question.seeMap') }} <span aria-hidden="true">→</span></router-link>
      </div>
    </div>
  </section>
</template>

<style scoped>
.question-section {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 64px;
  align-items: start;
  padding-top: 88px;
}
.question-kicker {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 10px;
  color: var(--accent);
  font-weight: 700;
  font-size: 15px;
}
.kicker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
}
.question-title {
  margin: 0 0 12px;
  font-size: 36px;
  line-height: 1.1;
  letter-spacing: -0.01em;
}
.question-lead {
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
  color: var(--text-secondary);
  max-width: 460px;
}
.question-card {
  border: 2px solid var(--text-primary);
  border-radius: 24px;
  padding: 28px;
}
.question-text {
  margin: 0 0 20px;
  font-size: 21px;
  line-height: 1.4;
}
.question-text:focus {
  outline: none;
}
.question-text:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 4px;
}
.question-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.question-option {
  width: 100%;
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 18px;
  border: 2px solid var(--control-border);
  border-radius: 14px;
  background: var(--surface);
  color: var(--text-primary);
  font: inherit;
  font-size: 17px;
  text-align: left;
  cursor: pointer;
}
.question-option:hover:not([aria-disabled]) {
  border-color: var(--text-primary);
}
.question-option[aria-disabled] {
  cursor: default;
}
.question-option.right {
  border-color: var(--mode-free);
  background: var(--mode-free-bg);
  font-weight: 700;
}
.question-option.wrong {
  border-color: var(--accent);
  background: var(--accent-tint);
}
.question-option.other {
  border-color: var(--line);
  color: var(--text-secondary);
}
.option-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.question-answer {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}
.question-verdict {
  margin: 0 0 8px;
  font-weight: 700;
}
.question-explanation {
  margin: 0 0 8px;
  font-size: 17px;
  line-height: 1.55;
}
.question-note {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-muted);
}
.question-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
}
.pill-button {
  min-height: 44px;
  padding: 0 20px;
  border-radius: 999px;
  border: 2px solid var(--control-border);
  background: var(--surface);
  color: var(--text-primary);
  font: inherit;
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
}
.pill-button:hover {
  border-color: var(--text-primary);
}
.question-map {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
}

@media (max-width: 900px) {
  .question-section {
    grid-template-columns: 1fr;
    gap: 24px;
    padding-top: 56px;
  }
  .question-title {
    font-size: 28px;
  }
  .question-card {
    padding: 20px;
  }
  .question-text {
    font-size: 19px;
  }
}
</style>
