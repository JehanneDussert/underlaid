<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const DATA_URL = '/data/school_ac_context_arrondissement.geojson'
const TREE_DATA_URL = '/data/tree_age_context_arrondissement.geojson'
const LIGHTING_DATA_URL = '/data/street_lighting_context_arrondissement.geojson'
const RNA_DATA_URL = '/data/associational_density_context_commune.geojson'

const schoolAcRows = ref([])
const loading = ref(true)
const treeRows = ref([])
const treeLoading = ref(true)
const lightingRows = ref([])
const lightingLoading = ref(true)
const rnaRows = ref([])
const rnaLoading = ref(true)

onMounted(async () => {
  const response = await fetch(DATA_URL)
  const geojson = await response.json()
  schoolAcRows.value = geojson.features
    .map((f) => f.properties)
    .filter((p) => p.note)
    .sort((a, b) => a.insee_com.localeCompare(b.insee_com))
  loading.value = false
})

onMounted(async () => {
  const response = await fetch(TREE_DATA_URL)
  const geojson = await response.json()
  treeRows.value = geojson.features
    .map((f) => f.properties)
    .sort((a, b) => a.insee_com.localeCompare(b.insee_com))
  treeLoading.value = false
})

onMounted(async () => {
  const response = await fetch(LIGHTING_DATA_URL)
  const geojson = await response.json()
  lightingRows.value = geojson.features
    .map((f) => f.properties)
    .sort((a, b) => a.insee_com.localeCompare(b.insee_com))
  lightingLoading.value = false
})

onMounted(async () => {
  const response = await fetch(RNA_DATA_URL)
  const geojson = await response.json()
  rnaRows.value = geojson.features
    .map((f) => f.properties)
    .sort((a, b) => b.associations_per_1000_inhabitants - a.associations_per_1000_inhabitants)
  rnaLoading.value = false
})

function numberLocale() {
  return locale.value === 'fr' ? 'fr-FR' : 'en-US'
}
function formatCm(value) {
  return new Intl.NumberFormat(numberLocale(), { maximumFractionDigits: 0 }).format(value)
}
function formatPercent(value) {
  return new Intl.NumberFormat(numberLocale(), { style: 'percent', maximumFractionDigits: 0 }).format(value)
}

// Highlights the two extremes as a concrete, checkable comparison rather
// than just dumping 20 rows and letting the reader spot it themselves.
const treeExtremes = computed(() => {
  if (!treeRows.value.length) return null
  const sorted = [...treeRows.value].sort((a, b) => a.avg_circumference_cm - b.avg_circumference_cm)
  return { lowest: sorted[0], highest: sorted[sorted.length - 1] }
})

function formatDensity(value) {
  return new Intl.NumberFormat(numberLocale(), { maximumFractionDigits: 0 }).format(value)
}

const lightingExtremes = computed(() => {
  if (!lightingRows.value.length) return null
  const sorted = [...lightingRows.value].sort((a, b) => a.lamps_per_km2 - b.lamps_per_km2)
  return { lowest: sorted[0], highest: sorted[sorted.length - 1] }
})

const rnaExtremes = computed(() => {
  if (!rnaRows.value.length) return null
  const sorted = [...rnaRows.value].sort((a, b) => a.associations_per_1000_inhabitants - b.associations_per_1000_inhabitants)
  return { lowest: sorted[0], highest: sorted[sorted.length - 1] }
})

function formatRate(value) {
  return new Intl.NumberFormat(numberLocale(), { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)
}

// The school AC notes are compiled from French-language press sources
// (see scripts/16_school_ac_context.py) — note_fr is the original-ish
// French, note is the English rendering. Everything else in this
// component goes through the i18n JSON like the rest of the app.
function localizedNote(row) {
  return locale.value === 'fr' ? row.note_fr : row.note
}
</script>

<template>
  <div class="context-banner">
    <p class="banner-intro">{{ t('context.intro') }}</p>

    <section>
      <h3>{{ t('context.lifeExpectancyTitle') }}</h3>
      <p>{{ t('context.lifeExpectancyBody') }}</p>
      <p class="source">{{ t('context.lifeExpectancySource') }}</p>
    </section>

    <section>
      <h3>{{ t('context.heatwaveTitle') }}</h3>
      <p>
        <strong>{{ t('context.heatwaveBodyStrong') }}</strong>
        {{ t('context.heatwaveBody') }}
      </p>
      <p class="source">{{ t('context.heatwaveSource') }}</p>
    </section>

    <section>
      <h3>{{ t('context.schoolsTitle') }}</h3>
      <p v-if="loading">{{ t('context.schoolsLoading') }}</p>
      <template v-else>
        <p>{{ t('context.schoolsBody') }}</p>
        <ul class="ac-list">
          <li v-for="row in schoolAcRows" :key="row.insee_com">
            <strong>{{ row.nom_arrondissement }}:</strong> {{ localizedNote(row) }}
          </li>
        </ul>
      </template>
      <p class="source">{{ t('context.schoolsSource') }}</p>
    </section>

    <section>
      <h3>{{ t('context.treesTitle') }}</h3>
      <p v-if="treeLoading">{{ t('context.schoolsLoading') }}</p>
      <template v-else-if="treeExtremes">
        <p>
          {{ t('context.treesBody', {
            lowName: treeExtremes.lowest.nom_arrondissement,
            lowCm: formatCm(treeExtremes.lowest.avg_circumference_cm),
            highName: treeExtremes.highest.nom_arrondissement,
            highCm: formatCm(treeExtremes.highest.avg_circumference_cm),
          }) }}
        </p>
        <ul class="ac-list">
          <li v-for="row in treeRows" :key="row.insee_com">
            <strong>{{ row.nom_arrondissement }}:</strong>
            {{ t('context.treesRow', { cm: formatCm(row.avg_circumference_cm), young: formatPercent(row.pct_young_trees), n: row.tree_count }) }}
          </li>
        </ul>
      </template>
      <p class="source">{{ t('context.treesSource') }}</p>
    </section>

    <section>
      <h3>{{ t('context.lightingTitle') }}</h3>
      <p v-if="lightingLoading">{{ t('context.schoolsLoading') }}</p>
      <template v-else-if="lightingExtremes">
        <p>
          {{ t('context.lightingBody', {
            lowName: lightingExtremes.lowest.nom_arrondissement,
            lowDensity: formatDensity(lightingExtremes.lowest.lamps_per_km2),
            highName: lightingExtremes.highest.nom_arrondissement,
            highDensity: formatDensity(lightingExtremes.highest.lamps_per_km2),
          }) }}
        </p>
        <ul class="ac-list">
          <li v-for="row in lightingRows" :key="row.insee_com">
            <strong>{{ row.nom_arrondissement }}:</strong>
            {{ t('context.lightingRow', { n: formatDensity(row.lamps_per_km2) }) }}
          </li>
        </ul>
      </template>
      <p class="source">{{ t('context.lightingSource') }}</p>
    </section>

    <section>
      <h3>{{ t('context.rnaTitle') }}</h3>
      <p v-if="rnaLoading">{{ t('context.schoolsLoading') }}</p>
      <template v-else-if="rnaExtremes">
        <p>
          {{ t('context.rnaBody', {
            lowName: rnaExtremes.lowest.nom_commune,
            lowRate: formatRate(rnaExtremes.lowest.associations_per_1000_inhabitants),
            highName: rnaExtremes.highest.nom_commune,
            highRate: formatRate(rnaExtremes.highest.associations_per_1000_inhabitants),
          }) }}
        </p>
        <p class="caveat">{{ t('context.rnaCaveat') }}</p>
        <ul class="ac-list ac-list-scroll">
          <li v-for="row in rnaRows" :key="row.insee_com">
            <strong>{{ row.nom_commune }}:</strong>
            {{ t('context.rnaRow', {
              rate: formatRate(row.associations_per_1000_inhabitants),
              n: formatDensity(row.associations_per_km2),
              count: row.active_association_count,
            }) }}
          </li>
        </ul>
      </template>
      <p class="source">{{ t('context.rnaSource') }}</p>
    </section>
  </div>
</template>

<style scoped>
.context-banner {
  max-width: 600px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-size: 13px;
  color: var(--text-primary);
}

.banner-intro {
  color: var(--text-secondary);
  font-size: 12px;
  margin: 0;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--gridline);
}

section h3 {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 8px;
}

section p {
  margin: 0 0 6px;
  line-height: 1.5;
}

.source {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
}

.ac-list {
  margin: 8px 0;
  padding-left: 18px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* RNA now lists ~143 communes (Phase 5) instead of 20 arrondissements —
   too long to show unscrolled inside a modal. */
.ac-list-scroll {
  max-height: 220px;
  overflow-y: auto;
  padding-right: 6px;
}

.caveat {
  font-size: 11.5px;
  font-style: italic;
  color: var(--text-muted);
}
</style>
