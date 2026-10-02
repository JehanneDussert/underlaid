# What building Underlaid actually taught us

*Moved out of the [README](../README.md) to keep it short for first-time
visitors. Paths below are relative to the repository root.*

Not the plan — the surprises. Kept here because they'd otherwise get
lost the next time someone (human or not) touches this pipeline.

**French open data is less standardized than it looks.**
- Identical-sounding dataset titles on data.gouv.fr are not globally
  unique. The generic-looking slug for "Carte des îlots de chaleur
  urbains (ICU)" turned out to belong to Toulouse Métropole, not Paris —
  the actual Paris-relevant heat data lived under a differently-named
  national dataset (Sat4BDNB). Always check the *publishing
  organization* field, never trust a title match.
- A regional portal mirror can be the authoritative source, not a
  derivative to be suspicious of: `data.iledefrance.fr`'s "iris" dataset
  is a direct IGN & INSEE republication (confirmed via its own API
  metadata), and ended up more practical to query than hunting for the
  "official" national endpoint would have been.
- The "recommended" source isn't always the practical one: Paris's
  official pedestrian-path dataset only ships NeTEx (a transit-industry
  XML format with no simple geometry export). The same OpenStreetMap
  data underneath it is directly queryable via Overpass in plain
  GeoJSON-friendly form — same information, far less parsing.
- Paris itself is coded two incompatible ways across sources: 20
  per-arrondissement commune codes (`75101`-`75120`, used by our IRIS
  reference and Filosofi) vs. one legacy citywide code (`75056`, used by
  the equipment-access grid and the QPV dataset). Three different
  scripts had to detect this and fall back to spatial joins instead of
  attribute joins.
- Crowdsourced data (Acceslibre) is sparse in ways that matter: only
  ~19% of accessibility records nationally have their key field filled
  in at all. Treating "undocumented" as "inaccessible" would have
  silently invented a signal that isn't there.
- Sometimes the honest answer is that the data simply doesn't exist.
  DansMaRue's open data (live dataset and all yearly historical exports,
  2012-2025) has a report date but never a resolution date or status —
  the "differentiated public-service responsiveness" axis originally
  planned for Phase 3 had to be dropped entirely, not approximated,
  once that was confirmed directly rather than assumed. Same for tree
  planting dates (trunk circumference stands in instead). Population
  was a temporary version of this story, not a permanent one: Phase 3
  reported associational density per km² only because no clean
  population figure existed in the pipeline at the time; Phase 5 later
  added one (script 21, INSEE Recensement), which is exactly why that
  figure could be revisited and switched to per-1,000-residents as the
  primary metric rather than staying a workaround forever. A data source
  not existing is a finding worth documenting, not a blocker to quietly
  route around — but it's also worth re-checking later, since "doesn't
  exist yet" and "will never exist" aren't the same claim.
- Not every accessible mirror is equally trustworthy for equally
  sensitive data. A third-party commune's Opendatasoft mirror was the
  only accessible source found for 2026 municipal-election results —
  fine for tree circumference, not solid enough footing to publish
  arrondissement-level abstention rates, given how much more politically
  loaded that topic is than canopy age. Skipped rather than published on
  uncertain provenance.

**Small bugs hid in type coercion, not logic.**
- pandas silently parses a CSV column of `"True"`/`"False"` text as
  actual Python booleans, not strings — comparing against the string
  `"True"` fails with no error, just quietly wrong (all-zero) output.
  Caught only because a summary statistic looked implausible.
- Vue's `<style scoped>` silently no-ops a `:root { }` block (the
  scoping attribute gets appended to `:root`, which never matches
  `<html>`), so CSS custom properties defined there never apply. They
  have to live in a genuinely global stylesheet.
- `pd.NA` as a missing-value placeholder is a trap two levels deep.
  First: Fiona's GeoJSON writer doesn't recognize it and serializes it
  as the literal string `"<NA>"` instead of JSON `null` — caught because
  the frontend rendered "Q<NA>" for one IRIS. The naive fix (plain
  Python `None` instead) turned out to be its own trap: assigning `None`
  into a column forces pandas to "object" dtype, and Fiona then
  stringifies **every** value in an object-dtype column, not just the
  missing ones — a subsequent feature's strict `=== 4` comparison in JS
  silently matched nothing, because `4` had become the string `'4'`.
  The actual fix was `np.nan`, which keeps the column genuine `float64`
  end to end — the same pattern that had already worked correctly,
  un-remarked, for `cumulative_vulnerability_score` the whole time.
- A page's own CSS can shadow a global rule by accident. A print
  stylesheet meant to hide only the app shell's footer used a bare
  `footer` selector, which also matched an unrelated page's legitimate
  content `<footer>` and silently deleted it from the printed PDF.
  Fixed by selecting the shell's footer by its actual `id` instead of
  its tag.
- A background that looks fine can be silently wrong for content that
  doesn't exist yet. `html`/`body` were pinned to `height: 100%` (one
  viewport) for a decorative radial-gradient glow, which worked
  perfectly until a page taller than one screen (the methodology page)
  got built — the glow then tiled down the entire scrollable canvas,
  since nothing told the browser not to repeat it past that first
  screen's height. Fixed with `background-attachment: fixed` +
  `background-repeat: no-repeat`, but it only became visible once a
  taller page actually existed to reveal it.

**The environment fought back more than the code did.**
- A corporate/AV TLS-inspecting proxy broke certificate validation two
  different ways for two different tools (Python's `requests` — fixed
  with `pip-system-certs`; `curl`'s Windows `schannel` backend — no fix
  found, still broken) while a real browser's network stack handled the
  exact same hosts without any special configuration at all.
- Headless Chromium (via Playwright, used to verify the frontend)
  intermittently loses its WebGL context for reasons specific to
  software-rendered headless GPU emulation — fixable with
  `--use-angle=swiftshader-webgl` most of the time, but not always. Real
  users on real GPUs won't see this; it's purely a test-environment
  artifact, and worth not over-indexing on.
- A completely unrelated Docker container was already squatting on the
  default Vite port (5173), so `curl localhost:5173` returned a
  confident `200` from someone else's app. The real dev server had
  silently moved to 5174; only tracing the listening PID caught it.
- What a browser *displays* and what `canvas.toDataURL()`/`drawImage()`
  can actually *read back* from that same canvas aren't guaranteed to
  match — and this turned out to be true even outside headless
  software-rendered WebGL, not just inside it. The press-kit map export
  composites the MapLibre canvas + deck.gl's own canvas; the deck.gl
  layer (vector data, no textures) always reads back correctly, but the
  MapLibre basemap (raster tiles) sometimes came back solid black
  despite rendering correctly on screen moments earlier. Tested directly
  on a real, hardware-accelerated browser (confirmed via `chrome://gpu`:
  "WebGL: Hardware accelerated") rather than assumed fixed once off
  headless — and the same failure reproduced there too, intermittently,
  with no fixed wait time (tried up to 3s) that reliably prevented it.
  That ruled out "headless-only" as the explanation; it's a transient
  GPU/driver buffer-swap race on this specific canvas. Fixed with
  detection + retry (sample a few pixels after each repaint; if the
  basemap area is still solid black, wait and try again, up to 4
  attempts) rather than a longer fixed delay, which doesn't reliably
  help against a race — the same defensive pattern already used
  elsewhere in this codebase for WebGL context loss.

  Verified at two sample sizes rather than trusting an initial small
  one: a first batch of 5 runs, then a second batch of 20 (a 5-run
  sample can easily hide a residual 5-10% failure rate that only shows
  up at more scale). Combined result: **24 of 25 runs read back the
  basemap correctly** — independently verified each time by sampling
  actual pixels from the downloaded PNG in a fresh page, not just
  trusting the app's own console log. The single failure (in the first,
  5-run batch) turned out to be a genuine CARTO tile-fetch network
  error, not the WebGL race the fix targets — correctly distinguished
  because the retry logic logs which one occurred instead of masking
  both the same way. The 20-run batch alone came back 20/20, with the
  retry path never even triggered (every run's basemap read back
  correctly on the very first attempt) — a good sign the underlying
  race is either rare or specific to conditions this second batch's
  brief pause between runs happened to avoid, but 0 failures in 20
  trials still leaves real uncertainty about the exact residual rate
  (a common small-sample rule of thumb puts the plausible upper bound
  closer to 10-15% than to 0%, not "proven negligible"). Treat this as
  strong evidence the fix meaningfully helps, not proof the race can
  never resurface.

- pandas' `.sum()` over an all-`NaN` group silently returns `0`, not
  `NaN` — a second instance of the same underlying failure mode as the
  unconditional-`fillna(0)` bug already caught in street lighting's raw
  layer (script 13), this time one level removed, inside script 19's
  `groupby().agg()` aggregation up to arrondissement grain. Fixed by
  restricting the whole script to Paris communes from the start, rather
  than trying to patch the aggregation after the fact. Found precisely
  because Phase 5's expansion introduced groups (non-Paris communes)
  that could legitimately have zero underlying rows for a Paris-only
  source — a case the original Paris-only version never exercised.

**The score itself is an estimate, not a fixed ground truth.**
Adding the two accessibility indicators (Acceslibre, footway density)
shifted which IRIS reach a cumulative score of 4 — one dropped out, one
new one appeared. That's expected for a score built from equal-weighted
z-scores and percentile ranks, not a bug: every new indicator nudges the
boundary. It also means the score should be re-examined, not blindly
trusted, each time a new sub-score indicator is added — which is exactly
why SCORING.md documents the current distribution instead of leaving
it implicit.

**Crossing the score with residents' means revealed income hidden in the exposure score.**
The exposure score was built to measure exposure only — income was
deliberately kept out. But the "access to services" sub-score included
the social position index (IPS) of nearby schools, which describes who
lives in a neighborhood, not what it's exposed to, and follows household
income by construction. Nothing flagged it while the score was looked
at on its own: every quartile check passed. It only showed once the
score was crossed with a separate measure of means (Phase 8): the
access sub-score moved with means at −0.52, and the "high exposure /
low means" cell turned out to be largely built on that one indicator.
Access left the score at the v0 launch (see SCORING.md, "Why access to
services left the score"). The lesson: an axis you keep separate is
also an instrument for auditing the other one — cross them, and look
at what drives the overlap, before quoting it.

**An OpenStreetMap density also measures how hard volunteers have mapped.**
Footway density (script 15, `highway=footway` ways per km²) looked like
a clean walkability proxy. It mostly measured mapping practice: Paris
contributors draw 53% of sidewalks as separate ways, Seine-Saint-Denis
contributors 17% — elsewhere, sidewalks are usually a `sidewalk=both`
tag on the street, which the query never counted. At equal population
density, Paris came out at 2.4× the expected density and
Seine-Saint-Denis at 0.4×. Aerial imagery settled it: Clichy "Klock"
(53,000 residents/km², sidewalks plainly visible, 56 streets tagged
`sidewalk=*`) scored 52 m/km²; Paris 11e "Saint-Ambroise 4", same kind
of streets, 165,000. Any crowd-mapped density needs the same check
before it enters a score: compare it with a physical driver (population
density) by area, look at how the feature is tagged in each area, and
eyeball the extremes on imagery.

**Counting the tags properly doesn't fix uneven mapping.** The obvious
repair — count sidewalks both ways they're recorded (drawn `footway=sidewalk`
lines, and `sidewalk=both|left|right` on the street, each sidewalk once) —
does fix Klock: 1.87 m of sidewalk per metre of street, against 1.76 in
Saint-Ambroise 4. But the audit run before rebuilding access
(`scripts/analysis/osm_sidewalk_completeness.py`, Geofabrik extract of
2026-09-30) measured the deeper problem: the share of street length with
*any* sidewalk information. The rule was set before computing: a gap of
more than 15 points between departments at equal density would make the
indicator unusable for comparisons.

| Residents per km² (fifths of inhabited IRIS) | Paris | Hauts-de-Seine | Seine-Saint-Denis | Val-de-Marne |
|---|---|---|---|---|
| All | 96% | 63% | 26% | 47% |
| under 7,200 | 83% | 51% | 23% | 36% |
| 7,200 to 12,900 | 97% | 62% | 26% | 60% |
| 12,900 to 21,000 | 97% | 72% | 32% | 62% |
| 21,000 to 34,100 | 99% | 75% | 37% | 74% |
| over 34,100 | 99% | 82% | 48%* | 57%* |

\* fewer than 20 IRIS of that department in the band.

The gap reaches 71 points. Unknown isn't absent: Aubervilliers "Firmin
Gemier" has no sidewalk information on any street, and imagery shows
sidewalks. Wheelchair-relevant attributes are worse: width recorded for
under 1% of sidewalks everywhere, surface for 72% in Paris vs 21% in
Seine-Saint-Denis, kerbs 119 vs 33 per 100 crossings. So no OSM sidewalk
figure enters the score, the old footway density left the map, and the
access rebuild routes walking on the full street network and takes
accessibility from official sources (Île-de-France Mobilités). The
general point: before trusting a crowd-mapped *attribute*, measure how
often it's filled in, by area and at equal density — not just its value
where it is filled in.

**A balanced quartile split can hide a sparse-data bias.**
Every sub-score is cut into exact quartiles overall, so the standing
"no quartile above 35%" test passes by construction. The bias only
shows when IRIS are grouped by how many indicators they actually have:
access sat at 29.6% in the worst quartile with 3 of 4 indicators vs
17.6% with all 4. `test_worst_quartile_share_does_not_depend_on_indicator_count`
now checks that grouping for every scored sub-score (max/min ratio
< 1.5).
