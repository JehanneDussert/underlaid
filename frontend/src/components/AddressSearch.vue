<script setup>
// Address field with suggestions from the national address base (BAN,
// api-adresse.data.gouv.fr). WAI-ARIA combobox pattern: arrow keys move
// through the suggestions, Enter picks, Escape closes; the number of
// suggestions is announced. Emits `select` with { label, lon, lat }.
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
})
const emit = defineEmits(['select'])
const { t } = useI18n()

const GEOCODE_URL = 'https://api-adresse.data.gouv.fr/search/'
const MGP_CENTER = [2.35, 48.86]

const query = ref('')
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
  if (message.value) return message.value
  if (props.busy || searching.value) return ''
  if (!open.value) return ''
  return suggestions.value.length ? t('address.suggestions', { n: suggestions.value.length }) : ''
})

async function fetchSuggestions(q) {
  const request = ++lastRequest
  searching.value = true
  try {
    const url = `${GEOCODE_URL}?q=${encodeURIComponent(q)}&lat=${MGP_CENTER[1]}&lon=${MGP_CENTER[0]}&limit=5`
    const data = await (await fetch(url)).json()
    if (request !== lastRequest) return []
    suggestions.value = data.features ?? []
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

function onInput() {
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
  emit('select', { label: feature.properties.label, lon, lat })
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
  <form class="address-search" role="search" @submit.prevent="submit">
    <label :for="props.id" :class="{ 'sr-only': props.hideLabel }" class="label">{{ props.label }}</label>
    <div class="row">
      <div class="field">
        <input
          :id="props.id"
          v-model="query"
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
      <LoadingDots v-if="searching && !props.busy" class="field-loading" :label="t('address.searching')" :show-label="false" />
      <button type="submit" :aria-disabled="props.busy ? 'true' : undefined">
        <LoadingDots v-if="props.busy" light :label="t('address.loadingPlace')" :show-label="false" />
        <template v-else>{{ t('address.submit') }}</template>
      </button>
    </div>
    <p class="status" aria-live="polite">{{ status }}</p>
    <p v-if="props.busy" class="busy-text" aria-hidden="true">{{ t('address.loadingPlace') }}</p>
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
button {
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
button:hover {
  background: #00469a;
}
button {
  min-width: 72px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.field-loading {
  flex-shrink: 0;
}
.busy-text {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
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
