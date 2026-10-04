<script setup>
// "Tous les lieux du quotidien" (target of the home page's button; no
// mock-up): for every need and place of the neighbourhood page, the median
// over the metropolis's neighbourhoods of the duration to the nearest place,
// for the three modes (routes_summary.json, script 38). An address leads to
// the neighbourhood page. Toilets and fountains: Paris neighbourhoods only.
import { computed, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddressSearch from '../components/AddressSearch.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { MODES } from '../data/modes'
import { NEEDS } from '../data/needs'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'
import { findNeighbourhood } from '../utils/neighbourhood'

const { t, locale } = useI18n()
const router = useRouter()

useSeoMeta({
  title: { en: 'All everyday places', fr: 'Tous les lieux du quotidien' },
  description: {
    en: 'How long it takes, as a median across the neighbourhoods of Paris and its inner suburbs, to reach the nearest doctor, town hall, crèche or park, on foot and by public transport, for three ways of getting around.',
    fr: "Combien de temps faut-il, en médiane des quartiers de Paris et de la petite couronne, pour rejoindre le médecin, la mairie, la crèche ou le parc le plus proche, à pied et en transports en commun, selon trois façons de se déplacer.",
  },
})

const summary = ref(null)
async function load() {
  summary.value = await loadStaticJson('/data/routes_summary.json')
}
onServerPrefetch(load)
onMounted(() => {
  if (!summary.value) load()
})

function value(place, mode) {
  const s = summary.value
  if (!s) return undefined
  if (place.source === 'paris') {
    if (!s.paris_median) return undefined
    const id = mode === 'wheelchair' && place.wheelchairId ? place.wheelchairId : place.id
    return s.paris_median[mode]?.[id]
  }
  return s.day_metropolis_median[mode]?.[place.id]
}
const fmt = (v) => (v === undefined ? t('nbhd.notYet') : v === null ? t('nbhd.over90') : t('plan.minutes', { n: v }))
const needs = computed(() => NEEDS.map((n) => ({ ...n, places: n.places.filter((p) => !p.night) })))

const outside = ref('')
const leaving = ref(false)
async function goTo(a) {
  leaving.value = true
  const r = await findNeighbourhood(a)
  if (!r) {
    leaving.value = false
    outside.value = t('nbhd.outside')
    return
  }
  router.push({ name: localizedRouteName('neighbourhood', locale.value), params: { code: r.code }, state: { label: a.label } })
}
</script>

<template>
  <article class="places-page container">
    <h1>{{ t('places.title') }}</h1>
    <p class="lead">{{ t('places.lead') }}</p>
    <div class="search">
      <AddressSearch id="places-address" :busy="leaving" :label="t('places.addressLabel')" :placeholder="t('landing.addressPlaceholder')" @select="goTo" />
      <p v-if="outside" class="flag" role="alert">{{ outside }}</p>
    </div>

    <section v-for="need in needs" :key="need.id" class="need" :aria-labelledby="`need-${need.id}`">
      <h2 :id="`need-${need.id}`"><span class="ring" :style="{ borderColor: need.color }" aria-hidden="true"></span>{{ t(`nbhd.need.${need.id}.title`) }}</h2>
      <!-- Focusable: a scrollable region must be reachable with the keyboard. -->
      <div class="table-wrap" tabindex="0" role="region" :aria-label="t('site.tableRegion')">
        <table>
          <caption class="sr-only">{{ t('places.caption', { need: t(`nbhd.need.${need.id}.title`) }) }}</caption>
          <thead>
            <tr>
              <th scope="col">{{ t('places.place') }}</th>
              <th v-for="m in MODES" :key="m" scope="col"><span class="dot" :class="`dot-${m}`" aria-hidden="true"></span>{{ t(`modes.${m}`) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="place in need.places" :key="place.id">
              <th scope="row">
                {{ t(`nbhd.place.${place.id}`) }}
                <span v-if="place.parisOnly" class="badge">{{ t('places.parisOnly') }}</span>
              </th>
              <td v-for="m in MODES" :key="m">{{ fmt(value(place, m)) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <p class="note">
      {{ t('places.note') }}
      <router-link :to="{ name: localizedRouteName('methodology', locale), hash: '#portee' }">{{ t('places.method') }}</router-link>
    </p>
  </article>
</template>

<style scoped>
.places-page {
  padding-top: 40px;
}
h1 {
  margin: 0 0 12px;
  font-size: 46px;
  letter-spacing: -0.02em;
}
.lead {
  margin: 0 0 24px;
  font-size: 19px;
  line-height: 1.55;
  color: var(--text-secondary);
  max-width: 820px;
}
.search {
  max-width: 640px;
  margin-bottom: 48px;
}
.need {
  margin-bottom: 40px;
}
.need h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 12px;
  font-size: 22px;
}
.ring {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid;
}
.table-wrap {
  overflow-x: auto;
  max-width: 900px;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 16px;
}
th,
td {
  text-align: left;
  padding: 12px 12px 12px 0;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
td {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
tbody th {
  font-weight: 400;
  white-space: normal;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
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
.badge {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 1px 8px;
}
.note {
  font-size: 15px;
  color: var(--text-secondary);
  max-width: 820px;
  line-height: 1.6;
}
.flag {
  margin: 8px 0 0;
}
@media (max-width: 760px) {
  h1 {
    font-size: 32px;
  }
  th,
  td {
    font-size: 15px;
    padding-right: 8px;
  }
  /* Three mode columns fit a phone screen once their headings wrap. */
  thead th {
    white-space: normal;
    vertical-align: bottom;
  }
  td {
    white-space: normal;
  }
}
</style>
