<script setup>
// Address field with suggestions from the national address base (BAN,
// api-adresse.data.gouv.fr). WAI-ARIA combobox pattern: arrow keys move
// through the suggestions, Enter picks, Escape closes; the number of
// suggestions is announced. Emits `select` with { label, lon, lat }.
// Used on the home page and on the address page.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  // Visually hide the label (it stays available to screen readers).
  hideLabel: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
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
let debounce = null
let lastRequest = 0

const listId = computed(() => `${props.id}-list`)
const optionId = (i) => `${props.id}-opt-${i}`
const status = computed(() => {
  if (message.value) return message.value
  if (!open.value) return ''
  return suggestions.value.length ? t('address.suggestions', { n: suggestions.value.length }) : ''
})

async function fetchSuggestions(q) {
  const request = ++lastRequest
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
      <button type="submit">{{ t('address.submit') }}</button>
    </div>
    <p class="status" aria-live="polite">{{ status }}</p>
  </form>
</template>

<style scoped>
.address-search {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 640px;
}
.label {
  font-size: 15px;
  font-weight: 600;
}
.row {
  display: flex;
  gap: 8px;
}
.field {
  position: relative;
  flex: 1;
  min-width: 0;
}
input {
  width: 100%;
  height: 56px;
  padding: 0 18px;
  font: inherit;
  font-size: 17px;
  border: 1.5px solid var(--dark);
  border-radius: var(--radius-small);
  background: var(--surface);
  color: var(--text-primary);
}
input::placeholder {
  color: var(--text-secondary);
}
button {
  height: 56px;
  padding: 0 24px;
  border: none;
  border-radius: var(--radius-small);
  background: var(--dark);
  color: var(--text-on-dark);
  font: inherit;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
}
.suggestions {
  position: absolute;
  z-index: 20;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: var(--surface);
  border: 1.5px solid var(--dark);
  border-radius: var(--radius-small);
  box-shadow: 0 8px 24px rgba(20, 22, 26, 0.12);
}
.suggestions li {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
}
.suggestions li.active,
.suggestions li:hover {
  background: var(--surface-muted);
}
.status {
  margin: 0;
  min-height: 1em;
  font-size: 14px;
  color: var(--text-secondary);
}
@media (max-width: 480px) {
  .row {
    flex-direction: column;
  }
}
</style>
