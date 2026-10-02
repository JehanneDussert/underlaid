// Figures quoted on the site that come from one-off audits rather than
// from the published data (those are in public/data/key_figures.json,
// computed by scripts/35_key_figures.py). Each one is dated and sourced;
// update the date and value together if an audit is re-run.

export const FACTS = {
  // Share of street length with any sidewalk information in OpenStreetMap
  // (tag on the street or a drawn sidewalk alongside), by département.
  // Audit of 1 October 2026 on the Geofabrik Île-de-France extract of
  // 30 September 2026 (SCORING.md, "Why access to services left the score").
  sidewalkInfo: { paris: 96, seineSaintDenis: 26, date: '2026-10-01' },

  // Share of metro stop points (platforms) marked wheelchair-accessible in
  // the Île-de-France Mobilités timetables (GTFS of 1 October 2026,
  // wheelchair_boarding = 1, inherited from the parent station), by
  // département: Paris 3.7% (648 stop points), Seine-Saint-Denis 30.0%
  // (60); Hauts-de-Seine 2.1% (48), Val-de-Marne 22.2% (45). In
  // Seine-Saint-Denis they are the stop points of the recent
  // extensions of lines 11 and 14. Checked on 2 October 2026.
  metroAccessible: { paris: 3.7, hautsDeSeine: 2.1, seineSaintDenis: 30.0, valDeMarne: 22.2, date: '2026-10-01' },

  // Train stations where a wheelchair user can board on their own
  // (accessibility level 6, "véhicule accessible en toute autonomie"),
  // Île-de-France Mobilités dataset "Accessibilité en gare" (Licence
  // Ouverte 2.0, updated 6 July 2026): 14 of 459, all on Transilien
  // line H in Val-d'Oise; 174 on prior booking (Assist'enGare), 58 on
  // request to station staff, 213 not accessible. Checked on 2 October 2026.
  autonomousStations: { autonomous: 14, total: 459, booking: 174, staff: 58, notAccessible: 213, date: '2026-07-06' },

  // Access to care, pre-registered test (step 4 of the access rebuild,
  // 2 October 2026): the gap between the lowest and the highest third of
  // means, at equal population density (density fifths), in points.
  careGapEqualDensity: { hautsDeSeine: 22.6, valDeMarne: 23.1, date: '2026-10-02' },
}
