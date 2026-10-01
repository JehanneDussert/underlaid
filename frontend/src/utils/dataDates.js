import { loadStaticJson } from './loadStaticJson'

// Per-layer dates written by scripts/run_all.py (last_updated.json
// "layers"). A context layer whose latest refresh failed keeps the date of
// its previous version (failure policy, scripts/pipeline_policy.py); the
// site shows that date next to its figures so mixed vintages are never
// silent.
let pending = null

export function loadDataDates() {
  if (!pending) pending = loadStaticJson('/data/last_updated.json').catch(() => ({}))
  return pending
}

// The oldest date among `layers` if it predates the run itself (by day),
// else null — i.e. null when every listed layer was refreshed by the last run.
export function staleLayerDate(dates, layers) {
  const run = dates?.generated_at
  if (!run || !dates.layers) return null
  const day = (iso) => iso.slice(0, 10)
  const stale = layers
    .map((name) => dates.layers[name])
    .filter((iso) => iso && day(iso) < day(run))
    .sort()
  return stale[0] ?? null
}

export function formatDataDate(iso, locale) {
  return new Intl.DateTimeFormat(locale === 'fr' ? 'fr-FR' : 'en-US', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(iso))
}
