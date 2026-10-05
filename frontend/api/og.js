// Sharing image of a neighbourhood page, made on request (decision of
// 5 October 2026): 1200 x 630 PNG in the site's identity (the plan's curved
// lines, as on scripts/make-share-images.mjs), with the neighbourhood's name,
// its commune and the pills of the themes where it is in the most affected
// quarter — the same pills as the page. Never an address.
//
//   /api/og?code=930290101&lang=fr
//
// Vercel Edge function; the CDN keeps each image (Cache-Control below).
import { ImageResponse } from '@vercel/og'

export const config = { runtime: 'edge' }

const LABELS = {
  fr: {
    kicker: 'Votre quartier',
    note: 'Dans le quart le plus touché des 2 752 quartiers :',
    none: 'Hors du quart le plus touché pour la chaleur, l’air et le bruit, le logement',
    region: 'Paris et petite couronne',
    pill: { thermal: 'Chaleur', pollution: 'Air et bruit', housing: 'Logements énergivores', access_care: 'Accès aux soins' },
  },
  en: {
    kicker: 'Your neighbourhood',
    note: 'In the most affected quarter of the 2,752 neighbourhoods:',
    none: 'Outside the most affected quarter for heat, air and noise, housing',
    region: 'Paris and its inner suburbs',
    pill: { thermal: 'Heat', pollution: 'Air and noise', housing: 'Energy-inefficient homes', access_care: 'Access to care' },
  },
}
const THEMES = ['thermal', 'pollution', 'housing', 'access_care']

const h = (type, style, children) => ({ type, props: { style, children } })

export default async function handler(request) {
  const url = new URL(request.url)
  const code = (url.searchParams.get('code') || '').replace(/\D/g, '')
  const lang = url.searchParams.get('lang') === 'en' ? 'en' : 'fr'
  const L = LABELS[lang]
  const origin = url.origin
  const [commune, regular, bold] = await Promise.all([
    code.length >= 5 ? fetch(`${origin}/data/quartiers/${code.slice(0, 5)}.json`).then((r) => (r.ok ? r.json() : null)) : null,
    fetch(`${origin}/share/fonts/atkinson-hyperlegible-latin-400-normal.woff`).then((r) => r.arrayBuffer()),
    fetch(`${origin}/share/fonts/atkinson-hyperlegible-latin-700-normal.woff`).then((r) => r.arrayBuffer()),
  ])
  const rec = commune?.iris?.find((r) => r.code === code)
  if (!rec) {
    // Unknown code: the home page's image.
    return Response.redirect(`${origin}/share/accueil-${lang}.png`, 302)
  }
  const pills = THEMES.filter((k) => rec.exposures?.[k]?.quarter === 4)
  const communeName = rec.commune.replace(/ Arrondissement$/, '')
  const pill = (k) =>
    h('div', { display: 'flex', alignItems: 'center', gap: 12, background: '#FCE4F1', borderRadius: 999, padding: '10px 20px', fontSize: 24 }, [
      h('div', { width: 14, height: 14, borderRadius: 7, background: '#E4007C' }),
      L.pill[k],
    ])
  const tree = h('div', { width: 1200, height: 630, display: 'flex', position: 'relative', background: '#fff', color: '#101010', fontFamily: 'Atkinson' }, [
    { type: 'img', props: { src: `${origin}/share/plan-panel.png`, width: 1200, height: 630, style: { position: 'absolute', left: 0, top: 0 } } },
    h('div', { position: 'absolute', left: 72, top: 72, width: 620, display: 'flex', flexDirection: 'column' }, [
      h('div', { fontSize: 24, fontWeight: 700, color: '#3C3C3C', marginBottom: 18 }, L.kicker),
      h('div', { fontSize: 60, fontWeight: 700, lineHeight: 1.05, letterSpacing: '-0.02em', marginBottom: 14 }, rec.name),
      h('div', { fontSize: 30, color: '#3C3C3C', marginBottom: 30 }, communeName),
      ...(pills.length
        ? [
            h('div', { fontSize: 22, color: '#3C3C3C', marginBottom: 14 }, L.note),
            h('div', { display: 'flex', flexWrap: 'wrap', gap: 12 }, pills.map(pill)),
          ]
        : [h('div', { fontSize: 22, color: '#3C3C3C' }, L.none)]),
    ]),
    h('div', { position: 'absolute', left: 72, bottom: 56, display: 'flex', alignItems: 'baseline', gap: 16 }, [
      h('div', { fontSize: 30, fontWeight: 700 }, 'underlaid.fr'),
      h('div', { fontSize: 22, color: '#3C3C3C' }, L.region),
    ]),
  ])
  return new ImageResponse(tree, {
    width: 1200,
    height: 630,
    fonts: [
      { name: 'Atkinson', data: regular, weight: 400, style: 'normal' },
      { name: 'Atkinson', data: bold, weight: 700, style: 'normal' },
    ],
    headers: { 'Cache-Control': 'public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400' },
  })
}
