// Neighbourhood data for the "Votre quartier" page: one small file per
// commune (Paris by arrondissement), built by scripts/39_neighbourhood_files.py.
// An address gives its commune (INSEE code from the address API), so finding
// its neighbourhood loads ~30 kB instead of the whole score (5 MB).
import booleanPointInPolygon from '@turf/boolean-point-in-polygon'
import { ref } from 'vue'
import { loadStaticJson } from './loadStaticJson'

const cache = new Map()

export async function loadCommune(insee) {
  if (!cache.has(insee)) cache.set(insee, loadStaticJson(`/data/quartiers/${insee}.json`).catch(() => null))
  return cache.get(insee)
}

// The neighbourhood of a code ("751114403"): its commune is the first 5
// characters.
export async function loadNeighbourhood(code) {
  const commune = await loadCommune(String(code).slice(0, 5))
  return commune?.iris.find((r) => r.code === code) ?? null
}

let indexPromise = null
export function loadIndex() {
  if (!indexPromise) indexPromise = loadStaticJson('/data/quartiers/index.json')
  return indexPromise
}

// Squared distance from a point to a polygon's vertices: fallback for an
// address that falls just outside every outline of its commune (outlines
// rounded to 6 decimals, addresses on a boundary street).
function nearestVertexDistance(geometry, lon, lat) {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
  let best = Infinity
  for (const poly of polygons) for (const ring of poly) for (const [x, y] of ring) best = Math.min(best, (x - lon) ** 2 + (y - lat) ** 2)
  return best
}

// { lon, lat, citycode } -> neighbourhood record, or null outside the
// metropolis (no file for that commune).
export async function findNeighbourhood({ lon, lat, citycode }) {
  if (!citycode) return null
  const commune = await loadCommune(String(citycode))
  if (!commune) return null
  const inside = commune.iris.find((r) => booleanPointInPolygon([lon, lat], r.geometry))
  if (inside) return inside
  let best = null
  let bestDistance = Infinity
  for (const r of commune.iris) {
    const d = nearestVertexDistance(r.geometry, lon, lat)
    if (d < bestDistance) {
      best = r
      bestDistance = d
    }
  }
  // Within about 200 m of an outline of the address's own commune.
  return bestDistance < 0.002 ** 2 ? best : null
}

// The last neighbourhood seen in this tab, so that "Votre quartier" in the
// menu leads back to it. Kept in sessionStorage (this tab only, cleared
// when it closes): a neighbourhood code, never an address.
const STORAGE_KEY = 'underlaid-neighbourhood'
export const lastNeighbourhood = ref(null)
export function rememberNeighbourhood(code) {
  lastNeighbourhood.value = code
  try {
    sessionStorage.setItem(STORAGE_KEY, code)
  } catch {
    /* storage unavailable: the link simply stays greyed after a reload */
  }
}
export function restoreNeighbourhood() {
  try {
    lastNeighbourhood.value = sessionStorage.getItem(STORAGE_KEY)
  } catch {
    lastNeighbourhood.value = null
  }
}
