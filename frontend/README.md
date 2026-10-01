# Underlaid — frontend

Vue 3 + deck.gl choropleth map of the cumulative vulnerability score
computed in `../scripts/`. See the project root README for the full
pipeline; this is just the map.

## Stack

- **Vue 3** (`<script setup>`). `src/App.vue` is just the shell (topbar +
  footer, shared across every route); the actual pages live in
  `src/views/` — see "Routing" below.
- **MapLibre GL** for the basemap (CARTO Positron style, no API key needed)
- **deck.gl** (`@deck.gl/core`, `@deck.gl/layers`, `@deck.gl/mapbox`) for the
  `GeoJsonLayer` choropleth, composited onto the MapLibre map via
  `MapboxOverlay`
- **vue-router** (history mode) — both `vercel.json` and `netlify.toml`
  carry a catch-all rewrite to `index.html` so a direct visit/refresh on
  any route still resolves client-side rather than 404ing on the host.
- **`@turf/boolean-point-in-polygon`** for the address search's IRIS
  lookup (see "What's in HomeView.vue" below) — the one geometry
  operation worth a real, tested library rather than hand-rolled ray
  casting, since MultiPolygons/holes are easy to get subtly wrong.
- **vue-i18n** for FR/EN — see "Bilingual (i18n)" below

## Data

`public/data/` holds a copy of every processed layer the frontend
fetches directly (never recomputed client-side — the frontend only
reads and colors these static files):

```bash
cp ../data/processed/vulnerability_score_iris.geojson public/data/
cp ../data/processed/qpv_boundaries_mgp.geojson public/data/
cp ../data/processed/school_ac_context_arrondissement.geojson public/data/
cp ../data/processed/tree_age_context_arrondissement.geojson public/data/
cp ../data/processed/street_lighting_context_arrondissement.geojson public/data/
cp ../data/processed/associational_density_context_commune.geojson public/data/
```

Re-copy the relevant file(s) after re-running the corresponding script
— `vulnerability_score_iris.geojson` (script 11) is the main choropleth
data; the other five feed `ContextBanner.vue` and the QPV overlay toggle
(all covering the full MGP except the three still-Paris-only context
facts — see `ContextBanner.vue`'s section below).

## Develop

```bash
npm install
npm run dev
```

## Smoke test

`scripts/smoke-test.mjs` checks the production build end to end in a real
browser (Playwright): map data loaded **and drawn** (pixel check against
the score ramp, not just "a canvas exists"), address search → detail
panel → share card, PNG export of both map views, the FR↔EN switch in
both directions, every route by direct access (with the `/ranking`
length derived from the published data), no horizontal scroll at phone
width, and zero browser console errors.

```bash
npm run build && npm run test:smoke                  # local build
SMOKE_BASE_URL=https://underlaid.vercel.app npm run test:smoke   # live site
SMOKE_SOFTWARE_GL=1 npm run test:smoke               # force software WebGL (GPU-less CI)
```

Exits non-zero on any failure. Checks that need the external address API
(BAN) are reported as `SKIP` if it doesn't answer — visibly, never as a
silent pass. Without a GPU, generating the share card takes 5-20 s (the
budget is 60 s); with one, under a second.

## Routing

Four routes, all rendered inside `App.vue`'s shared shell:

- `/` → `views/HomeView.vue` — the map.
- `/methodology` → `views/MethodologyView.vue` — the public, non-technical
  methodology page: why a cumulative count instead of an average, what
  this score does and doesn't measure, what each of the 4 sub-scores is built from, the
  "insufficient data" threshold rule told as the bias-and-fix story it
  actually is (47% vs. 25%, the two examples that dropped from 4/4 to
  3/4), the known caveats (Filosofi masking, ICU coverage, Acceslibre
  sparsity), and the current score distribution — all derived from
  `../SCORING.md` but rewritten for a non-technical reader, in both
  languages via the same i18n JSON files as the rest of the app.
- `/press` → `views/PressKitView.vue` — the one-page press kit (Phase 1):
  a condensed summary (not the full methodology page), with its own
  `@media print` stylesheet so "Print / Save as PDF" produces a clean
  single A4 page with no app chrome.
- `/ranking` → `views/RankingView.vue` — the ~58 IRIS currently at the
  cumulative score's public-ranking ceiling (score 3; capped there
  rather than at score 4, whose 4 occupants — see SCORING.md's Drancy
  example — are still too statistically fragile a sample for a public
  palmarès). Split into two groups by whether the access sub-score
  itself is the worst-quartile factor (see SCORING.md's "A note on
  Group A vs. Group B"), since an identical score doesn't imply
  identical real-world coping capacity. Each row is a full sentence
  built from that IRIS's actual worst-quartile sub-scores via
  `Intl.ListFormat`, following the project's editorial rule: "what the
  city hasn't brought to this neighborhood," never "what this
  neighborhood lacks" — applied only where that framing is actually
  accurate. When the access sub-score's own worst-quartile driver is a
  travel time that's still fast in absolute terms, it's described
  honestly in its own sentence instead ("longer than most of the metro
  area, though still fast in absolute terms") rather than folded into
  the "hasn't brought nearby services" list, which would overstate it.

## What's in HomeView.vue

Page layout: hero (eyebrow badge, gradient heading, one-line pitch) →
grid layout (map card + side panel card) → modals. This replaced an
earlier fullscreen-map-with-floating-overlays layout once the "dark
glass" maquette was provided — the map now lives in a bounded
`.map-frame` card rather than `position: fixed` across the whole
viewport. The topbar (wordmark, nav, EN/FR toggle) and footer live one
level up, in `App.vue`, since they're shared with `/methodology`.

- 5 metrics: cumulative score (0-4) and the 4 sub-score quartiles
  (thermal, pollution, access, housing) — toggled via pill buttons above
  the map, each recoloring the same `GeoJsonLayer`.
- Click an IRIS: the side panel (always present, not an overlay) fills
  in with its quartile-per-sub-score, concrete figures with an "MGP
  median: X" comparison line under the ones a reader most needs
  context for (including population and % artificialized surface, added
  in Phase 5), and a `cumul-box` restating the headline N/4 score.
  Before any click it shows a plain-language prompt instead of an empty
  card. See `../SCORING.md` for what each figure means.
- "Compare to official priority neighborhoods (QPV)" is a toggle, not a
  modal: it adds a second, non-interactive `GeoJsonLayer`
  (`public/data/qpv_boundaries_mgp.geojson`, copied from
  `../data/processed/`, produced by `scripts/14_qpv_boundaries.py`, 162
  QPV zones across the 4 MGP departments as of Phase 5) outlined in
  amber over the choropleth, so a reader can eyeball whether the
  cumulative score's worst spots line up with the neighborhoods France
  already officially recognizes as priority zones. Amber is reused
  deliberately here — it's an identity color everywhere else in the
  palette (never part of the ordinal choropleth ramp), which is exactly
  why it reads as "a different kind of thing" rather than another
  magnitude step.
- "Income vs. exposure ↗" opens a modal with `components/
  IncomeScatter.vue` — step 4's scatter plot. Independent `fetch` of the
  same GeoJSON rather than shared state with the map.
- "Context: heat, mortality, schools, trees, lighting, associations ↗"
  opens `components/ContextBanner.vue` — 6 narrative facts kept out of
  the IRIS score, same reasoning as income: life expectancy, heatwave
  excess mortality, air-conditioned schools, street-tree trunk
  circumference as an age proxy (Phase 3), street-lighting density
  (Phase 3), and RNA associational density (`scripts/18-20`) — the
  latter three server-side-aggregated via `utils/opendatasoft.
  query_records`'s `group_by` parameter rather than downloading raw
  points, each never joined to `code_iris` or scored. As of Phase 5,
  these 6 facts split into two genuinely different grains, both labeled
  explicitly in the UI: life expectancy, schools and trees/lighting stay
  **Paris arrondissement-only** (no MGP-wide source exists for any of
  them), while RNA associational density is now **MGP-wide, commune
  grain** (143 communes) and reports its rate per 1,000 residents as the
  primary figure (using script 21's population data), with per km² kept
  alongside since it surfaces a different, real distortion (the Bois de
  Vincennes/Boulogne park-area caveat) that per-capita alone doesn't
  fix.
- "About: sources of inspiration ↗" opens `components/AboutBanner.vue` —
  citing Adapt'Canicules, EJScreen/CalEnviroScreen/EJNYC and the July 9,
  2026 HCC report directly in the interface, not just in this README.
- **Export map snapshot (PNG)** — Phase 1's press kit: composites the
  MapLibre basemap canvas + deck.gl's choropleth/QPV canvas onto an
  offscreen canvas with a title/legend/date band, then downloads it.
  Captures whatever's currently on screen, so it covers all 5 metrics
  and the QPV overlay with one button rather than a fixed preset scene.
- **Address search** (the #1 sharing lever — people look up their own
  street before anything else) — geocodes via the free government BAN
  API (`api-adresse.data.gouv.fr`,
  no key, CORS-enabled), then finds which IRIS polygon actually contains
  that point via `@turf/boolean-point-in-polygon` (not just the nearest
  centroid), flies the map there, and populates the side panel exactly
  as a click would. As of Phase 5 this resolves anywhere in the full MGP
  (Paris + Hauts-de-Seine/Seine-Saint-Denis/Val-de-Marne), verified in
  browser against a real Boulogne-Billancourt address; an address
  outside that coverage area gets an explicit message rather than
  failing silently.
- **"More vulnerable than N% of MGP neighborhoods"** — shown in the
  side panel for any selected IRIS (click or search), computed from the
  live `cumulative_vulnerability_score` distribution rather than a
  hardcoded table, so it stays correct if the underlying data changes.
- **"Share this neighborhood ↓"** — generates a 1080×1920 (social-story
  format) PNG card client-side (name, arrondissement, big score,
  percentile, 4 sub-score chips, Underlaid watermark) and either opens
  the native share sheet (Web Share API, where supported — with the PNG
  attached as a file) or falls back to a plain download.
- **Heatwave banner** — a dismissible strip reusing the same Santé
  publique France figures already in `ContextBanner.vue` (no duplicated
  data), labeled explicitly as "last known alert; no live feed." A real
  Météo-France vigilance toggle would need an account on
  portail-api.meteofrance.fr, which isn't something to set up on the
  user's behalf for a static, backend-less site — showing the last known
  alert instead is the deliberate fallback for this case.
- Responsive down to ~375px-wide phones (tested via Playwright's device
  emulation, not a physical device): the layout grid collapses to a
  single column below 920px, modals go full-width below 640px, and the
  scatter SVG scrolls horizontally rather than overflowing.

## Visual design (dark glass)

Implements the "maquette E — dark glass moderne" provided by the user:
charcoal background with radial cyan/magenta glows, frosted-glass panels
(`backdrop-filter: blur`), Space Grotesk + IBM Plex Mono (Google Fonts),
gradient wordmark/headline text, pill toggles. Design tokens live in
`src/style.css` (`--bg`, `--panel`, `--cyan`, `--magenta`, `--amber`,
plus the pre-existing semantic aliases `--surface-1`, `--text-primary`,
etc. — remapped to the dark-glass values so every component picked up
the new look without a rewrite).

**The maquette's raw cyan→amber→magenta gradient is not used for the
choropleth.** Run through the `dataviz` skill's ordinal-ramp validator
(`validate_palette.js --ordinal`), it failed on two counts: 176° of hue
spread (not "one hue" for a magnitude ramp) and cyan/amber sitting at
nearly identical lightness (ΔL 0.02 — hard to tell apart for some
colorblind users or in grayscale). Following this project's own rule
that accessibility wins whenever it conflicts with the aesthetic, the
choropleth instead uses a validated single-hue magenta
sequential ramp: `#efc8d7 → #e977a3 → #f11e6f → #c9034f → #99003b`
(same array reused in `App.vue` and `IncomeScatter.vue`). Cyan/amber/
magenta stay as *identity* colors — wordmark, badges, focus rings, the
active-pill gradient — none of which encode an ordered data value, so
they were never subject to the ordinal check in the first place.

Accessibility items from the project's brief, all implemented:
- **Jargon tooltips** (`components/InfoTip.vue`): a focusable "i" button
  with a real `aria-label` (screen readers get the explanation on
  focus, not just sighted hover) next to "IRIS", "quartile" and
  "cumulative score" wherever they first appear.
- **Comparison benchmarks**: city-wide medians computed client-side
  (`medians` in `App.vue`, from an independent fetch of the same
  GeoJSON) and shown under access times and the F/G housing share.
- **Focus-visible**: `outline: 2px solid var(--cyan)` on every
  interactive element, verified via actual Tab-key navigation in a
  headless browser (not just written and assumed).
- **`prefers-reduced-motion`**: one global rule in `style.css` collapses
  every transition/animation duration app-wide, rather than a static
  fallback per component.
- **Screen-reader alternative to the choropleth**: an `aria-live` region
  announcing the selected IRIS's name and score, *plus* a `.sr-only`
  table listing all 2,752 IRIS (worst-first) as real text — a canvas map
  has nothing for a screen reader to read otherwise. Gotcha hit and
  fixed: putting `.sr-only` directly on the `<table>` didn't work —
  some browsers size a table to fit all its rows regardless of an
  explicit `height: 1px` + `overflow: hidden`, which blew up the page to
  ~26,000px tall. Wrapping the table in a plain `<div class="sr-only">`
  fixed it (divs don't have a table's special sizing behavior).
- **Contrast**: checked by computing WCAG contrast ratios directly
  (ink-on-panel, dark-text-on-pill) rather than eyeballing — all clear
  AA (4.5:1), most clear AAA (7:1).

**Known test-environment caveat**: headless Chromium's software WebGL
renderer loses context more reliably on this page than on the previous
(non-glass) layout — root cause not conclusively isolated (ruled out
`backdrop-filter` specifically by disabling it and reproducing anyway).
`refreshLayer()` in `App.vue` now retries once via `requestAnimationFrame`
and logs rather than throwing, so a real browser hitting this rare case
won't crash the UI. Initial render and click-to-select were both verified
working with real data before this was written off as environment noise.

## Bilingual (i18n)

EN/FR toggle at the top of the controls panel, always visible (never a
hidden menu), defaults to English, persisted to `localStorage`
(`underlaid-locale`) — no auto-detection from browser/geolocation, the
visitor's choice always wins.

- `src/i18n/en.json` / `src/i18n/fr.json`: every interface string
  (toggle labels, legend, side panel, scatter, context banner) lives
  here — nothing is hard-coded in a component template. `src/i18n/
  index.js` wires them into `vue-i18n` and exports `setLocale()`.
- Place names (IRIS, arrondissement names) are never translated — they
  come straight from the data (`nom_iris`, `nom_com`) in both locales.
- Numbers/currency go through `Intl.NumberFormat(locale === 'fr' ?
  'fr-FR' : 'en-US', ...)` (see `formatIncome`/`formatDecimal` in
  `App.vue` and `IncomeScatter.vue`) rather than hand-rolled string
  formatting — handles the comma-vs-period decimal separator and
  thousands grouping correctly for both locales automatically.
- The school-AC context notes (from `school_ac_context_arrondissement.
  geojson`) are the one exception to "everything through i18n JSON":
  they're compiled data, not UI copy, so they carry their own `note`
  (English) / `note_fr` (French) pair from `scripts/
  16_school_ac_context.py` — `ContextBanner.vue` picks whichever
  matches the active locale.
- The public-facing `/methodology` and `/press` pages (see "Routing"
  above) absorb the need for a bilingual methodology document — this
  README and `../SCORING.md` themselves stay English-only by design,
  since they're developer docs, not the public-facing material.
