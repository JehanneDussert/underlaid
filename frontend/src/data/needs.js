// Needs and everyday places of the "Votre quartier" page (redesign D4),
// in the order decided on 3 October 2026. `source` says where the duration
// comes from in the neighbourhood file (scripts/39_neighbourhood_files.py):
// "times" = first routing run (Tuesday 10:00), "places" = second run
// (everyday places, shown "pas encore calculé" until it is published),
// "paris" = Paris only, from the City's open data (toilets and drinking
// water, next routing run). Doctor and pharmacy are for information only
// (decision of 3 October 2026).
export const NEEDS = [
  {
    id: 'care',
    color: '#00A3E0',
    column: 0,
    places: [
      { id: 'gp', source: 'times' },
      { id: 'pharmacy', source: 'times' },
      { id: 'emergency', source: 'times' },
      // Night (1:00), on foot and by public transport; not counted in "le plus
      // proche" (display rule of 3 October 2026: only emergency departments
      // and stations at night).
      { id: 'emergencyNight', source: 'night', night: true },
    ],
  },
  {
    id: 'admin',
    color: '#0057B8',
    column: 0,
    places: [
      { id: 'town_hall', source: 'times' },
      { id: 'france_services', source: 'times' },
      { id: 'caf', source: 'times' },
      { id: 'cpam', source: 'times' },
      { id: 'employment', source: 'times' },
    ],
  },
  { id: 'food', color: '#00A06B', column: 0, places: [{ id: 'food_store', source: 'places' }] },
  {
    id: 'children',
    color: '#FF7A00',
    column: 0,
    places: [
      { id: 'creche', source: 'places' },
      { id: 'nursery_school', source: 'places' },
    ],
  },
  { id: 'post', color: '#8C6E00', column: 1, places: [{ id: 'post_office', source: 'times' }] },
  { id: 'police', color: '#101010', column: 1, places: [{ id: 'police', source: 'places' }] },
  {
    id: 'social',
    color: '#7B3FA0',
    column: 1,
    places: [
      { id: 'social_centre', source: 'places' },
      { id: 'library', source: 'places' },
    ],
  },
  {
    id: 'cool',
    color: '#5BB318',
    column: 1,
    places: [
      { id: 'park', source: 'places' },
      // Drinking water here (decision of 3 October 2026), Paris only.
      { id: 'drinking_water', source: 'paris', parisOnly: true },
    ],
  },
  {
    id: 'toilets',
    color: '#5B6B7A',
    column: 1,
    places: [
      // Wheelchair mode: the nearest toilet marked accessible (toilets_pmr).
      { id: 'toilets', source: 'paris', parisOnly: true, wheelchairId: 'toilets_pmr' },
      { id: 'toilets_24h', source: 'paris', parisOnly: true },
    ],
  },
]
