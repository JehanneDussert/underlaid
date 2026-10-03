<script setup>
// Home page, redesign "D4" (docs/design/refonte-d4/: 01, 01b, 02, 10):
// title, one address field, an optional travel mode, the network
// illustration with real median durations for the chosen mode, a strip
// with one finding, then a question drawn at random.
// Durations come from public/data/routes_summary.json (script 38), the
// other figures from key_figures.json (script 35) or data/facts.js (dated
// audits) — never typed in the text.
import { computed, onMounted, onServerPrefetch, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddressSearch from '../components/AddressSearch.vue'
import ModeToggle from '../components/ModeToggle.vue'
import NetworkPlan from '../components/NetworkPlan.vue'
import RandomQuestion from '../components/RandomQuestion.vue'
import { useSeoMeta } from '../composables/useSeoMeta'
import { localizedRouteName } from '../router'
import { loadStaticJson } from '../utils/loadStaticJson'
import { findNeighbourhood } from '../utils/neighbourhood'

const { t, locale } = useI18n()
const router = useRouter()

useSeoMeta({
  title: { en: 'One city, unequal living conditions', fr: 'Une même ville, des conditions de vie inégales' },
  description: {
    en: 'Heat, pollution, housing, access to care and services: the situation of your neighbourhood in Paris and its inner suburbs, depending on how you get around.',
    fr: "Chaleur, pollution, logement, accès aux soins et aux services : la situation de votre quartier à Paris et en petite couronne, selon votre façon de vous déplacer.",
  },
})

const figures = ref(null)
const routes = ref(null)
async function loadData() {
  const [f, r] = await Promise.all([loadStaticJson('/data/key_figures.json'), loadStaticJson('/data/routes_summary.json')])
  figures.value = f
  routes.value = r
}
onServerPrefetch(loadData)
onMounted(() => {
  if (!figures.value || !routes.value) loadData()
})

// No mode by default (decision of 3 October 2026).
const mode = ref(null)

// Phone: a compact selector ("Je me déplace : à préciser") that opens the
// three mode buttons; Escape or a choice closes it.
const phoneModesOpen = ref(false)
const phoneModesButton = ref(null)
function pickPhoneMode(value) {
  mode.value = value
  phoneModesOpen.value = false
  phoneModesButton.value?.focus()
}
function onPhoneModesKeydown(event) {
  if (event.key === 'Escape' && phoneModesOpen.value) {
    event.stopPropagation()
    phoneModesOpen.value = false
    phoneModesButton.value?.focus()
  }
}

// An address leads to its neighbourhood's page (/quartier/<code>), with
// the chosen mode; the typed address travels in the history state only,
// never in the URL.
const leaving = ref(false)
const outside = ref('')
async function goToAddress(a) {
  leaving.value = true
  outside.value = ''
  const r = await findNeighbourhood(a)
  if (!r) {
    leaving.value = false
    outside.value = t('nbhd.outside')
    return
  }
  router.push({
    name: localizedRouteName('neighbourhood', locale.value),
    params: { code: r.code },
    query: mode.value ? { mode: mode.value } : {},
    state: { label: a.label },
  })
}

const strip = computed(() => {
  const s = routes.value?.station_median_by_department
  if (!s) return null
  return { wc: s.wheelchair['75'], free: s.free['75'] }
})
</script>

<template>
  <div class="home">
    <div class="first-screen">
    <section class="hero">
      <div class="hero-text">
        <h1 class="hero-title">{{ t('landing.title') }}</h1>
        <p class="hero-lead">{{ t('landing.lead') }}</p>
        <div class="hero-form">
          <AddressSearch id="home-address" :busy="leaving" :label="t('landing.addressLabel')" hide-label :placeholder="t('landing.addressPlaceholder')" @select="goToAddress" />
          <p v-if="outside" class="outside" role="alert">{{ outside }}</p>

          <div class="modes-desktop">
            <ModeToggle v-model="mode" :label="t('landing.modesLabel')" />
          </div>

          <div class="modes-phone" @keydown="onPhoneModesKeydown">
            <button
              ref="phoneModesButton"
              type="button"
              class="phone-modes-button"
              :aria-expanded="phoneModesOpen ? 'true' : 'false'"
              aria-controls="phone-modes"
              @click="phoneModesOpen = !phoneModesOpen"
            >
              {{ t('landing.phoneModes') }}
              <strong>{{ mode ? t(`modes.${mode}`) : t('landing.phoneModesNone') }}</strong>
              <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12"><path d="M2 4.5 6 8.5 10 4.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </button>
            <div v-show="phoneModesOpen" id="phone-modes" class="phone-modes-panel">
              <ModeToggle :model-value="mode" :label="t('landing.modesLabel')" @update:model-value="pickPhoneMode" />
            </div>
          </div>
        </div>
        <p class="hero-hint">
          {{ t('landing.hint') }}
          <router-link :to="{ name: localizedRouteName('methodology', locale) }">{{ t('landing.hintLink') }}</router-link>
        </p>
      </div>

      <div class="hero-plan">
        <div class="phone-plan-head">
          <h2 class="phone-plan-title">{{ t('plan.fromNeighbourhood') }}</h2>
          <router-link class="phone-all" :to="{ name: localizedRouteName('routes', locale) }">{{ t('landing.allPlacesShort') }} <span aria-hidden="true">→</span></router-link>
        </div>
        <NetworkPlan :mode="mode" :medians="routes?.day_metropolis_median" />
        <p v-if="!mode" class="phone-plan-hint">{{ t('landing.phoneHint') }}</p>
        <router-link class="all-places" :to="{ name: localizedRouteName('routes', locale) }">{{ t('landing.allPlaces') }} <span aria-hidden="true">→</span></router-link>
      </div>
    </section>

    <div class="strip">
      <svg class="strip-dot" aria-hidden="true" width="20" height="20" viewBox="0 0 20 20">
        <circle class="strip-pulse" cx="10" cy="10" r="5" />
        <circle cx="10" cy="10" r="5" />
      </svg>
      <p v-if="strip" class="strip-text">
        <i18n-t keypath="landing.strip" tag="span" scope="global">
          <template #wc><strong>{{ t('landing.stripMinutes', { n: strip.wc }) }}</strong></template>
          <template #free><strong>{{ t('landing.stripMinutes', { n: strip.free }) }}</strong></template>
        </i18n-t>
      </p>
      <span class="strip-note">{{ t('landing.planNote') }}</span>
    </div>
    </div>

    <RandomQuestion :figures="figures" :routes="routes" />
  </div>
</template>

<style scoped>
/* The first screen: hero then strip, exactly the height left under the
   header (88 px), whatever the strip's height (it wraps on narrow
   screens). */
.first-screen {
  display: flex;
  flex-direction: column;
  min-height: calc(100svh - 88px);
}
.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 600px) minmax(0, 1fr);
  /* Header (88 px) + hero + strip fill the screen exactly (.first-screen
     below); the hero only grows taller when its text needs it. */
  flex: 1 0 auto;
  min-height: 480px;
  padding: 0 0 0 var(--page-gutter);
  /* The lines of the plan run off the right edge and stop at the strip. */
  overflow: hidden;
}
.hero-text {
  position: relative;
  z-index: 2;
  padding-top: 48px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.hero-title {
  margin: 0;
  font-size: 56px;
  line-height: 1.04;
  letter-spacing: -0.02em;
  animation: rise 700ms ease-out both;
}
.hero-lead {
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  color: var(--text-secondary);
  max-width: 520px;
  animation: rise 700ms 150ms ease-out both;
}
.hero-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 540px;
  animation: rise 700ms 300ms ease-out both;
}
.outside {
  margin: -8px 0 0;
  font-size: 15px;
  color: var(--text-primary);
}
.hero-hint {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-muted);
  max-width: 540px;
}
.hero-hint a {
  color: var(--text-secondary);
}
/* The plan takes the largest size that fits both the width and the
   height of its column (container query units), so the lines never run
   below the screen. Centred in the space right of the text, so that on
   wide screens the blank is shared on both sides. */
.hero-plan {
  position: relative;
  margin-left: -40px;
  container-type: size;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.all-places {
  position: absolute;
  right: var(--page-gutter);
  bottom: 24px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 18px;
  border-radius: 999px;
  border: 2px solid var(--text-primary);
  background: var(--surface);
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 700;
  font-size: 15px;
  animation: rise 600ms 2900ms ease-out both;
}
.modes-phone,
.phone-plan-head,
.phone-plan-hint {
  display: none;
}

.strip {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 60px;
  padding: 12px var(--page-gutter);
  border-top: 1px solid var(--line-soft);
  border-bottom: 1px solid var(--line-soft);
  font-size: 15px;
}
.strip-dot {
  flex-shrink: 0;
  fill: var(--accent);
  overflow: visible;
}
.strip-pulse {
  transform-box: fill-box;
  transform-origin: center;
  animation: strip-pulse 1600ms ease-out 3;
  opacity: 0;
}
.strip-text {
  margin: 0;
  line-height: 1.45;
}
.strip-note {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes strip-pulse {
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  100% {
    transform: scale(2.8);
    opacity: 0;
  }
}

@media (max-width: 1100px) {
  .hero-title {
    font-size: 46px;
  }
}
/* Short screens (laptops of 720-800 px): tighter text so the first
   screen still holds the form and the strip. */
@media (min-width: 901px) and (max-height: 800px) {
  .hero-text {
    padding-top: 24px;
    gap: 20px;
  }
  .hero-title {
    font-size: 46px;
  }
  .hero-form {
    gap: 14px;
  }
}
@media (max-width: 1024px) {
  .hero {
    padding-left: 32px;
  }
  .strip {
    padding-left: 32px;
    padding-right: 32px;
  }
  .all-places {
    right: 32px;
  }
}

/* Phone and narrow tablet (AccueilMobileBD4): one column, compact mode
   selector, vertical line. */
@media (max-width: 900px) {
  .first-screen {
    min-height: 0;
  }
  .hero {
    grid-template-columns: 1fr;
    min-height: 0;
    overflow: visible;
    padding: 24px 16px 0;
  }
  .hero-text {
    padding-top: 0;
    gap: 16px;
  }
  .hero-title {
    font-size: 34px;
    line-height: 1.06;
  }
  .hero-lead {
    font-size: 16px;
    line-height: 1.45;
  }
  .hero-form {
    gap: 16px;
  }
  .hero-hint {
    display: none;
  }
  .modes-desktop {
    display: none;
  }
  .modes-phone {
    display: block;
  }
  .phone-modes-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 48px;
    padding: 0 22px;
    border-radius: 999px;
    border: 2px solid var(--control-border);
    background: var(--surface);
    color: var(--text-primary);
    font: inherit;
    font-size: 17px;
    cursor: pointer;
  }
  .phone-modes-panel {
    margin-top: 12px;
    padding: 16px;
    border: 1.5px solid var(--line);
    border-radius: var(--radius);
  }
  .hero-plan {
    margin: 32px 0 0;
    container-type: normal;
    display: block;
  }
  .phone-plan-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
  }
  .phone-plan-title {
    margin: 0;
    font-size: 17px;
  }
  .phone-all {
    font-weight: 700;
    display: inline-flex;
    gap: 6px;
    align-items: center;
    min-height: 44px;
  }
  .phone-plan-hint {
    display: block;
    margin: 12px 0 0;
    font-size: 14px;
    color: var(--text-muted);
  }
  .all-places {
    display: none;
  }
  .strip {
    margin-top: 32px;
    padding: 16px;
    align-items: flex-start;
    flex-wrap: wrap;
  }
  .strip-dot {
    margin-top: 2px;
  }
  .strip-text {
    flex: 1;
    min-width: 0;
    font-size: 16px;
  }
  .strip-note {
    flex-basis: 100%;
    margin-left: 34px;
  }
}
</style>
