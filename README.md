# Underlaid

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23083312.svg)](https://doi.org/10.5281/zenodo.23083312)

**Une même ville, des conditions de vie inégales.** Underlaid réunit,
pour les 2 752 quartiers de Paris et de la petite couronne (découpage
Insee d'environ 2 000 habitants), ce que les données publiques
présentent d'ordinaire séparément : le **cadre de vie** (chaleur, air et
bruit, logements énergivores, accès aux soins) ; les **lieux à portée**
(services publics, soins, commerces, crèches et écoles, stations), à
pied et en transports en commun, selon trois façons de se déplacer :
sans contrainte, en marchant lentement, en fauteuil roulant ; et les
**ressources des habitants** (revenu, logements surpeuplés, résidences
secondaires), sur un axe séparé, jamais ajouté au cadre de vie. Tout
vient de données publiques ouvertes ; chaque formule est documentée.

**One city, unequal living conditions.** For the 2,752 neighbourhoods of
Paris and its inner suburbs (INSEE areas of about 2,000 residents),
Underlaid brings together what public data usually keeps apart: **living
conditions** (heat, air and noise, energy-inefficient housing, access to
care); **places within reach** (public services, care, shops, nurseries
and schools, stations), on foot and by public transport, for three ways
of getting around: without constraint, walking slowly, in a wheelchair;
and **residents' resources** (income, overcrowded homes, secondary
residences), on a separate axis, never added to living conditions. Built
entirely from public open data; every formula documented.

![Underlaid map: cumulative environmental exposure score across Paris and the inner suburbs](docs/screenshot.png)

**[Open the site](https://underlaid.fr/en)** ·
[Map](https://underlaid.fr/en/map) ·
[Method](https://underlaid.fr/en/method) ·
[Most exposed neighbourhoods](https://underlaid.fr/en/most-exposed-neighbourhoods) ·
[Press](https://underlaid.fr/en/press) ·
[Version française](https://underlaid.fr)

**What it measures / doesn't**
- ✅ **Exposure**: a count (0-4) of categories in their metro-wide worst quartile — never a smoothed average.
- ✅ **Access to care**, measured without a car: GPs and pharmacies reachable on foot and by public transport, shared among everyone who can reach them (E2SFCA). **Inclusive mobility** (what a wheelchair user keeps of that access) is shown for information, not counted.
- ✅ **Means to cope**, on a *separate* axis: median income (INSEE Filosofi 2021), overcrowded homes and secondary residences (2022 census) — crossed with exposure on the map, never added to the score.
- ✅ **Travel times to everyday destinations** (public services, emergency departments, GP, pharmacy, nearest station), on foot and by public transport, for three ways of travelling (no constraint, slow walking, wheelchair) — shown for information, never scored.
- ❌ Not sensitivity (age, health), not what households actually do (air conditioning, time off, car use, online procedures), not flood, soil or industrial risk (yet).
- ❌ Not an accusation: it shows where exposures stack up, not why, and names no one as the cause.

**Key figures** (2,752 IRIS, v0.2; population, overcrowding and
secondary residences from the 2022 census since October 3, 2026 — the
score moves with every pipeline run):

| Score | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| IRIS | 774 (28.1%) | 1,287 (46.8%) | 608 (22.1%) | 79 (2.9%) | 4 (0.1%) |

**What crossing exposure with means shows** (2,529 IRIS with published
income; "highly exposed" = 2 or more of the 3 exposures — heat, air and
noise, housing — in their worst quartile; access to care is a separate
axis and doesn't count here):
- **Not the same exposures.** Highly exposed neighborhoods with the
  *highest* means are mostly in Paris and stack **heat and old,
  energy-inefficient housing**. Those with the *lowest* means are mostly
  in Seine-Saint-Denis and Val-de-Marne and stack mainly **heat, air
  pollution and noise**.
- **Overall, the link between exposure and means is weak** (Spearman
  +0.09 with the score on 4), and slightly positive only because of
  dense, older central Paris; in the three inner-suburb departments
  there's almost no link.
- **Where high exposure and low means meet, it's concentrated**: in
  Seine-Saint-Denis, 61.8% of the highly exposed neighborhoods are in the
  metro area's lowest third of means; in Paris, 4.5% (Hauts-de-Seine
  1.9%, Val-de-Marne 24.5%).

**Four pre-registered tests** (hypotheses written and dated before any
crossing with residents' means or with car ownership; see
[SCORING.md](SCORING.md#working-hypothesis-and-its-test-pre-registered)).
The verdicts were computed with the 2021 census and remain the official
results; each was redone with the 2022 census and **confirmed**. Figures
below are the 2022 ones.
- **Access to care — supported.** Within Hauts-de-Seine and within
  Val-de-Marne, neighborhoods with the fewest means are more often among
  those with the weakest access to care (Hauts-de-Seine 39.3% against
  24.0% for those with the most means; Val-de-Marne 38.8% against 27.9%).
  At equal population density the gap remains: 20.7 points in
  Hauts-de-Seine, 17.3 in Val-de-Marne.
- **Inclusive mobility — refuted.** The inaccessibility of the metro
  weighs mostly on wheelchair trips within Paris, whatever the
  neighborhood's means; in number of GPs reachable, wheelchair access
  remains lower in the inner suburbs.
- **Public services — refuted, and reversed.** With thirds of means
  computed within each département, neighborhoods with the *most* means
  are more often in the quarter farthest from public services (town hall,
  France Services, CAF, CPAM, France Travail, post office) in
  Hauts-de-Seine, Seine-Saint-Denis and Val-de-Marne, and in all four
  départements for step-free travel. This measures travel time on foot
  and by public transport only: it doesn't account for the need to use
  these services, car use or online procedures, and the data don't
  establish why.
- **Households without a car — refuted, and reversed** (rule written on
  3 October 2026, before the site moved to the 2022 census; computed the
  same evening on the 2022 census; the rule was then in unversioned
  working notes, and its first record in the repository is one minute
  later than the calculation). With thirds computed within each
  département, the neighbourhoods with the *most* households without a
  car are clearly *less* often in the quarter farthest from public
  services: Hauts-de-Seine 14.6% against 65.5%, Seine-Saint-Denis 11.4%
  against 66.0%, Val-de-Marne 17.1% against 61.4% (Paris 0.6% against
  9.0%, a small gap). Car ownership depends partly on density and
  income; the test says nothing about the reasons. Confirmed with the
  second travel-time calculation.

---

## About this repository

Interactive map of living conditions per IRIS neighbourhood (heat, air
and noise, energy-inefficient housing, access to care), with the
cumulative count, the places within reach for three ways of getting
around, and a separate axis for residents' resources. Modeled on
EJScreen/CalEnviroScreen/EJNYC.

Covers the full Métropole du Grand Paris "Petite Couronne": Paris (75)
plus Hauts-de-Seine (92), Seine-Saint-Denis (93) and Val-de-Marne (94) —
**2,752 IRIS zones**. Originally shipped as a Paris-intra-muros MVP (992
IRIS); see "Expanding beyond Paris" in [SCORING.md](SCORING.md) for what
changed and why.

## Context

The closest regional precedent: **ORS Île-de-France / Ineris / L'Institut
Paris Region, "Cumuls d'expositions environnementales en Île-de-France"
(2022)** — a 5-year, 500m-grid study of composite environmental exposure
across the whole region, with a public interactive map
([cartoviz.institutparisregion.fr](https://cartoviz.institutparisregion.fr))
and a case study on Aubervilliers, a commune inside Underlaid's own MGP
coverage. Same core idea (composite exposure, not a single blended index);
Underlaid's difference is IRIS-level granularity and a cumulative
worst-quartile count rather than a coarser, non-cumulative grid score.

A comparable tool already exists: **[Adapt'Canicules](https://adaptaville.fr)**
(RésO Villes, 137 agglomerations, focused on QPV priority neighborhoods,
built on 200m gridded data). Underlaid's differentiation: **IRIS-level**
granularity (finer than QPV), an **interactive public-facing** map rather
than an institutional report, and a **cumulative** metric rather than a
smoothed average.

The score is meant to stay **descriptive, never accusatory**: it shows
the correlation between income and exposure without asserting intent
behind it. It's named a **cumulative environmental exposure score**,
not a "vulnerability score" — in climate science, vulnerability is
exposure + sensitivity + adaptive capacity together. The score measures
exposure only; adaptive capacity is measured on its own, separate axis
(the map's "Exposure × means" view) and never folded into it — see
SCORING.md's "What this score doesn't measure" and "Adaptive capacity —
a separate axis".

## Step 1 — Data

Every script in `scripts/` downloads and normalizes one source into
`data/processed/*_iris.geojson`, each carrying a `code_iris` column
(9-digit INSEE IRIS code) as the common join key.

`scripts/01_iris_contours.py` must run first: it produces
`data/processed/iris_mgp.geojson`, the geometric reference every other
script joins against. All scripts have been run end-to-end and validated
against the full Métropole du Grand Paris "Petite Couronne" (2,752 IRIS
zones across Paris + Hauts-de-Seine + Seine-Saint-Denis + Val-de-Marne).

### Sources

| Script | Output | Source |
|---|---|---|
| `01_iris_contours.py` | `iris_mgp.geojson` | data.iledefrance.fr — IGN & INSEE, IRIS 2024 edition, filtered to depts 75/92/93/94 |
| `02_icu_sat4bdnb.py` | `icu_iris.geojson` | data.gouv.fr / CSTB — Sat4BDNB urban heat island indicators |
| `03_cool_spots_facilities.py` | `cool_spots_facilities_iris.geojson` | INSEE BPE (reused from script 06), pools/museums/libraries (F101/F305/F307) — re-sourced from `opendata.paris.fr` in Phase 5 for MGP-wide uniformity |
| `04_cool_spots_green_areas.py` | `cool_spots_green_iris.geojson` | data.iledefrance.fr — open/publicly-accessible green & wooded space, region-wide — re-sourced from `opendata.paris.fr` in Phase 5 |
| `05_air_noise.py` | `air_noise_iris.geojson` | bruitparif.fr — Airparif/Bruitparif air-noise co-exposure map |
| `06_bpe.py` | `bpe_iris.geojson` | INSEE — Base Permanente des Équipements (BPE), health/education/transport domains |
| `07_equipment_access_200m.py` | `equipment_access_iris.geojson` | data.gouv.fr — access time to equipment, 200m grid (unscored context since the v0 launch, like scripts 09, 12, 15) |
| `08_income_filosofi.py` | `income_iris.geojson` | INSEE Filosofi — median disposable income, 2021 |
| `09_social_index_schools.py` | `social_index_iris.geojson` | data.education.gouv.fr — social position index (IPS), primary/middle schools |
| `10_energy_performance.py` | `energy_performance_iris.geojson` | data.ademe.fr — DPE, share of F/G-rated housing |
| `12_accessibility_erp.py` | `accessibility_iris.geojson` | Acceslibre (data.gouv.fr) — PMR accessibility of ERPs |
| `13_street_lighting.py` | `street_lighting_iris.geojson` | opendata.paris.fr — street lighting density (Paris only — no MGP-wide equivalent) |
| `14_qpv_boundaries.py` | `qpv_boundaries_mgp.geojson` | data.iledefrance.fr — QPV priority-neighborhood boundaries, MGP-wide (validation layer, not scored) |
| `15_pedestrian_paths.py` | `pedestrian_paths_iris.geojson` | OpenStreetMap (Overpass API) — footway density. Unscored and no longer shown on the map: OSM sidewalk mapping is too uneven across departments (audit in `scripts/analysis/osm_sidewalk_completeness.py`, [docs/LESSONS.md](docs/LESSONS.md)) |
| `16_school_ac_context.py` | `school_ac_context_arrondissement.geojson` | press/mairie communications, 2026 heatwave — air-conditioned schools (context only, Paris arrondissement grain only, not scored) |
| `17_enedis_thermosensitivity.py` | `enedis_thermosensitivity_iris.geojson` | opendata.enedis.fr — residential electrical thermosensitivity (winter heating load), second housing sub-score indicator alongside DPE |
| `18_tree_age_context.py` | `tree_age_context_arrondissement.geojson` | opendata.paris.fr — average street-tree trunk circumference (age proxy, no planting-date field exists) and young-tree share, Paris arrondissement grain only, context only, not scored |
| `19_street_lighting_context.py` | `street_lighting_context_arrondissement.geojson` | opendata.paris.fr — street lamp density per km² (area-weighted), Paris arrondissement grain only, context only, not scored |
| `20_associational_density_context.py` | `associational_density_context_commune.geojson` | data.iledefrance.fr — active-association density (RNA), per km² and per 1,000 residents, MGP-wide **commune** grain (143 communes, widened from 20 Paris arrondissements in Phase 5), context only, not scored |
| `21_population_iris.py` | `population_iris.geojson` | INSEE Recensement de la population 2022 (`P22_POP`; 2021 until October 3, 2026) — municipal population per IRIS; used to normalize raw counts into per-1,000-resident rates |
| `22_artificialization_mos.py` | `artificialization_iris.geojson` | data.iledefrance.fr — MOS (Mode d'Occupation du Sol) land use, % of IRIS area artificialized/sealed; 4th thermal sub-score indicator, substituted for IGN's OCS GE (no accessible vector API — see SCORING.md) |
| `24_secondary_residences.py` | `secondary_residences_iris.geojson` | INSEE Recensement de la population 2022 ("base infra-communale logement", `P22_RSECOCC / P22_LOG`; 2021 until October 3, 2026) — share of housing units that are secondary residences or occasional dwellings; one of the 3 indicators of the separate adaptive-capacity axis (script 26), never part of the exposure score — see SCORING.md |
| `25_overcrowding.py` | `overcrowding_iris.geojson` | INSEE Recensement 2022 ("base infra-communale logement", same file as script 24) — share of main residences in moderate or severe overcrowding (`C22_RP_SUROCC_MOD + C22_RP_SUROCC_ACC`), over all occupation categories of the same complementary count. INSEE changed the definition in 2022 (the 2021 variable excluded one-person studios): the median rate goes from 13.5% to 24.6% with no real change behind it. Adaptive-capacity indicator, never scored |
| `26_adaptive_capacity.py` | `adaptive_capacity_iris.json` | Derived — adaptive-capacity index (mean percentile rank of median income, overcrowding, secondary residences), its tertile, and the exposure × means bivariate class. **Separate file, never an input to the exposure score** — see SCORING.md "Adaptive capacity — a separate axis" |
| `27_gp_supply.py` | `access/gp_sites_idf.geojson` | Access to care (v0.2) — RPPS (Annuaire Santé) GP practice sites in Île-de-France, liberal and health-centre GPs, minus an explicit list of teleconsultation, on-call, emergency and restricted services (listed in SCORING.md) |
| `28_pharmacy_supply.py` | `access/pharmacy_sites_idf.geojson` | Access rebuild — FINESS community pharmacies, Île-de-France |
| `29_access_demand_grid.py` | `access/demand_grid_idf.geojson` | Access rebuild — INSEE Filosofi 2021 200 m population grid, age-weighted with the DREES APL weights |
| `30_access_networks.py` | working files (`data/interim/access`) | Access rebuild — standard and accessible networks: OSM without steps (plus IGN BD TOPO staircases), Île-de-France Mobilités GTFS restricted to accessible stops and trips |
| `31_access_travel_times.py` | working files | Access rebuild — R5 (r5py) travel times, walking and public transport, several hours; runs in `Dockerfile.access` |
| `32_access_e2sfca.py` | `access_e2sfca_iris.csv` | Access to care — E2SFCA indicators per IRIS (GPs, pharmacies, inclusive-mobility gap) and sensitivity runs; read by script 11 |
| `33_route_destinations.py` | `access/route_destinations_idf.geojson` (+ `route_destinations_excluded.csv`) | Routes — key destinations in Île-de-France: general emergency departments, town halls, local France Travail agencies, post offices (BPE 2025); France Services (ANCT, fixed sites); CAF and CPAM offices open to all (DILA directory); GPs and pharmacies (scripts 27-28); heavy-network stop points (IDFM GTFS). Same inclusion rule in all four départements; every excluded record listed with its reason |
| `34_route_travel_times.py` | working files (`data/interim/access/routes_ttm*`) | Routes — R5 travel times from every inhabited 200 m cell to the nearest destination of each type, 4 profiles × 4 time slots; `ROUTES_SET=neighbourhood` for the everyday places of script 37. Runs for hours in `Dockerfile.access` |
| `35_key_figures.py` | `key_figures.json` | Derived — the figures quoted in the site's sentences (distribution, "highly exposed" by département, access-to-care gaps), computed from the published files, never typed by hand |
| `36_route_aggregate.py` | `routes_iris_<slot>.json`, `routes_stations_iris.json` | Routes — per-IRIS population-weighted median of the cell times, "more than 90 min" flag, imposed step-free detour |
| `37_neighbourhood_destinations.py` | `access/neighbourhood_destinations_idf.geojson` | Everyday places for the "Votre quartier" page: crèches, food stores, public nursery schools, police, social centres, libraries (BPE 2025), parks (regional open-space inventory); information only |
| `38_routes_summary.py` | `routes_summary.json` | Derived — the travel times quoted on the home page (metro-wide medians by profile, nearest station by département, emergency departments at night) |
| `39_neighbourhood_files.py` | `quartiers/<insee_com>.json`, `quartiers/index.json` | Derived — one small file per commune (per arrondissement in Paris) for the "Votre quartier" page: outlines, exposures and rank shares, means, travel times |

Scripts 27-32 are not part of `run_all.py`: the travel-time step takes
several hours and needs the access image (`docker build -f
Dockerfile.access -t underlaid-access .` — Java 21, r5py, osmium). Their
result, `data/processed/access_e2sfca_iris.csv`, is versioned in the
repo and read by script 11, so the quarterly run reuses it as is; the
working files (`data/processed/access/`) are git-ignored. Recompute
access by hand when the GP directory, the pharmacies or the timetables
change materially. Timetables: Île-de-France Mobilités GTFS, under the
"Licence Mobilités". One-off audits and validation analyses live in
`scripts/analysis/`.

The routes scripts follow the same pattern: 33, 34, 36 and 37 run by
hand in the access image (the travel-time run of script 34 takes about
a day with 3 processes), and their per-IRIS results
(`data/processed/routes_iris_<slot>.json`, `routes_stations_iris.json`)
are versioned. Scripts 35, 38 and 39 are part of `run_all.py`: they
only read published files, so the quarterly run refreshes the site's
key figures, the routes summary and the per-commune neighbourhood files
along with the score.

### Things worth knowing before re-running these scripts

- **`06_bpe.py`** auto-downloads `BPE25.zip` (136 MB, all of France) from
  the stable URL pattern `insee.fr/fr/statistiques/fichier/8217525/
  BPE25.zip`, then filters to the 4 MGP departments (`DEPCOM[:2] in
  ("75","92","93","94")`) while reading the CSV in chunks (the file is
  too large to comfortably hold whole-France in memory). This URL will
  need updating (`BPE25.zip` → `BPE26.zip`, new page id) whenever INSEE
  ships a new edition.
- **`07_equipment_access_200m.py`**: turned out simpler at MGP scale than
  expected — `depcom` is a normal 5-digit INSEE commune code even for
  Paris's legacy single-commune code, so a plain
  `depcom.str[:2].isin(MGP_DEP_CODES)` filter covers every department
  uniformly (the earlier Paris-only version special-cased `75056`
  explicitly; that's gone now, not needed).
- **`08_income_filosofi.py`**: INSEE encodes statistically masked values
  (small-population IRIS) as the string `"ns"` and uses a comma decimal
  separator; the script converts both before computing anything. 223 of
  2,752 MGP IRIS end up masked (`median_income` is null there) — this is
  expected, not a bug.
- **`09_social_index_schools.py`**: the middle-school (collèges) dataset
  ships its own geolocation; the primary-school (écoles) dataset does
  not, and is geolocated by joining on `uai` against the
  `fr-en-adresse-et-geolocalisation-etablissements-premier-et-second-degre`
  directory dataset. Only IRIS that actually contain a school get a
  value (1,211/2,752 for primary, 548/2,752 for middle schools) — most
  IRIS are residential zones with no school in them, which is expected;
  step 2 will need a nearest-school (rather than within-IRIS) approach
  if finer coverage is wanted.
- **`21_population_iris.py`**: same INSEE-scrape pattern as script 08
  (find the current download link on the INSEE statistics page rather
  than hardcoding a versioned URL). 2022 census since October 3, 2026
  (2021 before, to match Filosofi; Filosofi has no IRIS vintage after
  2021, so income stays 2021 — see SCORING.md, "Census 2022"). IRIS codes
  are read as text, so the leading zero of codes like `09…` can't be
  lost. Used to turn raw BPE-derived counts into per-1,000-
  resident rates — most directly the cool-facility deficit indicator in
  the thermal sub-score, and retroactively the RNA associational-density
  context layer (script 20).
- **`22_artificialization_mos.py`**: IGN's official OCS GE
  artificialization product turned out to have no accessible vector
  API — only WMTS/WMS tile imagery (fine for a basemap, useless for an
  area statistic) and a bulk per-department download behind a
  JS-rendered portal with no discoverable direct URL. Substituted IDF's
  own MOS (Mode d'Occupation du Sol) land-use survey instead — 79
  categories, 54 of which are classified as artificialized/sealed (see
  SCORING.md for the exact list and reasoning). Reuses the area-weighted
  overlay helper from `utils/geo.py` already used for green-space
  coverage; needed an explicit `.clip(upper=1.0)` after the overlay to
  fix a floating-point overshoot (max coverage came out as
  `1.0000000000023` before the fix).
- **`10_energy_performance.py`**: data.ademe.fr runs on the "data-fair"
  platform (not Opendatasoft like every other source here), so it has
  its own query API and cursor-based pagination. The full MGP has
  ~2.1M DPE records since July 2021, so this script takes longer to run
  than it did at Paris-only scale (~800k records).
- **`12_accessibility_erp.py`**: uses Acceslibre's bulk CSV export
  (~524MB, all of France, no API key needed) rather than the live API
  (which requires one). The `entree_pmr` accessibility field is
  crowdsourced and sparsely filled in (~19% nationally) — watch for the
  `pmr_documented` vs. `pmr_accessible` distinction, and note that pandas
  parses that column's "True"/"False" text as actual Python booleans
  (not strings), which the join logic compares against accordingly.
- **`14_qpv_boundaries.py`**: QPV is a validation-only layer by design —
  it's never joined to `code_iris` or fed into the score,
  only meant to be visually compared against the cumulative score map to
  sanity-check that already-recognized priority neighborhoods show up as
  exposed too.
- **`16_school_ac_context.py`** is different in kind from every other
  script: there is no dataset or API for "air-conditioned schools per
  arrondissement during the 2026 heatwave" — the figures were manually
  compiled from press articles and arrondissement-mayor communications
  (researched 2026-07-11), with a source URL cited per row. Coverage is
  genuinely incomplete (8/20 arrondissements have a published figure or
  note; the rest are `null`, not guessed). Same grain limitation as life
  expectancy / heatwave excess-mortality: Paris arrondissement-level
  context only, never extended to the inner suburbs (no equivalent
  research exists there), never joined to `code_iris` or fed into the
  cumulative score. Re-running this script doesn't refresh anything —
  there's nothing to download; update `SCHOOL_AC_DATA` by hand if better
  figures surface.
- **`15_pedestrian_paths.py`**: the "official" source
  (transport.data.gouv.fr's OSM-derived pedestrian-path dataset) only
  ships NeTEx, a transit-accessibility XML format with no simple GeoJSON
  export — queries the same underlying OpenStreetMap data directly via
  the Overpass API instead. Public Overpass instances reject requests
  without a real `User-Agent` header (a 406 from the reverse proxy, not
  from Overpass itself) — if this script starts failing, check that
  first.
- **`17_enedis_thermosensitivity.py`**: Enedis' open data portal migrated
  from `data.enedis.fr` (now just serves the JS app, not the API) to
  `opendata.enedis.fr`, which runs the same "data-fair" platform as
  ADEME's DPE dataset in step 10 — same `qs` Lucene filter and
  cursor-based pagination. Already at IRIS granularity (`code_iris` in
  the response), no spatial join needed. Watch for the source's own
  placeholder IRIS codes (e.g. `75103xxxx`) used for commune-level
  fallback rows when finer granularity isn't published — these
  correctly fail the `code_iris` join against the real IRIS reference
  and get logged by `check_unmatched_codes`, not silently merged.
- **`18_tree_age_context.py`**: there is no planting-date field in
  opendata.paris.fr's "les-arbres" dataset (confirmed by inspecting the
  schema directly) — trunk circumference (`circonferenceencm`) stands
  in as the standard arboriculture age proxy instead. Uses
  `utils/opendatasoft.query_records`'s `group_by` parameter (added for
  this script) to aggregate server-side (avg circumference, tree count,
  young-tree share per arrondissement) rather than downloading all
  ~219k raw tree points for a context-only, Paris-arrondissement-grain
  fact — no inner-suburb equivalent exists, so this stays Paris only.
- **`19_street_lighting_context.py`**: re-aggregates the already-collected
  `street_lighting_iris.geojson` (script 13) up to Paris arrondissement
  grain as area-weighted density (sum lamps / sum area, not an average of
  per-IRIS densities, so a few odd-shaped IRIS don't skew a small
  arrondissement). Deliberately kept as context, not wired into scoring
  — a real 5th sub-score would have changed the cumulative score from
  "X out of 4" to "X out of 5" everywhere in the app for one indicator
  that, unlike the other four, only proxies nighttime visibility rather
  than "inclusive mobility" (PMR accessibility and footway density, both
  now unscored context — see SCORING.md).
  Restricted to Paris communes from the start of
  the aggregation (not just filtered afterward): pandas' `.sum()` over an
  all-NaN group silently returns `0`, not `NaN`, so a non-Paris commune
  with no lighting data would otherwise have shown up as a fabricated
  "0 lamps" (verified absence) instead of a genuine "no data" — the same
  class of bug already caught once in script 13 itself, this time in an
  aggregation rather than a raw fill.
- **`20_associational_density_context.py`**: same `group_by` aggregation
  pattern as script 18, against data.iledefrance.fr's RNA (national
  associations register) mirror — now dissolved by **commune** rather
  than arrondissement (143 communes across the full MGP, widened from 20
  in Phase 5), and reporting **per 1,000 residents** as the primary
  figure (using script 21's population data) alongside per km² as a
  secondary one. Per km² alone was the only option before population
  data existed in this pipeline; keeping it alongside the new per-capita
  rate matters because it's a genuinely different distortion that
  per-capita doesn't fix — the lowest-per-km² communes include the Bois
  de Vincennes/Boulogne, whose large park area alone explains the low
  density, not weaker associational life. One commune (Pierrefitte-sur-
  Seine) has zero RNA records at all — confirmed directly against the
  source API (both active-only and any-status queries) as a genuine data
  gap, not a pipeline bug, before relaxing the test suite to tolerate it.
- Several scripts (`02`, `03`, `05`, `06`, `08`, `09`, `10`) detect column
  names from a candidate list rather than a single hardcoded name,
  because some sources' exact schema could only be confirmed by
  inspecting the first real download. If you hit a `RuntimeError`
  mentioning a missing column, inspect the raw file under `data/raw/`
  and extend the relevant candidate list in that script.
- **Corporate/AV network note**: if every script fails with
  `SSLCertVerificationError`, it's almost certainly a TLS-inspecting
  proxy/antivirus whose root certificate isn't in `certifi`'s bundle.
  `pip-system-certs` (in `requirements.txt`) fixes this by making
  `requests` trust the OS certificate store instead.

### Installation

**Local (venv):**

```bash
make install   # creates .venv/ and installs requirements.txt into it
make run       # runs every script in order via run_all.py
make run-01_iris_contours   # run a single script by name
```

Without `make`, the equivalent is:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # .venv/Scripts/pip.exe on Windows
.venv/bin/python scripts/run_all.py
```

**Docker:**

```bash
make docker-build   # builds the image (Python + GDAL + requirements)
make docker-run      # runs run_all.py, writing into ./data via a volume mount
```

The Docker image only bundles `scripts/`; `data/` is always a mounted
volume so downloaded/processed files land on the host, not inside the
container.

## Step 2 — Cumulative environmental exposure score

`scripts/11_compute_vulnerability_score.py` combines the layers above
into `data/processed/vulnerability_score_iris.geojson`: 4 sub-scores
(thermal — built from 4 indicators since Phase 5 added
artificialized-surface share alongside heat vulnerability, cool
facilities and canopy; air/noise pollution; housing — built from 2
indicators since Phase 3 added electrical thermosensitivity alongside
DPE; access to care — GPs and pharmacies, E2SFCA, since v0.2) plus a
cumulative score = the count of sub-scores simultaneously in their worst
quartile (0-4), by design not a weighted average. The former access
sub-score left the count at the v0 launch; its raw figures stay in the
output as unscored context (see SCORING.md, "Why access to services left
the score"). See **[SCORING.md](SCORING.md)** for the full formula,
weights, thresholds and known caveats (nothing here is a black box).

Run it after `run_all.py` (or `make run`, which already includes it):

```bash
make run-11_compute_vulnerability_score
```

Current distribution across the full MGP's 2,752 IRIS (2022 census):
28.1% score 0, 46.8% score 1, 22.1% score 2, 2.9% (79 IRIS) score 3,
0.1% (4 IRIS) score 4 — quartile thresholds are computed on IRIS with at least 50
residents only (see SCORING.md, "Quartile thresholds: inhabited IRIS
only", and the correction sections before it for everything that moved
this distribution). The four IRIS at 4/4: Flachat I in
Asnières-sur-Seine, Nonneville 3 and Nonneville 4 in Aulnay-sous-Bois,
Quatre Cités 3 in Champigny-sur-Marne.

### Tests

```bash
make test
```

`tests/` is a smoke-test suite, not full coverage (77 tests): every per-IRIS layer has exactly 2,752 rows, every context layer
has the row count matching its actual grain (20 for the 3 still-
Paris-only arrondissement facts, ~143 for the now MGP-wide commune-grain
RNA layer), `code_iris` is unique and well-formed against any of the 4
department prefixes, known masking patterns (Filosofi's `"ns"`) stay
within their documented range, and — the one that actually matters —
**no sub-score's quartile split skews past 35% for any single quartile
among IRIS with valid data**. That last one is a standing regression
guard for the sparse-data bias described above: it's the automated
version of the 47%-vs-25% check that caught it in the first place, so a
future source addition (or a further geographic expansion) can't
reintroduce the same bias silently. Because an exact overall quartile
split can hide that bias, a second test checks the worst-quartile share
by *number of indicators available* for each sub-score (max/min ratio
under 1.5) — the check that caught access's 29.6%-vs-17.6% skew. The
adaptive-capacity axis has its
own guards: masking follows income masking exactly, tertiles stay
balanced, no cell of the 3×3 grid is anomalously over-represented, and
no capacity field ever appears in the exposure score's output.

## Step 3 — Web site

`frontend/` is a Vue 3 site prerendered with `vite-ssg` (redesign D4,
October 2026; see `frontend/README.md`). French at the root, English
under `/en`. It never recomputes the score: it reads the files of
`frontend/public/data/`, copied from `data/processed/`.

- **Home**: an address field, an optional way of getting around (without
  constraint, slow walk, wheelchair), an illustrated plan of a few
  everyday places with the metropolitan median times, and one question
  drawn at random (including "Lequel de ces quartiers ?": two anonymised
  neighbourhoods, close but different or far apart but alike, names only
  in the answer).
- **Votre quartier** (`/quartier/<INSEE code>`, one prerendered page per
  neighbourhood, never an address in the URL): the living environment
  (heat, air and noise, energy performance of housing, access to care,
  each placed among the 2,752 neighbourhoods), what is within reach (one
  position bar per need — mean of the ranks of its places — and the
  nearest place of each type for each way of getting around), and both
  together. Each page loads only its commune's file
  (`frontend/public/data/quartiers/<insee_com>.json`, script 39).
  Travel-time display rules (3 October 2026): public services, GP and
  pharmacy are information only, never a sub-score; at night only
  emergency departments and stations are shown; the wheelchair profile is
  presented as a lower bound.
- **Explorer la carte**: MapLibre GL without a basemap (real IRIS
  outlines, inner commune boundaries, the Seine), six themes, filters
  combined with AND ("highly exposed" = at least 2 of the 3 exposures;
  resources in the lowest quarter; access to care in the hardest
  quarter), a text alternative (sortable list). Reads `map_iris.geojson`
  (script 39: only the fields the map uses, 5-decimal outlines).
- **Quartiers les plus exposés**: the inhabited neighbourhoods with at
  least 2 of the 3 exposures (407 with the October 2026 data), those with
  all three first, grouped by residents' resources.
- **Méthode**, **À propos**, **Tous les lieux du quotidien**,
  **Corrections**, **Accessibilité** (RGAA 4.1, "partiellement
  conforme" until the manual tests are done; `docs/accessibilite.md`).

```bash
cd frontend
npm install
npm run dev
```

Checks (all in CI, `.github/workflows/frontend-checks.yml`):
`npm run test:smoke` (full journey), `npm run test:a11y` (axe-core and
keyboard, desktop and phone), `npm run test:fit` (home page at 9 screen
sizes), `npm run test:overflow` (no sideways scrolling at 320, 375 and
390 px, Chromium and WebKit), `npm run test:seo` (title, description,
sharing image, canonical and hreflang on every prerendered page).
Lighthouse report: `bash frontend/scripts/lighthouse-report.sh` →
`docs/lighthouse.md` (local build), or with
`LIGHTHOUSE_BASE_URL=https://underlaid.fr` against the live site. The
weekly workflow `.github/workflows/lighthouse.yml` does the latter every
Monday: table in the job summary, JSON reports as an artifact, an issue
when accessibility or SEO drops below 100 on any page.

## Living conditions and residents' resources

Part 3 of each neighbourhood page ("Les deux à la fois") places the
neighbourhood on a cloud of all neighbourhoods: number of exposures in
the most affected quarter against residents' resources. It is
descriptive, never presented as a tested result; the tested hypotheses
(pre-registered, with their verdicts) are on the Method page and in
[SCORING.md](SCORING.md#working-hypothesis-and-its-test-pre-registered).
What the cloud shows is that exposure does not follow income neatly:
every level of exposure spans almost the whole range of resources, and
the link is weak (slightly positive only because of dense, older central
Paris). "The poorest neighbourhoods cumulate the most exposures" is not
what the data shows.

## What building this actually taught us

The surprises along the way — French open data quirks, the sparse-data
bias found (twice) in the quartile ranking, and why the score is an
estimate that moves with every correction — are in
**[docs/LESSONS.md](docs/LESSONS.md)**.

## Step 5 — Static build & deployment

No backend, no database, no server-side code anywhere in this project.
All the heavy lifting (downloads, spatial joins, the score itself)
happens once, offline, in `scripts/`; the frontend only ever fetches a
pre-computed static GeoJSON and colors it. There is nothing to
recompute client-side and nothing that needs a secret environment
variable — every source is public open data.

### Build

```bash
cd frontend
npm run build   # runs vite-ssg build, outputs to frontend/dist/
```

`npm run build` runs `vite-ssg build` rather than a plain `vite build`
(see "SEO and pre-rendering" below) — bundling and static prerendering
happen in the same command, no extra step needed.

Current build (October 2026): about 275 MB in `dist/`, almost all of it
the 5,504 prerendered neighbourhood pages (about 46 KB each, a few KB
compressed); the main JavaScript bundle is about 160 KB, the map code
(MapLibre) is loaded only on "Explorer la carte", and the map reads
`map_iris.geojson` (2.6 MB, about 0.6 MB compressed).

**Geometry: precision reduced, shapes not simplified.** The published
`vulnerability_score_iris.geojson` goes through
`npx mapshaper vulnerability_score_iris.geojson -o precision=0.000001` only
(6 decimal places, ~11 cm at this latitude): 6.4 MB → 4.6 MB (1.0 MB
gzipped), every coordinate kept. An earlier version also ran
`-simplify 10% keep-shapes`; re-measured on all 2,752 IRIS (not one
spot-checked polygon) at the v0 launch, it shifted IRIS areas by 3.9% at
the median and up to 85% for small IRIS — and the address search uses
these exact outlines to decide which neighborhood an address falls in.
Every simplification level tested saved at most ~160 KB gzipped
(properties, not shapes, dominate the file), so shapes are kept intact.
Re-run the command above after every copy from `data/processed/`.

### SEO and pre-rendering

The site address is set in one place (`frontend/src/siteUrl.js`,
`https://underlaid.fr`; `SITE_URL=` overrides it at build time). Every
page — French at the root, English under `/en`, and one page per
neighbourhood in each language (5,504) — is prerendered with
`vite-ssg` and carries its own `<title>`, meta description, canonical
address, reciprocal `hreflang` alternates and sharing image
(`frontend/public/share/`, made by `frontend/scripts/make-share-images.mjs`).
`sitemap.xml` (main pages and inhabited neighbourhoods) and `robots.txt`
are written at build time; preview deployments are never indexed. The
Method page carries schema.org `Dataset` markup (ODbL licence, DOI,
dates, author). The project's former Vercel address redirects
permanently to the same path on https://underlaid.fr (`frontend/vercel.json`,
generated with the page redirects by `frontend/scripts/sync-redirects.mjs`).

Two bugs met when wiring prerendering, kept as lessons: `@unhead/vue`
existed in two incompatible versions (per-route `<head>` tags silently
ignored), and a shared `i18n` singleton leaked the locale between pages
rendered at the same time (fixed with one i18n instance per
`createApp()`).

### Deploy

Both configs are committed and ready to point a host at:

- **Vercel**: `frontend/vercel.json` (`buildCommand`/`outputDirectory`).
  In the Vercel dashboard, set the project's **Root Directory** to
  `frontend` (Vercel doesn't have a monorepo "base path" field in
  `vercel.json` itself — the root directory setting is where that lives).
- **Netlify**: `netlify.toml` at the repo root, with `base = "frontend/"`
  — no dashboard configuration needed, it's all in the committed file.

Neither config needs any environment variables — unless the automated
update workflow below is wired to a deploy hook, in which case that
hook lives in the host's own dashboard, not in these files.

**A real bug, found and fixed after the switch to static pre-rendering
(see "SEO and pre-rendering" above):** both configs originally carried
a blanket SPA-fallback rewrite (`/(.*)` → `/index.html` on Vercel,
`/*` → `/index.html` on Netlify) — correct for the pure client-side-routed
app this was before `vite-ssg`, where a direct visit to `/ranking` had
no matching file and needed Vue Router to handle it after the fact.
Once every declared route got its own real prerendered HTML file (8
total — `index.html`, `methodology.html`, `ranking.html`, `press.html`,
and their `fr/` counterparts), that same rewrite became actively
harmful: it would have made both hosts serve the home page's
`index.html` for every URL, `/ranking` and `/fr/ranking` included,
silently undoing the entire prerendering effort. This wouldn't show up
testing locally via `vite preview` — that server has no concept of
either host's rewrite rules, it just serves whatever static file
matches the request path directly, which is exactly why it went
unnoticed until the configs themselves were reviewed directly rather
than only testing the local build output. Fixed by removing the
fallback entirely from both files: with every route now a real static
file, no SPA fallback is needed, and a truly unmatched path should
return each host's normal 404 rather than silently serving the home
page.

### Keeping the data current — automated updates

`.github/workflows/update-pipeline.yml` re-runs the full pipeline on a
schedule (`0 3 1 1,4,7,10 *` — 03:00 UTC on the 1st of January, April,
July and October) and on manual `workflow_dispatch`. Quarterly because
most sources here (INSEE, IGN/IDF, Airparif/Bruitparif, Enedis, RNA...)
don't change more often than that; DPE and Acceslibre do update more
frequently upstream and could get their own faster schedule later if
that turns out to matter — not built now since a full run only takes a
few minutes, so splitting it adds workflow complexity for a benefit
nothing has needed yet.

**When a source fails** (`scripts/pipeline_policy.py`). Every script
belongs to a family. The IRIS reference, the scored categories and the
means-to-cope axis are **blocking**: if one fails, the run stops and
nothing is published. Context-only layers (detail-panel figures such as
travel times or the school social position index, the context modal, the QPV outline)
are **not blocking**, under guardrails: their previous version is
restored and kept only if it still has the expected schema (columns,
and exactly the current IRIS codes for IRIS-grain layers) and is less
than two quarters old — otherwise the failure blocks like the others.
A kept layer keeps its own date in `last_updated.json` (`"layers"`),
which the site shows next to its figures ("data as of …"), and the
failure is written to `data/processed/run_report.json`, from which the
workflow opens a GitHub issue (or comments on the open one for that
script). Why: on 2026-10-01, two context-only sources broke upstream
(the middle-school IPS dataset lost its coordinates; the Acceslibre
file URL changed); under an "everything blocks" rule they would have
held back the quarterly refresh of the whole score.

The workflow never publishes blind. After running `scripts/run_all.py`
(inside the project's own Docker image, so it gets the same
GDAL/geopandas environment already validated for local use — see
`Dockerfile`), it runs the existing `tests/` suite against the fresh
output first (code_iris well-formedness, layer row counts, the standing
47%/25% sparse-data-bias regression guard, etc.) — a failure here means
something is structurally broken, not just a distribution shift, so it
routes to the same "open a PR, don't publish" path as the diff check
below. Only once tests pass does it run `scripts/23_diff_report.py` to
compare the fresh output against whatever is currently live in
`frontend/public/data/`:
how many IRIS entered/left the score->=3 population, and how much the
0-4 category breakdown shifted. This is the automated form of an audit
this project has already had to do by hand twice (`access_time`,
`cool_facility_deficit` — see SCORING.md): in both of those real cases,
a distribution shift this large turned out to be a bug, not a real
change in the world, and a person looking at the numbers is what caught
it. A quarterly unattended run has no one to do that unless the workflow
stops and asks — so it does:

- **Within the default thresholds** (<=15% turnover on score->=3, no
  single category's share moving by more than 5 percentage points): the
  new data is copied into `frontend/public/data/`, a dated snapshot is
  kept in `data/history/` (`scripts/prune_export_history.py`, last 4
  runs retained), and the change is proposed as a pull request (branch
  `automated-update/within-thresholds`): `master` is protected (pull
  requests only, checks required, no direct push), so a person merges it
  and the host deploys on merge. A pull request opened with the
  workflow's own token does not start the required checks: close and
  reopen it to run them.
- **Past either threshold**: nothing is published. The workflow opens a
  pull request instead (branch `automated-update/needs-review`, using
  [`peter-evans/create-pull-request`](https://github.com/peter-evans/create-pull-request)),
  with the diff report as the PR body, so a person reviews the actual
  data change before it goes anywhere near the live site. Merging that
  PR only updates `data/processed/` — completing the publish (copying to
  `frontend/public/data/`, committing, redeploying) is still a manual
  step after that, deliberately: the threshold existing at all means this
  case is exactly the one that shouldn't be made one click shorter.

`scripts/run_all.py` also writes `data/processed/last_updated.json`
(just `{"generated_at": "<UTC timestamp>"}`) at the end of a successful
run — copied to `frontend/public/data/` on every accepted publish, and
shown on every page's footer and on `/methodology` next to the
distribution table, so a specific example (Drancy, etc.) can always be
read against the snapshot it came from rather than assumed current.

### Integrating into an existing site

Two ways, both documented here since the brief asked for both:

**1. Dedicated subdomain** (e.g. `underlaid.yoursite.com`): deploy this
`frontend/` as its own Vercel/Netlify project, then point a CNAME record
for that subdomain at the host's provided domain. No code changes needed
— it's a standalone static site.

**2. Iframe embed** of a page of the site, for instance the map or one
neighbourhood:

```html
<iframe
  src="https://underlaid.fr/carte"
  width="100%"
  height="800"
  style="border: none;"
  loading="lazy"
  title="Underlaid — carte des quartiers de Paris et de la petite couronne"
></iframe>
```

A neighbourhood page has a stable address (`https://underlaid.fr/quartier/<IRIS code>`,
`/en/neighbourhood/<IRIS code>` in English). Pages adapt to the width
of the frame (layouts are tested down to 320 px).

## Roadmap

**v0.1** — the public launch: cumulative exposure score over the 2,752
IRIS of Paris and the inner suburbs, the separate "means to cope" axis,
methodology and press pages in French and English, quarterly automated
data updates behind a publication guard-rail.

**v0.2** — access to care back in the score (now on 4), rebuilt without
a car and weighted by how many people share each GP and pharmacy
(E2SFCA); inclusive mobility shown for information; the pre-registered
hypothesis tested and its verdicts published (SCORING.md).

**Redesign and travel times** (October 2026) — the redesigned site at
https://underlaid.fr ("Votre quartier", "Explorer la carte"); precomputed
travel times from each neighbourhood to emergency departments, GP,
pharmacy, public services, everyday places (crèches, food stores,
nursery schools, police, social centres, libraries, parks) and, in Paris
only, public toilets and drinking fountains; the pre-registered
public-services hypothesis tested (refuted, and reversed); the census
moved to 2022 (sensitivity check published).

**v0.3** (7 October 2026) — the second travel-time calculation
(pre-registered on 4 and 5 October 2026, published with PR #7): the same
start and end points for every way of getting around (wheelchair times
shorter than unconstrained ones: 11 cases out of 62,788), a revised
wheelchair profile (0.8 m/s; streets steeper than 8 % avoided using the
IGN RGE ALTI 1 m; sensitivity 0.5-1.0 m/s and 6 %), and public schools
(elementary, collège, lycée; private schools under contract computed but
not shown). The three verdicts were checked with it and confirmed; the
published verdicts stay the reference. Publication thresholds written
before the results are in `docs/checks/`.

**In progress** — a descriptive decomposition of wheelchair travel times
(pre-registered on 7 October 2026, no verdict), computed the night of
7 October: share of journeys made entirely on foot per way of getting
around, and how much of the wheelchair gap comes from speed and slopes
versus inaccessible stops.

Next:
1. **New indicators** (Phase 7): **flood risk** (Seine/Marne PPRI — a
   possible next layer, not measured today), soil and water pollution,
   aircraft noise, industrial risk, digital divide. Each goes through the
   same variance/skew check before entering anything.
2. **Lift availability**: the IDFM lift-status feed is archived hourly
   since 6 October 2026 (`scripts/archive_elevators.py`), for an
   availability rate per station after the launch.
3. **Access to public services nationwide** (Phase 9): a separate
   commune/200 m-grid module, not an extension of this score.
4. Citizen reporting, a guide to adapting Underlaid to another city.

Not planned for now: Grande Couronne, PWA.

## License & data attribution

**Code**: [MIT](LICENSE). **Published data** (`frontend/public/data/*.geojson`,
i.e. the score and every indicator behind it): [Open Database License (ODbL)
1.0](https://opendatacommons.org/licenses/odbl/1-0/). That's not a free
choice: two inputs (OpenStreetMap, and the Ville de Paris datasets) are
themselves ODbL, whose share-alike clause applies to any derived database
made public. Every other input is under the Licence Ouverte / Open Licence
2.0 (Etalab), which explicitly allows redistribution under ODbL.

Each source keeps its original license. Every entry below was checked
against the publisher's own metadata (portal API or reuse-terms page) in
September 2026, not assumed:

| Source | Publisher | Used for | License |
|---|---|---|---|
| IRIS contours 2024 (data.iledefrance.fr) | IGN & INSEE | Neighborhood boundaries | Licence Ouverte 2.0 |
| BPE 2025, Filosofi 2021, Recensement 2022 (population, housing), access-time 200m grid | INSEE | Services, cool facilities, route destinations, income, population, secondary residences, overcrowding, access time | Licence Ouverte 2.0 — "Source : Insee" |
| [France Services sites](https://www.data.gouv.fr/datasets/liste-des-structures-labellisees-france-services) (licence checked on the publisher's data.gouv.fr page, 3 October 2026) | ANCT | Route destinations | Licence Ouverte 2.0 |
| [Directory of public administration](https://www.data.gouv.fr/datasets/service-public-gouv-fr-annuaire-de-ladministration-base-de-donnees-locales), CAF and CPAM offices (licence checked on the publisher's data.gouv.fr page, 3 October 2026) | DILA, published under Premier ministre (service-public.gouv.fr) | Route destinations | Licence Ouverte (version 1.0) |
| Urban heat island indicators (Sat4BDNB, data.gouv.fr) | CSTB | Thermal | Licence Ouverte 2.0 |
| Open green & wooded spaces; MOS land use 2021 (data.iledefrance.fr) | L'Institut Paris Region | Thermal | Licence Ouverte 2.0 |
| Air-noise co-exposure map 2024 | Airparif & Bruitparif | Pollution | Published as open data with no formal license named; the publisher requires this citation: *"Source des données : Cartographie air-bruit établie par Airparif et Bruitparif – http://carto.airparif.bruitparif.fr"* |
| IPS social position index, school directory (data.education.gouv.fr) | DEPP — Ministère de l'Éducation nationale | Context, not scored (school social position index) | Licence Ouverte 2.0 |
| DPE energy performance certificates (data.ademe.fr) | ADEME | Housing | Licence Ouverte 2.0 |
| Electricity consumption by IRIS (opendata.enedis.fr) | Enedis | Housing (thermosensitivity) | Licence Ouverte 2.0 |
| Acceslibre (data.gouv.fr) | Acceslibre | Context, not scored (PMR accessibility) | Licence Ouverte 2.0 |
| QPV boundaries (data.iledefrance.fr) | ANCT | Validation layer, not scored | Licence Ouverte |
| RNA associations directory (data.iledefrance.fr) | Ministère de l'Intérieur | Context, not scored | Licence Ouverte 2.0 |
| Street trees, public lighting (opendata.paris.fr) | Ville de Paris | Context, not scored | **ODbL** |
| Footways (Overpass API); street network (Geofabrik Île-de-France extract) | © OpenStreetMap contributors | Footways: context, not scored; street network: travel times for access to care | **ODbL** |
| RPPS directory of health professionals (Annuaire Santé) | Agence du Numérique en Santé (ANS) | Access to care (GPs) | Licence Ouverte 2.0 |
| FINESS (pharmacies) | Ministère de la Santé | Access to care (pharmacies) | Licence Ouverte 2.0 |
| APL age weights and distance decay | DREES | Access to care (method parameters) | Licence Ouverte 2.0 |
| Filosofi 2021 200 m population grid | INSEE | Access to care (demand) | Licence Ouverte 2.0 — "Source : Insee" |
| Public transport timetables (GTFS) | Île-de-France Mobilités | Access to care, inclusive mobility and routes (travel times) | **Licence Mobilités** — "Contient des informations de « Horaires prévus sur les lignes de transport en commun d'Île-de-France (GTFS Datahub) », mises à disposition par Île-de-France Mobilités aux conditions de la « Licence Mobilités »." |
| BD TOPO (staircases) | IGN | Inclusive mobility (step-free walking) | Licence Ouverte 2.0 |
| RGE ALTI 1 m (terrain model) | IGN | Slopes of the wheelchair network (streets steeper than 8 % avoided) | Licence Ouverte 2.0 |
| [Lift status](https://data.iledefrance-mobilites.fr/explore/dataset/etat-des-ascenseurs/) (PRIM API) | Île-de-France Mobilités | Archived hourly since 6 October 2026; not used yet, not redistributed | **Licence Mobilités** |
| Address search (API Adresse / BAN) | IGN, DINUM | Web map search | Licence Ouverte 2.0 |

Context figures quoted but not redistributed as data (life expectancy —
Institut Paris Region / APUR / ORS Île-de-France; heatwave excess
mortality — Santé publique France; air-conditioned schools — mairie and
press communications, see `scripts/16_school_ac_context.py`) are cited
with their source where they appear on the site.

To cite the project, see [`CITATION.cff`](CITATION.cff) (GitHub shows a
"Cite this repository" button), and include the date of the data
snapshot you used — it's shown in the site footer, and the score moves
with every pipeline run.
