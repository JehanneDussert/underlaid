<script setup>
import { ref, computed, onMounted, onServerPrefetch } from 'vue'
import { useI18n } from 'vue-i18n'
import { localizedRouteName } from '../router'
import { useSeoMeta } from '../composables/useSeoMeta'
import { loadStaticJson } from '../utils/loadStaticJson'

const { t, locale } = useI18n()
const DATA_URL = '/data/vulnerability_score_iris.geojson'

// Injected at build time (vite.config.js) from the actual scoring
// output — never hardcoded, so this count can't silently drift out of
// sync with the pipeline the way a hand-typed number would.
useSeoMeta({
  title: {
    en: `Where the Most Stacks Up — ${__RANKING_COUNT__} Most-Exposed Neighborhoods`,
    fr: `Là où le cumul est le plus fort — les ${__RANKING_COUNT__} quartiers les plus exposés`,
  },
  description: {
    en: `The ${__RANKING_COUNT__} neighborhoods in Paris and its inner suburbs where heat, pollution, poor access to services, and inefficient housing cumulate most — split into two groups by whether a lack of services is actually the cause, each explained neighborhood by neighborhood.`,
    fr: `Les ${__RANKING_COUNT__} quartiers de Paris et de la petite couronne où la chaleur, la pollution, le manque d'accès aux services et le logement énergivore se cumulent le plus — répartis en deux groupes selon qu'un déficit de services en est réellement la cause, expliqué quartier par quartier.`,
  },
})

const rows = ref([])
const loading = ref(true)

// Editorial rule for this project: always "what the city hasn't brought to
// this neighborhood," never "what this neighborhood lacks" — the gap is
// framed as an external provision failure, not an inherent deficiency.
// That framing only holds where a service genuinely falls short, though:
// applying it to a neighborhood with decent-to-excellent access (several
// among the metro area's wealthiest) would assert a public shortfall that
// doesn't exist there. Split into two groups by whether the access
// sub-score itself is the worst-quartile factor, each with its own wording.
const GAP_KEYS_UNDERSERVED = {
  thermal: 'ranking.gapThermal',
  pollution: 'ranking.gapPollution',
  housing: 'ranking.gapHousing',
}

const GAP_KEYS_DENSE = {
  thermal: 'ranking.denseGapThermal',
  pollution: 'ranking.denseGapPollution',
  housing: 'ranking.denseGapHousing',
}

// The access sub-score is a mean of 4 quite different indicators (travel
// time, nearby school segregation, documented wheelchair accessibility,
// footway density) — audited manually (Val de Grâce 6, Champs-Élysées 2,
// Sorbonne 3/4, École Militaire 5, then a full pass over the ranking; see
// SCORING.md's "Access time's compressed distribution") and found that a
// single static "nearby health, education, and transport services" phrase
// mischaracterizes most of these rows: only a minority are actually driven
// by travel time, the rest by school segregation or sparse pedestrian
// infrastructure — both real, but not about distance to services at all.
// `access_primary_driver` (added to the pipeline output for this reason)
// picks the phrase that actually reflects what's driving the sub-score,
// rather than always defaulting to the same generic clause.
const ACCESS_GAP_KEYS_BY_DRIVER = {
  access_time: 'ranking.gapAccessTime',
  school_segregation: 'ranking.gapAccessSchool',
  mobility_accessibility_deficit: 'ranking.gapAccessMobility',
  pedestrian_path_deficit: 'ranking.gapAccessFootway',
}

function accessGapKey(p) {
  return ACCESS_GAP_KEYS_BY_DRIVER[p.access_primary_driver] || 'ranking.gapAccessTime'
}

// Loaded via onServerPrefetch during vite-ssg's build-time prerendering
// (so /ranking's ~58 real neighborhood names/scores land in the actual
// HTML, not just after client JS runs) and again via onMounted in the
// browser — this project has no initialState/hydration wiring, so the
// client fetch simply re-fetches the same static JSON rather than
// reusing the server-rendered data; harmless, just one extra request.
async function loadRows() {
  const geojson = await loadStaticJson(DATA_URL)
  rows.value = geojson.features
    .map((f) => f.properties)
    .filter((p) => p.cumulative_vulnerability_score === 3)
    .sort((a, b) => a.insee_com - b.insee_com || a.nom_iris.localeCompare(b.nom_iris))
  loading.value = false
}

onServerPrefetch(loadRows)
onMounted(loadRows)

function isUnderserved(p) {
  return p.subscore_access_quartile === 4
}

const groupA = computed(() => rows.value.filter(isUnderserved))
const groupB = computed(() => rows.value.filter((p) => !isUnderserved(p)))

function affectedCategories(p) {
  return ['thermal', 'pollution', 'access', 'housing'].filter((key) => p[`subscore_${key}_quartile`] === 4)
}

function accessTimeMinutes(p) {
  const vals = [p.access_minutes_domain_C, p.access_minutes_domain_D, p.access_minutes_domain_E].filter(
    (v) => v !== null && v !== undefined
  )
  if (!vals.length) return null
  return vals.reduce((a, b) => a + b, 0) / vals.length
}

// access_time's own distribution is heavily floor-clustered (most of the
// metro area ties near "1 minute"), so its z-score can swing hard from a
// tiny absolute difference — audited directly against Val de Grâce 6 and
// Champs-Élysées 2 (see SCORING.md's "Access time's compressed
// distribution" caveat): both land in the worst access quartile mainly
// because of access_time, despite raw times of ~1.2-1.6 min. Among all
// IRIS where access_time is the dominant driver of a worst-quartile
// access score, 94% sit at or under 2.0 min (median 1.33, 90th
// percentile 1.7) — only a genuine 6% tail is slower than that. 2.0 min
// is chosen to cover that 94%, so the caveat fires for the cases the
// audit actually found (Val de Grâce 6 at 1.57 min included), while
// still letting the small genuinely-slow tail read as an unqualified
// service shortfall.
const ACCESS_TIME_FAST_THRESHOLD_MIN = 2.0

function formatMinutes(value) {
  return new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-US', { maximumFractionDigits: 1 }).format(value)
}

// Found via manual audit (see SCORING.md's "Access time's compressed
// distribution"): the previous version of this function asserted "the
// city hasn't brought nearby health, education, and transport services"
// in the main sentence whenever access_time was the dominant driver,
// then — only when that time was actually fast — appended a caveat
// contradicting its own opening clause ("access itself is fast here in
// absolute terms..."). A reader who stops at the first sentence walks
// away with exactly the false impression the caveat existed to prevent.
// Fixed at the structure, not just the wording: a fast access_time is
// now never described as a service shortfall in the first place — it's
// excluded from the "hasn't brought X" list entirely and described
// honestly, from its very first mention, in a separate sentence that
// never asserts the opposite of what it goes on to say.
function isFastAccessTimeCase(p) {
  if (!isUnderserved(p) || p.access_primary_driver !== 'access_time') return false
  const minutes = accessTimeMinutes(p)
  return minutes !== null && minutes <= ACCESS_TIME_FAST_THRESHOLD_MIN
}

function gapSentence(p) {
  const keys = isUnderserved(p) ? GAP_KEYS_UNDERSERVED : GAP_KEYS_DENSE
  const fastAccessTime = isFastAccessTimeCase(p)
  const categories = affectedCategories(p).filter((key) => !(key === 'access' && fastAccessTime))
  const clauses = categories.map((key) => (key === 'access' ? t(accessGapKey(p)) : t(keys[key])))
  const listFormat = new Intl.ListFormat(locale.value === 'fr' ? 'fr-FR' : 'en-US', { style: 'long', type: 'conjunction' })
  const sentenceKey = isUnderserved(p) ? 'ranking.gapSentence' : 'ranking.denseSentence'
  let sentence = t(sentenceKey, { list: listFormat.format(clauses) })

  if (fastAccessTime) {
    const minutes = accessTimeMinutes(p)
    sentence += ' ' + t('ranking.accessTimeRelativeOnly', { min: formatMinutes(minutes) })
  }

  return sentence
}
</script>

<template>
  <div class="ranking-view">
    <router-link class="back-link" :to="{ name: localizedRouteName('home', locale) }">{{ t('methodology.backLink') }}</router-link>

    <h1>{{ t('ranking.title') }}</h1>
    <p class="intro">{{ t('ranking.intro') }}</p>
    <p class="intro-split">{{ t('ranking.introSplit') }}</p>

    <p v-if="loading" class="loading">{{ t('scatter.loading') }}</p>
    <template v-else>
      <section class="ranking-group">
        <h2 class="group-title">{{ t('ranking.groupATitle', { n: groupA.length }) }}</h2>
        <p class="group-desc">{{ t('ranking.groupADesc') }}</p>
        <ol class="ranking-list">
          <li v-for="p in groupA" :key="p.code_iris" class="ranking-row glass">
            <div class="row-head">
              <span class="name">{{ p.nom_iris }}</span>
              <span class="commune">{{ p.nom_com }}</span>
            </div>
            <p class="gap-sentence">{{ gapSentence(p) }}</p>
          </li>
        </ol>
      </section>

      <section class="ranking-group">
        <h2 class="group-title">{{ t('ranking.groupBTitle', { n: groupB.length }) }}</h2>
        <p class="group-desc">{{ t('ranking.groupBDesc') }}</p>
        <ol class="ranking-list">
          <li v-for="p in groupB" :key="p.code_iris" class="ranking-row glass">
            <div class="row-head">
              <span class="name">{{ p.nom_iris }}</span>
              <span class="commune">{{ p.nom_com }}</span>
            </div>
            <p class="gap-sentence">{{ gapSentence(p) }}</p>
          </li>
        </ol>
      </section>
    </template>

    <p v-if="!loading" class="footnote">{{ t('ranking.footnote', { n: rows.length }) }}</p>
  </div>
</template>

<style scoped>
.ranking-view {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 40px 64px;
}
@media (max-width: 920px) {
  .ranking-view {
    padding: 28px 20px 48px;
  }
}

.back-link {
  display: inline-block;
  margin-bottom: 24px;
  font-size: 12.5px;
  color: var(--text-secondary);
  text-decoration: none;
}
.back-link:hover {
  color: var(--cyan);
}

h1 {
  font-weight: 700;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.08;
  margin: 0 0 16px;
  letter-spacing: -0.02em;
}

.intro {
  font-size: 15px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 14px;
}

.intro-split {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin: 0 0 28px;
  padding: 14px 16px;
  border-left: 2px solid var(--cyan);
  background: rgba(255, 255, 255, 0.02);
}

.loading {
  color: var(--text-secondary);
  font-size: 13px;
}

.ranking-group {
  margin-bottom: 32px;
}
.ranking-group:last-child {
  margin-bottom: 0;
}

.group-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--text-primary);
}

.group-desc {
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-muted);
  margin: 0 0 14px;
}

.ranking-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-row {
  padding: 16px 20px;
}

.row-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.name {
  font-weight: 700;
  font-size: 15px;
  color: var(--text-primary);
}
.commune {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--mono);
}

.gap-sentence {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-secondary);
}

.footnote {
  margin-top: 24px;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
