<script setup>
// "Votre quartier" (redesign D4, docs/design/refonte-d4/: 03, 03b, 03c, 11,
// 12): one neighbourhood, by its INSEE code in the URL (/quartier/<code>,
// never an address). Sticky bar (address, three modes), title from the
// templates validated on 3 October 2026, then:
//   1. Le cadre de vie — heat, air and noise, housing, ranked among the
//      2,752 neighbourhoods;
//   2. Ce qui est à portée — access to care, then the nearest place for
//      each need, for no mode (three durations), one mode, or one mode
//      compared with another;
//   3. Les deux à la fois — where the neighbourhood stands on exposure and
//      access to care (descriptive), with the tested hypothesis as stated
//      in the method.
// Data: one file per commune (scripts/39_neighbourhood_files.py).
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AccordionItem from '../components/AccordionItem.vue'
import AddressSearch from '../components/AddressSearch.vue'
import LoadingDots from '../components/LoadingDots.vue'
import ModeToggle from '../components/ModeToggle.vue'
import NeighbourhoodScatter from '../components/NeighbourhoodScatter.vue'
import RankBar from '../components/RankBar.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { MODES } from '../data/modes'
import { NEEDS } from '../data/needs'
import { localizedRouteName } from '../router'
import { findNeighbourhood, loadCommune, loadIndex, loadNeighbourhood, rememberNeighbourhood } from '../utils/neighbourhood'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

useSeoMeta({
  title: { en: 'Your neighbourhood', fr: 'Votre quartier' },
  description: {
    en: 'Heat, air and noise, housing, access to care and everyday places: the situation of a neighbourhood of Paris or its inner suburbs, depending on how you get around.',
    fr: "Chaleur, air et bruit, logement, accès aux soins et lieux du quotidien : la situation d'un quartier de Paris ou de la petite couronne, selon votre façon de vous déplacer.",
  },
})

const EXPOSURES = ['thermal', 'pollution', 'housing']
const nf = (v) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB').format(v)

// --- Data -------------------------------------------------------------
const record = ref(null)
const index = ref(null)
const loading = ref(false)
const notFound = ref('')
const label = ref('')

async function load(code) {
  if (!code) {
    record.value = null
    return
  }
  loading.value = true
  notFound.value = ''
  const [r, i, c] = await Promise.all([loadNeighbourhood(code), loadIndex().catch(() => null), loadCommune(String(code).slice(0, 5))])
  communeIris.value = c?.iris ?? []
  loading.value = false
  record.value = r
  index.value = i
  if (r) rememberNeighbourhood(r.code)
  else notFound.value = t('nbhd.unknownCode')
}
onMounted(() => {
  label.value = (typeof history !== 'undefined' && history.state?.label) || ''
  load(route.params.code)
})
watch(
  () => route.params.code,
  (code) => load(code)
)

// A new address in the sticky bar: find its neighbourhood, then go there.
const searching = ref(false)
async function onAddress(a) {
  searching.value = true
  const r = await findNeighbourhood(a)
  searching.value = false
  if (!r) {
    notFound.value = t('nbhd.outside')
    return
  }
  label.value = a.label
  router.push({ name: localizedRouteName('neighbourhood', locale.value), params: { code: r.code }, query: route.query, state: { label: a.label } })
}

// --- Mode and comparison (in the URL: no personal data) -----------------
const mode = computed({
  get: () => (MODES.includes(route.query.mode) ? route.query.mode : null),
  set: (v) => {
    const { mode: _m, compare: _c, ...rest } = route.query
    router.replace({ query: v ? { ...rest, mode: v } : rest, state: { label: label.value } })
  },
})
const compare = computed({
  get: () => (mode.value && MODES.includes(route.query.compare) && route.query.compare !== mode.value ? route.query.compare : null),
  set: (v) => {
    const { compare: _c, ...rest } = route.query
    router.replace({ query: v ? { ...rest, compare: v } : rest, state: { label: label.value } })
  },
})

// --- Title and pills ------------------------------------------------------
const worst = computed(() => {
  if (!record.value) return []
  return EXPOSURES.filter((k) => record.value.exposures[k].quarter === 4)
})
const careWorst = computed(() => record.value?.exposures.access_care.quarter === 4)
const insufficient = computed(() => (record.value ? EXPOSURES.filter((k) => record.value.exposures[k].status === 'insufficient_data') : []))
const title = computed(() => {
  if (!record.value) return ''
  const n = worst.value.length
  const care = careWorst.value ? 'Care' : ''
  if (n === 0) return t(`nbhd.title.none${care}`)
  if (n === 1) return t(`nbhd.title.one.${worst.value[0]}${care}`)
  if (n === 2) return t(`nbhd.title.two${care}`, { what: worst.value.map((k) => t(`nbhd.title.short.${k}`)).join(t('nbhd.title.and')) })
  return t(`nbhd.title.three${care}`)
})
const pills = computed(() => [...worst.value, ...(careWorst.value ? ['access_care'] : [])])

// --- Part 1 and the care card ---------------------------------------------
function rankCard(k) {
  const e = record.value.exposures[k]
  const ok = e.status !== 'insufficient_data' && e.rank !== null
  const n = ok ? Math.min(10, Math.max(0, Math.round(e.rank * 10))) : null
  return {
    key: k,
    title: t(`nbhd.exposure.${k}.title`),
    subtitle: t(`nbhd.exposure.${k}.subtitle`),
    share: ok ? e.rank : null,
    inWorstQuarter: e.quarter === 4,
    sentence: ok ? t(k === 'access_care' ? 'nbhd.rank.care' : 'nbhd.rank.exposure', { n }, n) : '',
    nearby: ok ? nearby(k) : null,
  }
}

// "Sur 10 quartiers, N…": which ones? The inhabited neighbourhoods of the
// same commune (Paris: arrondissement) that are better placed, up to three
// named, the most favourable first.
const communeIris = ref([])
function nearby(k) {
  const mine = record.value.exposures[k].rank
  const others = communeIris.value.filter((r) => r.code !== record.value.code && r.inhabited && r.exposures[k].rank !== null)
  const better = others.filter((r) => r.exposures[k].rank < mine).sort((a, b) => a.exposures[k].rank - b.exposures[k].rank)
  return { count: better.length, total: others.length + 1, names: better.slice(0, 3).map((r) => r.name) }
}
function nearbyText(card) {
  const nb = card.nearby
  if (!nb || nb.total < 2) return ''
  const key = card.key === 'access_care' ? 'nbhd.nearby.care' : 'nbhd.nearby.exposure'
  const base = t(key, { count: nb.count, total: nb.total, commune: record.value.commune }, nb.count)
  return nb.names.length ? `${base} ${t('nbhd.nearby.names', { names: nb.names.join(', ') })}` : base
}
const cards = computed(() => (record.value ? EXPOSURES.map(rankCard) : []))
const careCard = computed(() => (record.value ? rankCard('access_care') : null))

// --- Part 2: durations ----------------------------------------------------
const PARIS = computed(() => record.value?.code.startsWith('75'))
function minutes(place, m) {
  const r = record.value
  if (!r) return undefined
  if (place.source === 'times') return r.times ? r.times[m]?.[place.id] : undefined
  if (place.source === 'night') return r.night_emergency ? r.night_emergency[m] : undefined
  if (place.source === 'places') return r.places ? r.places[m]?.[place.id] : undefined
  return undefined // "paris": next routing run
}
// undefined = not computed yet; null = more than 90 min.
const computedYet = (place) => minutes(place, 'free') !== undefined
const fmtMin = (v) => (v === null ? t('nbhd.over90') : t('plan.minutes', { n: v }))

function nearest(need) {
  const day = need.places.filter((p) => !p.night && computedYet(p))
  if (!day.length) return null
  const best = (m) => {
    const vals = day.map((p) => minutes(p, m)).filter((v) => v !== null && v !== undefined)
    return vals.length ? Math.min(...vals) : null
  }
  if (mode.value) {
    const v = best(mode.value)
    return v === null ? t('nbhd.over90') : t('plan.minutes', { n: v })
  }
  const all = MODES.map(best).filter((v) => v !== null)
  if (!all.length) return t('nbhd.over90')
  const lo = Math.min(...all)
  const hi = Math.max(...all)
  return lo === hi ? t('plan.minutes', { n: lo }) : t('nbhd.range', { lo, hi })
}
function gap(place) {
  const a = minutes(place, mode.value)
  const b = minutes(place, compare.value)
  if (a === null || b === null || a === undefined || b === undefined) return null
  return b - a
}
const openNeeds = ref({})
// Every need starts closed (decision of 3 October 2026); the visitor opens
// the ones they want, and they stay open when the mode changes.
const needOpen = (need) => openNeeds.value[need.id] ?? false
const columns = computed(() => [0, 1].map((c) => NEEDS.filter((n) => n.column === c)))

// Wheelchair: the nearest accessible stop against the nearest stop.
const station = computed(() => record.value?.station ?? null)

// --- Part 3 ----------------------------------------------------------------
const highlyExposed = computed(() => worst.value.length >= 2)
const part3Key = computed(() => (highlyExposed.value ? (careWorst.value ? 'both' : 'exposedOnly') : careWorst.value ? 'careOnly' : 'neither'))
</script>

<template>
  <div class="nbhd">
    <!-- Sticky bar: address and modes -->
    <div class="sticky-bar">
      <div class="sticky-inner">
        <div class="sticky-address">
          <AddressSearch
            id="nbhd-address"
            compact
            hide-label
            :busy="searching"
            :initial="label"
            :label="t('landing.addressLabel')"
            :placeholder="record ? t('nbhd.fieldPlaceholder', { name: record.name, commune: record.commune }) : t('landing.addressPlaceholder')"
            @select="onAddress"
          />
        </div>
        <div class="sticky-modes">
          <ModeToggle v-model="mode" :label="t('nbhd.modesLabel')" />
        </div>
      </div>
    </div>

    <div class="container nbhd-body">
      <nav class="breadcrumb" :aria-label="t('nbhd.breadcrumb')">
        <router-link :to="{ name: localizedRouteName('home', locale) }">{{ t('nbhd.home') }}</router-link>
        <span aria-hidden="true"> › </span>
        <span>{{ t('site.nav.neighbourhood') }}<template v-if="record"> : {{ record.name }}, {{ record.commune }}</template></span>
      </nav>

      <p v-if="notFound" class="flag" role="status">{{ notFound }}</p>
      <div v-if="loading" class="page-loading"><LoadingDots :label="t('address.loadingPlace')" /></div>

      <template v-if="record">
        <header class="nbhd-head">
          <h1>{{ title }}</h1>
          <div v-if="pills.length" class="pills">
            <span v-for="p in pills" :key="p" class="pill"><span class="pill-dot" aria-hidden="true"></span>{{ t(`nbhd.pill.${p}`) }}</span>
            <span class="pills-note">{{ t('nbhd.pillsNote', { n: nf(index?.n_iris ?? 2752) }) }}</span>
          </div>
          <p v-if="!record.inhabited" class="flag">{{ t('nbhd.fewResidents') }}</p>
          <p v-if="insufficient.length" class="flag">{{ t('nbhd.insufficient', { what: insufficient.map((k) => t(`nbhd.exposure.${k}.title`).toLowerCase()).join(', ') }) }}</p>
          <p class="nbhd-lead">{{ t('nbhd.lead') }}</p>
          <ol class="part-links">
            <li><a href="#cadre"><strong>1</strong> {{ t('nbhd.part1.title') }}</a></li>
            <li><a href="#portee"><strong>2</strong> {{ t('nbhd.part2.title') }}</a></li>
            <li><a href="#deux"><strong>3</strong> {{ t('nbhd.part3.title') }}</a></li>
          </ol>
        </header>

        <!-- 1. Le cadre de vie -->
        <section id="cadre" class="part" aria-labelledby="part1-title">
          <h2 id="part1-title"><span class="part-num n1">1.</span>{{ t('nbhd.part1.title') }}</h2>
          <p class="part-intro">{{ t('nbhd.part1.intro', { n: nf(index?.n_iris ?? 2752) }) }}</p>
          <div class="cards">
            <RankBar
              v-for="c in cards"
              :key="c.key"
              :title="c.title"
              :subtitle="c.subtitle"
              :share="c.share"
              :in-worst-quarter="c.inWorstQuarter"
              :left-label="t('nbhd.rank.left')"
              :right-label="t('nbhd.rank.right')"
              :sentence="c.sentence"
              :missing="t('nbhd.rank.missing')"
              :note="nearbyText(c)"
            />
          </div>
        </section>

        <!-- 2. Ce qui est à portée -->
        <section id="portee" class="part" aria-labelledby="part2-title">
          <div class="part2-head">
            <div>
              <h2 id="part2-title"><span class="part-num n2">2.</span>{{ t('nbhd.part2.title') }}</h2>
              <p class="part-intro">{{ t('nbhd.part2.intro') }}</p>
            </div>
            <div v-if="mode" class="compare">
              <ModeToggle v-model="compare" :exclude="[mode]" :label="t('nbhd.compareLabel')" />
            </div>
          </div>

          <details class="how">
            <summary>{{ t('nbhd.how.title') }}</summary>
            <dl>
              <template v-for="m in MODES" :key="m">
                <dt><span class="dot" :class="`dot-${m}`" aria-hidden="true"></span>{{ t(`modes.${m}`) }}</dt>
                <dd>{{ t(`nbhd.how.${m}`) }}</dd>
              </template>
            </dl>
            <p>
              {{ t('nbhd.how.all') }}
              <router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('nbhd.how.link') }}</router-link>
            </p>
          </details>

          <div v-if="careCard" class="care-card">
            <div class="care-text">
              <h3>{{ careCard.title }}</h3>
              <p>{{ careCard.subtitle }}</p>
            </div>
            <div class="care-bar">
              <div class="rank-bar" aria-hidden="true" v-if="careCard.share !== null">
                <span class="rank-marker" :class="{ worst: careCard.inWorstQuarter }" :style="{ left: `${100 * careCard.share}%` }"></span>
              </div>
              <div class="rank-scale" aria-hidden="true" v-if="careCard.share !== null"><span>{{ t('nbhd.rank.careLeft') }}</span><span>{{ t('nbhd.rank.careRight') }}</span></div>
              <p class="care-sentence">{{ careCard.share !== null ? careCard.sentence : t('nbhd.rank.missing') }}</p>
              <p v-if="nearbyText(careCard)" class="care-nearby">{{ nearbyText(careCard) }}</p>
            </div>
          </div>

          <div v-if="!mode" class="no-mode" role="note">
            <strong>{{ t('nbhd.noMode') }}</strong>
            <span v-for="m in MODES" :key="m" class="legend-item"><span class="dot" :class="`dot-${m}`" aria-hidden="true"></span>{{ t(`modes.${m}`) }}</span>
            <span class="muted">{{ t('nbhd.noModeHint') }}</span>
          </div>
          <div v-else-if="compare" class="no-mode" role="note">
            <span class="legend-item"><span class="dot" :class="`dot-${mode}`" aria-hidden="true"></span><strong>{{ t(`modes.${mode}`) }}</strong></span>
            <span aria-hidden="true">→</span>
            <span class="legend-item"><span class="dot" :class="`dot-${compare}`" aria-hidden="true"></span><strong>{{ t(`modes.${compare}`) }}</strong></span>
            <span class="muted">{{ t('nbhd.gapLegend') }}</span>
          </div>

          <div class="needs">
            <div v-for="(col, ci) in columns" :key="ci" class="needs-col">
              <AccordionItem
                v-for="need in col"
                :key="need.id"
                class="need"
                :open="needOpen(need)"
                @update:open="(v) => (openNeeds[need.id] = v)"
              >
                <template #title>
                  <span class="need-head">
                    <span class="need-ring" :style="{ borderColor: need.color }" aria-hidden="true"></span>
                    <span class="need-text">
                      <span class="need-name">{{ t(`nbhd.need.${need.id}.title`) }}</span>
                      <span class="need-sub">{{ t(`nbhd.need.${need.id}.sub`) }}</span>
                    </span>
                    <span v-if="nearest(need)" class="need-nearest"><span class="nearest-label">{{ t('nbhd.nearest') }}&nbsp;</span><strong>{{ nearest(need) }}</strong></span>
                  </span>
                </template>
                <ul class="places">
                  <li v-for="place in need.places" :key="place.id" class="place" :class="{ 'place-note': place.parisOnly && !PARIS }">
                    <span class="place-name">
                      {{ t(`nbhd.place.${place.id}`) }}
                      <span v-if="!computedYet(place) && !(place.parisOnly && !PARIS)" class="badge">{{ t('nbhd.notYet') }}</span>
                    </span>
                    <span v-if="place.parisOnly && !PARIS" class="paris-only">{{ t('nbhd.parisOnly') }}</span>
                    <span v-else-if="computedYet(place)" class="place-times">
                      <template v-if="!mode">
                        <span v-for="m in MODES" :key="m" class="t-item">
                          <span class="dot" :class="`dot-${m}`" aria-hidden="true"></span>
                          <span class="sr-only">{{ t(`modes.${m}`) }} :</span>
                          {{ fmtMin(minutes(place, m)) }}
                        </span>
                      </template>
                      <template v-else-if="!compare">
                        <strong>{{ fmtMin(minutes(place, mode)) }}</strong>
                      </template>
                      <template v-else>
                        <strong>{{ fmtMin(minutes(place, mode)) }}</strong>
                        <span class="t-item"><span class="dot" :class="`dot-${compare}`" aria-hidden="true"></span><span class="sr-only">{{ t(`modes.${compare}`) }} :</span>{{ fmtMin(minutes(place, compare)) }}</span>
                        <span v-if="gap(place) !== null" class="gap" :class="{ big: Math.abs(gap(place)) >= 3 }">{{ gap(place) === 0 ? t('nbhd.same') : t('nbhd.gap', { n: (gap(place) > 0 ? '+' : '−') + Math.abs(gap(place)) }) }}</span>
                      </template>
                    </span>
                  </li>
                </ul>
              </AccordionItem>
            </div>
          </div>

          <aside v-if="station" class="station-note">
            <span class="dot dot-wheelchair" aria-hidden="true"></span>
            <div>
              <p>
                {{
                  station.wheelchair === station.free
                    ? t('nbhd.stationSame', { wc: fmtMin(station.wheelchair) })
                    : t('nbhd.station', { wc: fmtMin(station.wheelchair), free: fmtMin(station.free) })
                }}
              </p>
              <p class="station-link">
                <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#limites' }">{{ t('nbhd.stationLink') }}</router-link>
              </p>
            </div>
          </aside>
        </section>

        <!-- 3. Les deux à la fois -->
        <section id="deux" class="part part3" aria-labelledby="part3-title">
          <div class="part3-text">
            <h2 id="part3-title"><span class="part-num n3">3.</span>{{ t('nbhd.part3.title') }}</h2>
            <p class="part3-lead">
              {{ t(`nbhd.part3.${part3Key}`) }}
              <template v-if="part3Key === 'both' && index">{{ t('nbhd.part3.count', { n: nf(index.highly_exposed_and_worst_care) }) }}</template>
            </p>
            <p class="part3-def">{{ t('nbhd.part3.definition') }}</p>
            <p class="part3-hyp">
              {{ t('nbhd.part3.hypothesis') }}
              <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#hypotheses' }">{{ t('nbhd.part3.hypothesisLink') }}</router-link>
            </p>
            <!-- Opens the map with the same cases ticked: highly exposed and the
                 most difficult access to care, this neighbourhood selected. -->
            <router-link class="primary-button" :to="{ name: localizedRouteName('map', locale), query: { f: 'exposed,care', q: record.code } }">{{ t('nbhd.part3.map') }}</router-link>
          </div>
          <NeighbourhoodScatter v-if="index" :points="index.points" :current="record.code" />
        </section>
      </template>

      <section v-else-if="!loading && !route.params.code" class="empty">
        <h1>{{ t('site.nav.neighbourhood') }}</h1>
        <p>{{ t('nbhd.empty') }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.sticky-bar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface);
  border-bottom: 1px solid var(--line-soft);
}
.sticky-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px var(--page-gutter);
}
.sticky-address {
  flex: 0 1 420px;
  min-width: 0;
}
.sticky-modes :deep(.mode-label) {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
.nbhd-body {
  padding-top: 32px;
}
.breadcrumb {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.page-loading {
  padding: 32px 0;
  font-size: 17px;
}
.flag {
  margin: 8px 0;
  font-size: 15px;
  color: var(--text-secondary);
}
.nbhd-head h1 {
  margin: 0 0 14px;
  font-size: 40px;
  line-height: 1.12;
  letter-spacing: -0.01em;
  max-width: 900px;
}
.pills {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--accent-tint);
}
.pill-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
}
.pills-note {
  color: var(--text-secondary);
}
.nbhd-lead {
  margin: 16px 0 0;
  font-size: 18px;
  line-height: 1.5;
  color: var(--text-secondary);
  max-width: 760px;
}
.part-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
  font-size: 15px;
}
.part-links a {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  border: 1.5px solid var(--control-border);
  border-radius: 999px;
  text-decoration: none;
}
.part {
  padding-top: 104px;
  scroll-margin-top: 96px;
}
.part h2 {
  margin: 0 0 10px;
  font-size: 30px;
}
.part-num {
  margin-right: 10px;
}
.n1 {
  color: var(--accent);
}
.n2 {
  color: var(--primary);
}
.n3 {
  color: var(--line-purple);
}
.part-intro {
  margin: 0 0 32px;
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 720px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 28px;
}
.part2-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 28px;
}
.part2-head .part-intro {
  margin-bottom: 0;
}
.compare :deep(.mode-label) {
  margin: 0 0 8px;
  font-size: 14px;
}
.compare :deep(.mode-button) {
  font-size: 15px;
}
.how {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 20px 28px;
  margin-bottom: 24px;
}
.how summary {
  cursor: pointer;
  font-weight: 700;
  min-height: 28px;
}
.how dl {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 10px 20px;
  margin: 16px 0 10px;
}
.how dt {
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.how dd {
  margin: 0;
  line-height: 1.55;
  color: var(--text-secondary);
}
.how p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
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
.care-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 24px;
  align-items: center;
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 26px 28px;
  margin-bottom: 28px;
}
.care-text h3 {
  margin: 0 0 6px;
  font-size: 20px;
}
.care-text p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.rank-bar {
  position: relative;
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #f1f1f1 0%, #f1f1f1 75%, #fbd3e7 75%, #fbd3e7 100%);
}
.rank-marker {
  position: absolute;
  top: -4px;
  width: 18px;
  height: 18px;
  margin-left: -9px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid var(--text-primary);
}
.rank-marker.worst {
  background: var(--accent);
  border-color: var(--accent);
}
.rank-scale {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}
.care-sentence {
  margin: 8px 0 0;
  font-weight: 700;
}
.no-mode {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 16px;
  padding: 14px 20px;
  border-radius: 12px;
  background: var(--mode-wheelchair-bg);
  font-size: 14px;
  margin-bottom: 28px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.muted {
  color: var(--text-secondary);
}
.needs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 40px;
  align-items: start;
}
.needs-col {
  display: flex;
  flex-direction: column;
  border-top: 2px solid var(--text-primary);
}
/* Closed needs line up across the two columns: every header has the same
   three lines (name, places, nearest duration) and the same height. */
.needs-col .need :deep(.accordion-button) {
  min-height: 112px;
}
@media (min-width: 761px) {
  .need-head {
    flex-wrap: wrap;
    row-gap: 4px;
  }
  .need-nearest {
    flex-basis: 100%;
    margin-left: 30px;
    margin-top: 2px;
  }
}
.needs-col .need {
  border: none;
  border-bottom: 1px solid var(--line);
  border-radius: 0;
}
.need-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
}
.need-ring {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid;
  flex-shrink: 0;
  margin-top: 3px;
}
.need-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.need-name {
  font-weight: 700;
  font-size: 18px;
}
.need-sub {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
}
.need-nearest {
  font-size: 14px;
  white-space: nowrap;
  color: var(--text-secondary);
}
.need-nearest strong {
  color: var(--text-primary);
  font-size: 16px;
}
.places {
  margin: 0;
  padding: 0;
  list-style: none;
}
.place {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid var(--line-soft);
  font-size: 16px;
}
.place-name {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.badge {
  font-size: 12px;
  color: var(--text-secondary);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 1px 8px;
}
.place-times {
  display: flex;
  align-items: center;
  gap: 12px;
  white-space: nowrap;
}
.t-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 700;
}
.gap {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text-secondary);
}
.gap.big {
  background: var(--accent-tint);
  color: #8e0050;
  font-weight: 700;
}
.paris-only {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.place-note {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}
.care-nearby {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.station-note {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-top: 32px;
  padding: 22px 28px;
  border-radius: var(--radius);
  background: #f2f5f9;
}
.station-link {
  margin-top: 8px !important;
}
.station-note .dot {
  margin-top: 7px;
}
.station-note p {
  margin: 0;
  line-height: 1.6;
}
.part3 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 64px;
  align-items: center;
}
.part3-lead {
  font-size: 18px;
  line-height: 1.55;
  margin: 8px 0 12px;
}
.part3-def,
.part3-hyp {
  font-size: 15px;
  line-height: 1.55;
  color: var(--text-secondary);
  margin: 0 0 12px;
}
.primary-button {
  display: inline-flex;
  align-items: center;
  min-height: 48px;
  padding: 0 22px;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-weight: 700;
  text-decoration: none;
  margin-top: 8px;
}
.primary-button:hover {
  background: #00469a;
  color: #fff;
}
.empty {
  padding: 48px 0;
}

@media (max-width: 1024px) {
  .sticky-inner {
    padding: 12px 32px;
  }
}
@media (max-width: 900px) {
  .cards {
    grid-template-columns: 1fr;
  }
  .needs {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .needs-col + .needs-col {
    border-top: none;
  }
  .care-card,
  .part3 {
    grid-template-columns: 1fr;
  }
  .how dl {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 760px) {
  .sticky-inner {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 10px 16px;
  }
  .sticky-address {
    flex-basis: auto;
  }
  .sticky-modes :deep(.mode-buttons) {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 2px;
  }
  .nbhd-head h1 {
    font-size: 28px;
  }
  .part h2 {
    font-size: 24px;
  }
  .place {
    flex-wrap: wrap;
  }
  /* Phone (VotreQuartierMobileD4): name and duration only; the list of
     places and "le plus proche" stay for screen readers. */
  .need-sub,
  .nearest-label {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }
  .need-name {
    font-size: 17px;
  }
  .needs-col .need :deep(.accordion-button) {
    min-height: 64px;
  }
}
</style>
