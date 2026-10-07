<script setup>
// "Hypothèses et résultats" (method page, docs/design/refonte-d4/,
// MethodeD4 part 7): each pre-registered hypothesis with its verdict in
// words, what the result shows, and the date it was written. Texts
// validated by the project owner on 3 October 2026; no explanation of a
// result is presented as established.
import { useI18n } from 'vue-i18n'
import { HYPOTHESES } from '../data/hypotheses'

defineProps({
  // Heading level of each hypothesis, to fit the page outline.
  level: { type: Number, default: 3 },
})
const { t, te, locale } = useI18n()
// Column labels of a hypothesis table: its own if given, else residents' resources.
const col = (h, key) => (te(`hypotheses.${h.id}.${key}`) ? t(`hypotheses.${h.id}.${key}`) : t(`hypotheses.${key}`))

// French writes the first day of a month "1er".
const date = (iso) => {
  const text = new Intl.DateTimeFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(iso))
  return locale.value === 'fr' ? text.replace(/^1 /, '1er ') : text
}
function controlText(h) {
  const c = h.control2022
  if (c.table) return t(`hypotheses.${h.id}.control`, Object.fromEntries(c.table.flatMap((r) => [[`l${r.dep}`, pct(r.lowest)], [`h${r.dep}`, pct(r.highest)]])))
  const f = c.figures
  const args = {}
  for (const [k, v] of Object.entries(f)) {
    if (Array.isArray(v)) {
      args[`${k}l`] = pct(v[0])
      args[`${k}h`] = pct(v[1])
    } else args[k] = new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: 1 }).format(v)
  }
  return t(`hypotheses.${h.id}.control`, args)
}
// Pre-registered hypotheses, then the additional test (households without a
// car): its rule was only in unversioned notes before the calculation, so it
// cannot be shown as verifiably pre-registered (decision of 7 October 2026).
const groups = [
  { id: 'pre', items: HYPOTHESES.filter((h) => !h.additional) },
  { id: 'additional', title: 'hypotheses.additionalTitle', intro: 'hypotheses.additionalIntro', items: HYPOTHESES.filter((h) => h.additional) },
].filter((g) => g.items.length)
const pct = (v) => new Intl.NumberFormat(locale.value === 'fr' ? 'fr-FR' : 'en-GB', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(v / 100)
</script>

<template>
  <div class="hypotheses">
    <p class="hypotheses-intro">{{ t('hypotheses.intro') }}</p>
    <template v-for="g in groups" :key="g.id">
      <component :is="`h${level}`" v-if="g.title" class="hypotheses-group-title">{{ t(g.title) }}</component>
      <p v-if="g.intro" class="hypotheses-intro">{{ t(g.intro) }}</p>
      <ul class="hypotheses-list" role="list">
        <li v-for="h in g.items" :key="h.id" class="hypothesis" :class="`verdict-${h.verdict}`">
          <span class="verdict-tag">{{ t(`hypotheses.verdict.${h.verdict}`) }}</span>
          <component :is="`h${g.title ? level + 1 : level}`" class="hypothesis-statement">{{ t(`hypotheses.${h.id}.statement`) }}</component>
          <p class="hypothesis-result">{{ t(`hypotheses.${h.id}.result`) }}</p>
          <table v-if="h.table" class="hypothesis-table">
            <caption>{{ t(`hypotheses.${h.id}.tableCaption`) }}</caption>
            <thead>
              <tr>
                <th scope="col">{{ t('hypotheses.department') }}</th>
                <th scope="col">{{ col(h, 'lowestThird') }}</th>
                <th scope="col">{{ col(h, 'highestThird') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in h.table" :key="row.dep">
                <th scope="row">{{ t(`hypotheses.dep.${row.dep}`) }}</th>
                <td>{{ pct(row.lowest) }}</td>
                <td>{{ pct(row.highest) }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="h.table" class="hypothesis-result">{{ t(`hypotheses.${h.id}.after`) }}</p>
          <p v-if="h.table" class="hypothesis-caveat">{{ t(`hypotheses.${h.id}.caveat`) }}</p>
          <p v-if="h.control2022" class="hypothesis-control">
            <strong>{{ t('hypotheses.control.label') }} {{ t(h.control2022.confirmed ? 'hypotheses.control.confirmed' : 'hypotheses.control.notConfirmed') }}.</strong>
            {{ controlText(h) }}
          </p>
          <p v-if="h.control2" class="hypothesis-control">
            <strong>{{ t('hypotheses.control2.label') }} {{ t('hypotheses.control.confirmed') }}.</strong>
            {{ t(`hypotheses.${h.id}.control2`) }}
          </p>
          <p v-if="h.note" class="hypothesis-caveat">{{ t(`hypotheses.${h.id}.note`) }}</p>
          <p v-if="!h.additional" class="hypothesis-date">{{ t('hypotheses.written', { date: date(h.written) }) }}</p>
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.hypotheses-intro {
  margin: 0 0 24px;
  font-size: 17px;
  line-height: 1.6;
  max-width: 720px;
}
.hypotheses-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.hypothesis {
  border: 1.5px solid var(--line);
  border-radius: var(--radius);
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.verdict-tag {
  align-self: flex-start;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
  border: 1.5px solid var(--text-primary);
}
.verdict-supported .verdict-tag {
  background: var(--mode-free-bg);
}
.verdict-refuted .verdict-tag,
.verdict-reversed .verdict-tag {
  background: var(--accent-tint);
}
.hypothesis-statement {
  margin: 0;
  font-size: 19px;
  line-height: 1.4;
}
.hypothesis-result {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-secondary);
}
.hypothesis-caveat {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
  border-left: 3px solid var(--line-strong);
  padding-left: 12px;
}
.hypotheses-group-title {
  margin: 28px 0 0;
}
.hypothesis-control {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--surface-muted);
}
.hypothesis-date {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
.hypothesis-table {
  border-collapse: collapse;
  font-size: 15px;
  width: 100%;
  max-width: 560px;
}
.hypothesis-table caption {
  text-align: left;
  font-size: 14px;
  color: var(--text-secondary);
  padding-bottom: 8px;
}
.hypothesis-table th,
.hypothesis-table td {
  padding: 8px 12px 8px 0;
  overflow-wrap: anywhere;
  border-bottom: 1px solid var(--line);
  text-align: left;
}
.hypothesis-table td {
  font-variant-numeric: tabular-nums;
}
@media (max-width: 600px) {
  .hypothesis {
    padding: 18px 16px;
  }
  .hypothesis-table {
    font-size: 14px;
  }
}
</style>
