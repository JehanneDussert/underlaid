<script setup>
// Address field with suggestions from the national address base (BAN,
// api-adresse.data.gouv.fr). WAI-ARIA combobox pattern: arrow keys move
// through the suggestions, Enter picks, Escape closes; the number of
// suggestions is announced. Emits `select` with { label, lon, lat }.
// Only addresses of Paris and the inner suburbs (departments 75, 92, 93,
// 94) are proposed; when every match is elsewhere, a message says so.
// Used on the home page and on the address page.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import LoadingDots from './LoadingDots.vue'

const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  // Visually hide the label (it stays available to screen readers).
  hideLabel: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
  // Set by the page while it loads what the chosen address leads to.
  busy: { type: Boolean, default: false },
  // Text shown in the field at first (e.g. the address that led here).
  initial: { type: String, default: '' },
  // Compact pill with a location mark and a clear button (sticky bar of
  // the neighbourhood page).
  compact: { type: Boolean, default: false },
})
const emit = defineEmits(['select'])
const { t } = useI18n()

const GEOCODE_URL = 'https://api-adresse.data.gouv.fr/search/'
const MGP_CENTER = [2.35, 48.86]
const DEPARTMENTS = ['75', '92', '93', '94']
const inZone = (feature) => DEPARTMENTS.includes(String(feature.properties?.citycode ?? '').slice(0, 2))

const query = ref(props.initial)
const input = ref(null)
function clear() {
  query.value = ''
  suggestions.value = []
  open.value = false
  input.value?.focus()
}
const suggestions = ref([])
const active = ref(-1)
const open = ref(false)
const message = ref('')
// Waiting for the address API (suggestions), shown in the field.
const searching = ref(false)
let debounce = null
let lastRequest = 0

const listId = computed(() => `${props.id}-list`)
const optionId = (i) => `${props.id}-opt-${i}`
const status = computed(() => {
  // Announced through the live status line below (the dots are visual).
  if (props.busy) return t('address.loadingPlace')
  if (message.value) return message.value
  if (searching.value) return t('address.searching')
  if (!open.value) return ''
  return suggestions.value.length ? t('address.suggestions', { n: suggestions.value.length }, suggestions.value.length) : ''
})

async function fetchSuggestions(q) {
  const request = ++lastRequest
  searching.value = true
  try {
    // More results than shown, so that addresses of the zone are not
    // crowded out by homonyms elsewhere in France.
    const url = `${GEOCODE_URL}?q=${encodeURIComponent(q)}&lat=${MGP_CENTER[1]}&lon=${MGP_CENTER[0]}&limit=20`
    // Never wait forever on the address service (the field would stay on
    // "Recherche en cours…").
    const data = await (await fetch(url, { signal: AbortSignal.timeout(8000) })).json()
    if (request !== lastRequest) return []
    const all = data.features ?? []
    suggestions.value = all.filter(inZone).slice(0, 5)
    message.value = all.length && !suggestions.value.length ? t('address.outsideZone') : ''
    open.value = suggestions.value.length > 0
    active.value = -1
    return suggestions.value
  } catch {
    message.value = t('address.unavailable')
    suggestions.value = []
    open.value = false
    return []
  } finally {
    if (request === lastRequest) searching.value = false
  }
}

// Read the field on every input event, not through v-model: v-model waits
// for the end of a keyboard "composition", and phone keyboards (Android,
// iOS predictive text) compose a whole word until the space bar, so the
// search used to start only after a space.
function onInput(event) {
  if (event?.target) query.value = event.target.value
  message.value = ''
  clearTimeout(debounce)
  const q = query.value.trim()
  if (q.length < 3) {
    suggestions.value = []
    open.value = false
    return
  }
  debounce = setTimeout(() => fetchSuggestions(q), 250)
}

function pick(feature) {
  const [lon, lat] = feature.geometry.coordinates
  query.value = feature.properties.label
  open.value = false
  suggestions.value = []
  emit('select', { label: feature.properties.label, lon, lat, citycode: feature.properties.citycode })
}

function onKeydown(event) {
  if (event.key === 'ArrowDown' && suggestions.value.length) {
    event.preventDefault()
    open.value = true
    active.value = (active.value + 1) % suggestions.value.length
  } else if (event.key === 'ArrowUp' && suggestions.value.length) {
    event.preventDefault()
    open.value = true
    active.value = active.value <= 0 ? suggestions.value.length - 1 : active.value - 1
  } else if (event.key === 'Escape') {
    open.value = false
    active.value = -1
  }
}

// The button (or Enter without a highlighted suggestion) takes the
// highlighted suggestion, else the first one, fetching it if needed.
async function submit() {
  if (props.busy) return
  if (open.value && active.value >= 0) return pick(suggestions.value[active.value])
  const q = query.value.trim()
  if (q.length < 3) {
    message.value = t('address.tooShort')
    return
  }
  const list = suggestions.value.length ? suggestions.value : await fetchSuggestions(q)
  if (list.length) pick(list[0])
  else if (!message.value) message.value = t('address.notFound')
}
</script>

<template>
  <form class="address-search" :class="{ compact: props.compact }" role="search" :aria-busy="props.busy || searching ? 'true' : 'false'" @submit.prevent="submit">
    <label :for="props.id" :class="{ 'sr-only': props.hideLabel }" class="label">{{ props.label }}</label>
    <div class="row">
      <svg v-if="props.compact" class="here-mark" aria-hidden="true" width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7" fill="#fff" stroke="currentColor" stroke-width="2.4" /><circle cx="9" cy="9" r="3" fill="currentColor" /></svg>
      <div class="field">
        <input
          ref="input"
          :id="props.id"
          :value="query"
          type="text"
          role="combobox"
          autocomplete="off"
          aria-autocomplete="list"
          :aria-expanded="open ? 'true' : 'false'"
          :aria-controls="listId"
          :aria-activedescendant="open && active >= 0 ? optionId(active) : undefined"
          :placeholder="props.placeholder"
          @input="onInput"
          @keydown="onKeydown"
          @blur="open = false"
        />
        <ul v-show="open" :id="listId" role="listbox" class="suggestions" :aria-label="t('address.listLabel')">
          <li
            v-for="(s, i) in suggestions"
            :id="optionId(i)"
            :key="s.properties.id"
            role="option"
            :aria-selected="i === active ? 'true' : 'false'"
            :class="{ active: i === active }"
            @mousedown.prevent="pick(s)"
          >{{ s.properties.label }}</li>
        </ul>
      </div>
      <button v-if="props.compact && query" type="button" class="clear" :aria-label="t('address.clear')" @click="clear">
        <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12"><path d="M1.5 1.5l9 9M10.5 1.5l-9 9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" /></svg>
      </button>
      <LoadingDots v-if="searching && !props.busy" class="field-loading" :label="t('address.searching')" :show-label="false" />
      <button type="submit" class="submit" :class="{ 'sr-only-submit': props.compact }" :aria-disabled="props.busy ? 'true' : undefined">
        <template v-if="props.busy">
          <LoadingDots light :label="t('address.loadingPlace')" :show-label="false" />
          <!-- The button keeps an accessible name while it shows the dots. -->
          <span class="sr-only">{{ t('address.loadingPlace') }}</span>
        </template>
        <template v-else>{{ t('address.submit') }}</template>
      </button>
    </div>
    <p class="status" aria-live="polite">{{ status }}</p>
  </form>
</template>

<style scoped>
/* Pill field of the redesign (IdentiteD4): the input and the blue "Voir"
   button inside one 2 px black outline; the focus ring goes around the
   whole pill. */
.address-search {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 640px;
}
.label {
  font-size: 15px;
  font-weight: 700;
}
.row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 60px;
  padding: 0 8px 0 22px;
  border: 2px solid var(--text-primary);
  border-radius: 999px;
  background: var(--surface);
}
.row:focus-within {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}
.field {
  flex: 1;
  min-width: 0;
}
input {
  width: 100%;
  height: 44px;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 18px;
  color: var(--text-primary);
}
input:focus,
input:focus-visible {
  outline: none;
}
input::placeholder {
  color: var(--text-muted);
}
.submit {
  flex-shrink: 0;
  height: 44px;
  padding: 0 20px;
  border: none;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font: inherit;
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
}
.submit:hover {
  background: #00469a;
}
.submit {
  min-width: 72px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.field-loading {
  flex-shrink: 0;
}
.suggestions {
  position: absolute;
  z-index: 30;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: var(--surface);
  border: 2px solid var(--text-primary);
  border-radius: 18px;
  box-shadow: 0 8px 24px rgba(16, 16, 16, 0.12);
}
.suggestions li {
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 16px;
}
.suggestions li.active,
.suggestions li:hover {
  background: var(--mode-wheelchair-bg);
}
.status {
  margin: 0;
  min-height: 1em;
  font-size: 14px;
  color: var(--text-secondary);
}
/* Compact variant (sticky bar): 48 px, location mark, clear button; the
   submit button is kept for keyboard users but visually hidden (Enter
   submits; the suggestions do the rest). */
.compact .row {
  height: 48px;
  padding: 0 6px 0 14px;
  gap: 10px;
}
.compact input {
  font-size: 16px;
}
.here-mark {
  flex-shrink: 0;
  color: var(--text-primary);
}
.clear {
  width: 34px;
  min-width: 34px;
  height: 34px;
  padding: 0;
  border-radius: 50%;
  border: 1.5px solid var(--control-border);
  background: var(--surface);
  color: var(--text-primary);
}
.clear:hover {
  background: var(--surface-muted);
}
.sr-only-submit {
  position: absolute;
  width: 1px;
  height: 1px;
  min-width: 0;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}
.compact .status:empty {
  display: none;
}
@media (max-width: 600px) {
  .row {
    height: 56px;
    padding-left: 18px;
  }
  input {
    font-size: 17px;
  }
}
</style>
