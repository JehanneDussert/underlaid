// All on-screen texts of the launch video. A new language only needs a new
// entry here (and a composition in Root.tsx); numbers and names come from
// src/data/pair.json. French: validated by the project lead on 2026-10-07.
// English: draft translation, to be reviewed before any render.

export type Texts = {
  locale: string
  act1Title: string
  act1Text: string
  themes: { thermal: string; pollution: string; housing: string }
  barsLegend: string
  outOf10: (n: number) => string
  act2Title: string
  act2Text: (x: number, y: number) => string
  free: string
  wheelchair: string
  minutes: (n: number) => string
  act3Title: string
  act3Text: string
  act3Cta: string
  sources: string
}

export const TEXTS: Record<'fr' | 'en', Texts> = {
  fr: {
    locale: 'fr-FR',
    act1Title: 'Inégalités environnementales',
    act1Text: 'À quelques rues d’écart, la chaleur, l’air, le bruit et la performance énergétique des logements ne sont pas les mêmes.',
    themes: { thermal: 'Chaleur', pollution: 'Air et bruit', housing: 'Logements énergivores' },
    barsLegend: 'Sur 10 quartiers, combien sont moins exposés',
    outOf10: (n) => `${n} sur 10`,
    act2Title: 'Inégalités d’accès',
    act2Text: (x, y) => `Pour rejoindre la station la plus proche : ${x} minutes sans contrainte, ${y} minutes en fauteuil roulant.`,
    free: 'sans contrainte',
    wheelchair: 'en fauteuil roulant',
    minutes: (n) => `${n} min`,
    act3Title: 'Underlaid',
    act3Text: 'Les données publiques des 2 752 quartiers de Paris et de la petite couronne, réunies sur une carte.',
    act3Cta: 'Entrez votre adresse : underlaid.fr',
    sources:
      'Quartiers Insee d’environ 2 000 habitants. Données : Insee, CSTB, L’Institut Paris Region, Airparif et Bruitparif, ADEME, Enedis. Trajets à pied : © les contributeurs d’OpenStreetMap. Stations : contient des informations d’Île-de-France Mobilités, disponibles sous la Licence Mobilités.',
  },
  en: {
    locale: 'en-GB',
    act1Title: 'Environmental inequalities',
    act1Text: 'A few streets apart, heat, air, noise and the energy performance of housing are not the same.',
    themes: { thermal: 'Heat', pollution: 'Air and noise', housing: 'Energy-inefficient housing' },
    barsLegend: 'Out of 10 neighbourhoods, how many are less exposed',
    outOf10: (n) => `${n} out of 10`,
    act2Title: 'Inequalities of access',
    act2Text: (x, y) => `To reach the nearest station: ${x} minutes without constraint, ${y} minutes in a wheelchair.`,
    free: 'without constraint',
    wheelchair: 'in a wheelchair',
    minutes: (n) => `${n} min`,
    act3Title: 'Underlaid',
    act3Text: 'The public data of the 2,752 neighbourhoods of Paris and its inner suburbs, brought together on one map.',
    act3Cta: 'Enter your address: underlaid.fr/en',
    sources:
      'INSEE areas of about 2,000 residents. Data: INSEE, CSTB, L’Institut Paris Region, Airparif and Bruitparif, ADEME, Enedis. Walking routes: © OpenStreetMap contributors. Stations: contains information from Île-de-France Mobilités, available under the Licence Mobilités.',
  },
}
