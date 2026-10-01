# Cumulative environmental exposure score — methodology

Computed by `scripts/11_compute_vulnerability_score.py`, run after scripts
01-10, 12, 15, 17, 21, 22 and 24. Output: `data/processed/vulnerability_score_iris.geojson`.

**Phase 5 scope note**: this file originally documented Paris intra-muros
(992 IRIS). It now covers the full Métropole du Grand Paris "Petite
Couronne" — Paris (75) plus Hauts-de-Seine (92), Seine-Saint-Denis (93)
and Val-de-Marne (94) — **2,752 IRIS total**. See "Expanding beyond
Paris" below for what changed and why.

**v0 launch note (September 2026)**: the score now counts **3**
sub-scores — thermal, air/noise pollution, housing — so it ranges
**0-3**. Access to services was removed from the count; its raw figures
are still published as unscored context. See "Why access to services
left the score" below. Sections further down that describe older
corrections keep their "out of 4" figures: they're history, and say so.

## What this score doesn't measure

This is deliberately called a **cumulative environmental exposure
score**, not a "vulnerability score" — an earlier, less precise name
this project used until it was renamed. In climate science, vulnerability
is conventionally decomposed into three distinct components (the IPCC's
own framing, echoed throughout French and international climate-adaptation
literature):

- **Exposure** — is a place physically subject to a hazard (heat,
  pollution, energy-inefficient housing)?
- **Sensitivity** — how much does that exposure actually harm the
  people there (age, health status, pre-existing conditions)?
- **Adaptive capacity** — can people there reduce the harm (the
  financial means to act, a home large enough to find a cooler room,
  the option to leave during a heatwave)?

**The exposure score only measures the first one.** Every sub-score
here — thermal, pollution, housing — is a measure of physical
exposure to a hazard or a deficit in provision. None of it captures
sensitivity (no health, age, or pre-existing-condition data is used
anywhere in this pipeline) or adaptive capacity. Adaptive capacity is
now measured **on its own, separate axis** — see "Adaptive capacity — a
separate axis" below — and crossed with the exposure score on the map's
"Exposure × means" view, but it is never folded into the score itself.
Calling the result "vulnerability" would silently smuggle in a claim
this data was never built to support: that the same score also reflects
who's *least able to cope*, not just who's *most exposed*.

**Why this distinction isn't just semantic.** The income/exposure
scatter (`/` — "Income vs. exposure") is the clearest illustration:
exposure, as measured here, doesn't reliably track income across this
data — every score band spans nearly the whole income range (see
README's step 4 and "Expanding beyond Paris" below for concrete
examples, including several of the metro area's wealthiest addresses
landing in the worst-exposure band). If this were labeled a
"vulnerability score," that finding would read as "wealthy neighborhoods
are just as vulnerable as poor ones" — which isn't a defensible claim,
because a wealthy household facing the exact same physical exposure
(heat, noise, an energy-inefficient apartment) typically has more ways
to cope with it: air conditioning, remote work during a heatwave,
private healthcare, the option to renovate or move. **Two neighborhoods
can have an identical exposure score and a very different real-world
vulnerability**, because adaptive capacity — measured separately, never
inside this score — is what actually separates them. "Exposure score" makes only the claim
this data can back up; "vulnerability score" would make a bigger one it
can't.

**A related, more specific blind spot: this pipeline only ever counts
*public* facilities and provision, never private substitutes for them.**
The thermal sub-score's "cool facilities" indicator counts public pools,
libraries and similar BPE-listed public equipment; the housing
sub-score's thermosensitivity indicator is built from Enedis winter
*heating* consumption, not cooling. Neither one, nor anything else in
this pipeline, counts residential air conditioning, membership in a
private club or pool, or the ability to have groceries and services
delivered rather than walk to them — all private ways to substitute for
exactly the public provision this pipeline measures. This is why a
dense, wealthy neighborhood can cumulate a high exposure score while its
residents are, in practice, considerably better protected than the score
alone suggests: **Notre-Dame des Champs 8** (6th arrondissement, Group C
on `/ranking`) is a direct illustration — its worst-quartile thermal and
housing sub-scores come entirely from public-provision and building-stock
measures, and nothing in this pipeline can see whether its households
have private air conditioning or the means to leave for a second home
during a heatwave.

That last possibility is partly measurable: `pct_secondary_residences`
(INSEE, 2021, `scripts/24_secondary_residences.py`) is the share of each
IRIS's housing stock that's a secondary residence or occasional
dwelling — a direct proxy for the capacity to physically leave during a
heatwave, unlike median income, which only captures that possibility
indirectly. Shown in the map's IRIS detail panel next to median income,
**it is never merged into any sub-score or the cumulative score** — it
is one of the three indicators of the separate adaptive-capacity axis
(see below) — adding it as a scored indicator
would just relabel the same "vulnerability, not exposure" conflation
this whole section exists to avoid. `P21_RSECOCC` (the INSEE source
variable) counts secondary residences and occasional/seasonal dwellings
together; IRIS-level data doesn't separate the two, so treat the figure
as a proxy for both combined, not secondary residences alone. Rates are
suppressed (shown as no data) below 20 total housing units, the same
sparse-denominator guard already applied to `cool_facility_deficit`.

**What this means in practice on `/ranking`:** the page's own Group A /
Group B / Group C split (see "A note on Group A vs. Group B vs. Group
C" further down) exists specifically so this distinction isn't lost in
a single ranked list — Group A (genuinely under-served), Group C (a
dense-fabric neighborhood whose access sub-score is nominally
worst-quartile too, but only because a fast time still ranks last
metro-wide), and Group B (dense/older housing stock, access genuinely
not an issue) can land at the identical cumulative score while facing
very different odds of actually coping with it.

## Adaptive capacity — a separate axis

`scripts/25_overcrowding.py`, `scripts/26_adaptive_capacity.py` →
`adaptive_capacity_iris.json`, a **separate file** from the exposure
score. Nothing in it feeds back into `cumulative_vulnerability_score`
(`tests/test_pipeline.py::test_capacity_never_leaks_into_the_exposure_score`
guards this).

**Why a separate axis rather than a 5th sub-score.** Folding means into
the score would turn a defensible count of exposures into an opaque
blend, and would hide the very finding it's meant to qualify: exposure
doesn't track income cleanly. Kept apart, the two axes can be crossed
honestly — the same approach as CalEnviroScreen's "pollution burden ×
population characteristics", except that Underlaid shows the cross as a
map instead of multiplying the two into one number. Closest precedents at
this scale: Kasten et al., Strasbourg, *Climatologie* 20 (2023), an
exposure/sensitivity/adaptation index at IRIS level from INSEE proxies;
PACTES Chaleur (2023, commune level).

**Indicators** (INSEE 2021 — the same vintage as Filosofi and the
population counts — all at IRIS level):

| Indicator | Source variable | Direction | Masked (of 2,752) |
|---|---|---|---|
| Median disposable income | Filosofi `DISP_MED21` | higher = more means | 223 (8.1%) |
| Overcrowded homes (INSEE definition, one-person studios excluded) | RP logement `C21_RP_HSTU1P_SUROCC / C21_RP_HSTU1P` | higher = fewer means | 72 (2.6%) |
| Secondary residences & occasional dwellings | RP logement `P21_RSECOCC / P21_LOG` | higher = more means (option to leave) | 64 (2.3%) |

Rates are suppressed below 20 dwellings (same floor as elsewhere).

**Construction.** Each indicator is turned into a percentile rank (0-1,
oriented so higher = more means); the index is their plain mean. Ranks,
not z-scores, because two of the three are heavily skewed (overcrowding:
skew 1.7, max |z| 11; secondary residences: skew 4.1, max |z| 14) — the
same sparse-data signature that distorted `access_time` and
`cool_facility_deficit`; a rank can't let one extreme value drag the
index. The index is computed only where median income is published (the
anchor) and at least 2 of 3 indicators are present: **2,529 IRIS
(91.9%)**. The 223 others (2.9% of the population — mostly woods, parks,
business parks and worker hostels, where INSEE masks income for
statistical secrecy) get no index and appear as "not published" on the
map; they are never imputed. They're spread across exposure classes in
the same proportions as all IRIS (checked by a test), so leaving them
out doesn't hide one part of the picture. This anchoring also drops the
extreme overcrowding rates (up to 100%), all of which come from such
non-standard IRIS.

**Classes.** Means: tertiles of the index (lowest / middle / highest
third of the metro area). Exposure: the cumulative score grouped as 0 /
1 / 2+ — scores 3 and 4 together are only 2.2% of IRIS, too few for a
class of their own.

**Candidates measured and rejected.** Poverty rate (Spearman −0.91 with
median income and masked on exactly the same IRIS — a duplicate that
would double-weight income); share of social housing (ambiguous: the
landlord, not the household, can act on the building); households
without a car (in dense Paris, a way of life rather than a lack of
means). Home ownership (capacity to insulate or install shutters) was
considered and left out: it adds little to the grid and its meaning is
muddy in Paris, where many well-off households rent.

**Distribution (3-sub-score exposure, 2,529 IRIS with an index):**

| | means: lowest third | middle third | highest third |
|---|---|---|---|
| **exposure 0** | 423 | 405 | 216 |
| **exposure 1** | 373 | 344 | 393 |
| **exposure 2+** | 47 | 94 | 234 |

"2+" means 2 or 3 of the 3 sub-scores in their worst quartile.

**1. Two profiles, not one scale.** Correlation of the capacity index
with each sub-score: housing +0.66, thermal +0.37, pollution −0.30.
Highly exposed IRIS (2+) with the highest means are mostly in Paris (191
of 234) and stack heat + housing (worst quartile in 92% / 94% of them) —
dense, older building stock. Those with the lowest means (47, about
126,000 residents) are mostly in Seine-Saint-Denis (27) and Val-de-Marne
(13) and stack heat + air/noise pollution (87% / 89%).

**2. The link between exposure and means is weak.** Spearman(capacity
index, exposure score) = **+0.28** — slightly positive only because of
dense, older central Paris (+0.39 within Paris); within the inner-suburb
departments it's near zero (92: +0.06, 93: −0.08, 94: +0.09). Always
state it with that explanation in public copy — never as "the well-off
are more exposed", which the data doesn't show outside Paris.

**3. Where high exposure and low means meet, it's concentrated.** In
Seine-Saint-Denis, 79% of the highly exposed IRIS are in the metro
area's lowest third of means; in Paris, 2% (92: 2%, 94: 25%).

**How this crossing changed the exposure score itself.** The first
version of this grid was computed with the former 4-sub-score exposure
score, and its "2+ / lowest means" cell turned out to be largely built
in: the access sub-score included school social position (IPS), which
follows household income by construction (capacity vs access: −0.52).
That finding started the audit that took access out of the score — see
"Why access to services left the score" below. With the 3-sub-score
score, the cell has no such mechanical overlap: none of the three
remaining sub-scores uses a population characteristic.

**What this axis doesn't measure.** It measures *means*, not what
households actually do with them: nothing here says whether a home has
air conditioning, whether someone can take time off during a heatwave,
or anything about health or age (sensitivity, still unmeasured).
`P21_RSECOCC` mixes secondary residences and occasional dwellings. The
index is relative (thirds of this metro area), not an absolute
threshold of "enough" means.

**Map palette.** A 3×3 grid, pink for exposure (the brand magenta at its
end), blue for *lack* of means, darkest = stacked exposures and lowest
means. Checked with the dataviz skill's `validate_palette.js`
(`--ordinal --mode dark --surface #080A0F`): every row and column passes
the ordered-ramp checks; neighbouring cells stay ≥ 8.2 ΔE apart under
protan/deutan simulation and ≥ 12.1 in normal vision — better than the
existing 5-step exposure ramp's own adjacent figures (7.8 / 9.3). Nine
ordered cells can't all clear the 15 ΔE normal-vision floor meant for
categorical palettes, so the cell is also always named in words (legend
tooltips, detail panel, screen-reader table).

## Why a "count of worst quartiles" instead of a weighted average

A single weighted-average score would smooth out exactly the phenomenon
this project exists to show: the same neighborhoods stacking up several
*distinct* exposures at once. A high average can hide a zone with
one severe problem and three mediocre scores just as easily as a zone
with four moderately-bad ones — the two situations are not equivalent,
but a mean treats them the same. Counting how many sub-scores land in
their own worst quartile keeps that distinction visible.

## The 3 sub-scores

Every indicator below is transformed so that **higher = more exposed**
(protective indicators — cool spots, canopy, social position — are sign-
flipped). Each is standardized to a z-score (`(x - mean) / std`) before
being combined, so indicators on different units/scales weigh in
equally.

| Sub-score | Indicators (equal weight, simple mean of z-scores) | Source |
|---|---|---|
| **Thermal** | `hvi` (heat vulnerability index, Sat4BDNB) · `-count(cool spots within 400m of IRIS centroid) per 1,000 residents` · `-% of IRIS area covered by "cool" green space` · `% of IRIS area that's artificialized/sealed (MOS land use)` | scripts 02, 03, 04, 21, 22 |
| **Pollution** | area-weighted mean air-noise co-exposure class (1-9 scale) | script 05 |
| **Housing** | % of sampled DPE certificates rated F or G ("passoire thermique") · residential electrical thermosensitivity (`part_thermosensible`, Enedis) | scripts 10, 17 |

Each sub-score is the **unweighted mean** of its (standardized) indicator
z-scores, skipping indicators missing for a given IRIS. Weights are equal
by design — there's no principled basis yet to weigh one indicator over
another; revisit this once the tool has real user feedback.

Access to services (scripts 07, 09, 12, 15 — travel time, school IPS,
wheelchair-accessible entrances, OSM footway density) was a 4th
sub-score until the v0 launch. Its raw figures are still in the output,
shown as unscored context in the map's detail panel — see the next
section for why.

## Why access to services left the score

Found while crossing the score with the adaptive-capacity axis (see
above): the access sub-score moved with residents' means (Spearman
−0.52), and each of its four indicators turned out to fail on its own.
Every alternative was simulated on the full data before deciding,
without touching the published score.

**The four indicators, one by one.**
- **School IPS (social position index)** describes the population, not
  an exposure — it follows household income by construction. It was the
  access driver for most of the IRIS whose "high exposure / low means"
  profile relied on access.
- **Acceslibre wheelchair-accessible entrances** are crowdsourced and
  missing for 1,064 of 2,752 IRIS (39%). In the 4-sub-score version,
  IRIS with 3 of the 4 access indicators landed in the worst access
  quartile 29.6% of the time vs 17.6% with all 4 (ratio 1.68) — the same
  sparse-data signature as the original 47%-vs-25% bias. The overall
  25/25/25/25 quartile check couldn't see it; it only shows when IRIS
  are grouped by number of available indicators (now a standing test:
  `test_worst_quartile_share_does_not_depend_on_indicator_count`).
  Dropping IPS alone made it worse (min-indicator rule falls to 2 of 3,
  545 more IRIS scored, 44.5% vs 13.4% in the worst quartile).
- **OSM footway density** mostly measures mapping practice. Script 15
  counts `highway=footway` ways only; sidewalks tagged on the street
  (`sidewalk=both|left|right`) aren't counted. Share of footway ways that
  are separately-drawn sidewalks: 75: 53%, 92: 33%, 94: 33%, 93: 17%. At
  equal population density (log-log fit), Paris has 2.4× the expected
  footway density and Seine-Saint-Denis 0.4×; within 10,000-25,000
  residents/km², medians are 39,800 m/km² (75) vs 6,600 (93). Checked on
  IGN orthophotos with the OSM ways overlaid: Clichy "Klock" (53,000
  residents/km², sidewalks plainly visible, 56 streets tagged
  `sidewalk=*`) counts 52 m/km²; Aubervilliers "Firmin Gemier" and Bondy
  "Suzanne Buisson" likewise; Paris 11e "Saint-Ambroise 4", same urban
  form, 165,000 m/km².
- **Access time** sits at its floor: 98% of IRIS are at 1.5 min or less
  on average (18 distinct rounded values). It barely discriminates, so
  any access score built on it is effectively driven by the other
  indicators.

**Options simulated** (distribution 0-4 or 0-3; "2+/low" = exposure 2+
with the lowest third of means):

| Option | Distribution | 2+/low | Verdict |
|---|---|---|---|
| Before (4 sub-scores) | 874 / 1,230 / 586 / 58 / 4 | partly built on IPS | income inside the exposure score |
| Access without IPS (min 2/3) | 804 / 1,250 / 620 / 73 / 5 | 164 | sparse-data bias (44.5% vs 13.4%) |
| Access without IPS (min 3/3) | 956 / 1,205 / 528 / 60 / 3 | 125 | access undefined for 1,120 IRIS (41%) |
| C: access = time + footways | 811 / 1,254 / 605 / 77 / 5 | 158 | access ≈ footway density (R² 0.73), a mapping artefact |
| **D: access out of the count** | **1,144 / 1,202 / 375 / 31** | **45** | **adopted** |

In C, 20 of the 30 IRIS entering scores 3-4 were IRIS previously
excluded for insufficient access data. In D, 31 IRIS leave scores 3-4
(access was the 3rd category for each: 17 via access time, 8 via
footways, 6 via IPS), none enter, and the four former 4/4 IRIS become
3/3.

**Coming back.** Access can return once an indicator passes both the
global and the per-indicator-count quartile checks — candidates and
their feasibility are listed in CLAUDE.md (Phase 7, "Retour de l'accès
dans le score"): DREES APL, a home-made 2SFCA at IRIS level, footway
counting that includes street-tagged sidewalks.

Median income (`08_income_filosofi.py`) is **not** part of the score. It
is carried through to the output for step 4 (correlation between income
and cumulative exposure), on purpose — folding it into the score would
make that correlation circular. It's also one of the three
indicators of the separate adaptive-capacity axis — see "Adaptive
capacity — a separate axis" below.

## From sub-score to quartile

Each sub-score's z-score mean is converted to a quartile (1 = best 25%,
4 = worst 25%) via **percentile rank**, not `pandas.qcut` directly:
several indicators (notably access time — most of dense inner-Paris
sits at "1 minute to the nearest equipment") have enough tied values to
make qcut's bin edges collide. Percentile rank handles ties by averaging
their rank instead of erroring out.

## Minimum-indicator threshold ("insufficient_data")

**A sub-score is only computed if a strict majority of its indicators
have data for that IRIS.** Concretely: `floor(n_indicators / 2) + 1` —
**3 of 4 for thermal** (raised from 2/3 in Phase 5 when artificialization
became its 4th indicator), 3 of 4 for access, 1 of 1 for pollution (a
single-indicator sub-score — can't require more than what exists), 2 of
2 for housing (both DPE and Enedis are required, not just one — see
"Electrical thermosensitivity" below). Below threshold, the sub-score,
and its quartile, are both null and its status is set to
`"insufficient_data"` — explicitly excluded from the cumulative score,
not silently treated as "not exposed" (quartile 1-3) or averaged over
whatever scraps of data happened to be there.

**Why this exists — a real bias, measured, not assumed.** Investigating
why Porte Dauphine 11 and Madeleine 2 (Paris-intra-muros-era examples)
scored 4/4, their "access" sub-score turned out to be built from only
1-2 of its 4 indicators (no school, no documented PMR entry nearby —
both are small, non-residential IRIS), while their raw access *times*
were actually excellent (1.0-1.35 minutes). Checked systematically
across all 992 Paris IRIS at the time, before this fix:

> Among the 89 IRIS whose access sub-score relied on a single indicator,
> **47% landed in the worst quartile — nearly double the 25% you'd
> expect from chance.** Sparse-data IRIS were being penalized for
> *lacking data*, not for having worse access.

After adding the threshold (Paris-only numbers, at the time): **125 of
992 IRIS lost their access sub-score to `insufficient_data`** (867
remained "ok"); **26 lost their housing sub-score** (966 "ok"); thermal
and pollution were unaffected. Quartile splits among the remaining "ok"
IRIS moved to a clean 25/25/25/25 on all four sub-scores — the skew was
gone, not just relabeled.

**Re-verified at MGP scale (Phase 5).** Expanding to 2,752 IRIS —
2.8x the population, and far more heterogeneous (dense Paris core plus
inner-suburb communes of every density and land use) — is exactly the
kind of change that could quietly reintroduce a similar bias, so the
same check was rerun rather than assumed to still hold. Current
sub-score completeness:

| Sub-score | OK | insufficient_data | Min. indicators required |
|---|---|---|---|
| Thermal | 2,750 / 2,752 | 2 | 3 / 4 |
| Pollution | 2,752 / 2,752 | 0 | 1 / 1 |
| Access | 2,188 / 2,752 | 564 | 3 / 4 |
| Housing | 2,676 / 2,752 | 76 | 2 / 2 |

(Thermal's count reflects the `cool_facility_deficit` fix further below
— 1 additional IRIS below `MIN_POPULATION_FOR_RATE` lost its 4th
thermal indicator, still comfortably above the 3/4 threshold.)

And the quartile balance among each sub-score's "ok" IRIS, at the full
MGP scale:

| Sub-score | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| Thermal | 25.0% | 25.0% | 25.0% | 25.0% |
| Pollution | 25.0% | 25.0% | 25.0% | 25.0% |
| Access | 25.0% | 25.0% | 25.0% | 25.0% |
| Housing | 25.0% | 25.0% | 25.0% | 25.0% |

A clean 25/25/25/25 split on all four, same as the Paris-only
re-verification. The threshold rule generalizes; it wasn't tuned to one
city's particular data gaps.

## Access time's compressed distribution — found, and corrected

The minimum-indicator threshold above protects against a sub-score being
computed from too *few* indicators. It does **not** protect against a
different failure mode: one *available* indicator's z-score being
unreliable because its underlying distribution isn't roughly normal.
`access_time` turned out to be exactly this case — audited manually
(same rigor as Porte Dauphine/Madeleine and Drancy) after two IRIS in
the score-3 ranking, **Val de Grâce 6** (Paris 5e) and
**Champs-Élysées 2** (Paris 8e), turned out to have their access
sub-score landing in the worst quartile mainly *because of*
`access_time`, despite raw times of 1.6 and 1.2 minutes respectively —
fast by any human reading. Widening the audit to **Sorbonne 3, Sorbonne
4, and École Militaire 5** (also fast-looking, raised as candidates for
the same bias) found the opposite, useful result: all three genuinely
have `subscore_access_quartile` outside the worst quartile (2, 1 and 1)
— they were never miscategorized, which helped confirm the bias is real
and specific rather than something a suspicious eye sees everywhere.

**Why this happens.** Most of the metro area is tied at or near the
"1 minute" floor (25th percentile = 1.00, median = 1.00, 75th
percentile = 1.08), so `access_time`'s raw standard deviation is tiny
(0.15). A value like 1.57 minutes — objectively fast — sits at the
95.8th percentile of this compressed distribution, giving a raw z-score
of **+3.38**: an extreme outlier in relative terms despite being a
trivial absolute difference (a few tens of seconds). `access_time`'s
worst raw z-score anywhere in the dataset was **+15.30** — by a wide
margin the single most extreme standardized value produced by *any*
indicator in this pipeline (the next-worst, `housing_energy_poverty`,
peaks at 7.87; most stay under 5). Val de Grâce 6's other two available
access indicators (`school_segregation` is missing — no school in this
small IRIS; `pedestrian_path_deficit` is strongly *favorable*,
z = -1.82) weren't enough to pull the mean of the 3 available z-scores
back out of the worst quartile.

**Checked every other indicator for the same profile before fixing
just this one.** A biased fix that only patches the example already
found isn't good enough — the same floor/ceiling-clustering pathology
could exist elsewhere, unnoticed. Computed, for all 11 raw indicators
across the 4 sub-scores: share of values tied at the single most common
value, and the most extreme raw z-score produced anywhere in the
dataset.

| Indicator | Share at mode | Worst raw \|z\| |
|---|---|---|
| `access_time` | 49.9% | **15.30** |
| `mobility_accessibility_deficit` | 77.5% | 4.79 |
| `cool_facility_deficit` | 50.4% | 47.90 |
| `canopy_deficit` | 40.8% | 8.37 |
| `pedestrian_path_deficit` | 0.4% | 5.87 |
| `housing_energy_poverty` | 2.9% | 7.87 |
| `artificialization_deficit` | 8.1% | 4.05 |
| `electric_thermosensitivity` | 0.2% | 3.76 |
| `air_noise_class` | 0.5% | 3.65 |
| `school_segregation` | 0.3% | 2.18 |
| `heat_icu` | 5.4% | 2.77 |

`access_time` is the clear, severe outlier: both the mechanism (a hard
physical floor — you cannot travel for less than ~1 minute — with over
half the metro area pinned to it) and the resulting magnitude (a raw
z-score five times more extreme than the runner-up) are qualitatively
different from the rest. `mobility_accessibility_deficit` also has a
large share at its mode (77.5% of documented ERPs report exactly 0%
PMR-accessible), but its worst z stays under 5 — the point-mass sits
close to the mean rather than far out on a long tail, so it dilutes
this indicator's discriminating power without producing false extreme
classifications. `cool_facility_deficit` and `canopy_deficit` do
produce some large |z| values, but from a **different mechanism** — a
long right tail on a rate (a handful of IRIS with a tiny population
denominator or unusually high raw count), not a hard floor — and
correcting that would need a different technique (winsorizing or
capping, not a rank transform) plus its own manual audit, not a fix
piggybacked on this one. **Flagged here as a follow-up, not silently
left undocumented, but not fixed in this pass.**

**The fix applied**: `access_time` is now standardized by percentile
rank rather than raw z-score, rescaled by √12 (the reciprocal of a
uniform(0,1) distribution's standard deviation) so it sits on a
comparable spread to the genuinely normal-ish indicators it's averaged
against — otherwise a rank-transformed indicator would be systematically
diluted relative to its peers. This is the exact same reasoning already
applied one step downstream, when `quartile_from_rank()` converts a
sub-score's z-score mean into a quartile via percentile rank instead of
`pandas.qcut`, for the identical underlying reason (too many tied
values for a normal-distribution assumption to hold) — this fix just
applies that logic one level earlier, to the raw indicator itself,
rather than only at the final quartile-conversion step.

**Verified after the fix**:
- Quartile balance across all 4 sub-scores stayed a clean 25/25/25/25
  among "ok" IRIS — the fix didn't introduce a new imbalance.
- **Val de Grâce 6 moved out of the worst access quartile** (Q4 → Q3),
  and its cumulative score dropped from 3 to 2 as a direct result —
  correctly, since access was the only genuinely questionable factor in
  its profile.
- **Champs-Élysées 2 stayed in the worst access quartile** (subscore
  moved from 0.424 to 0.575) — its own `pedestrian_path_deficit` is
  close to neutral (unlike Val de Grâce 6's strongly favorable one), so
  even a correctly-scaled `access_time` isn't offset by anything else
  available. This is a legitimate outcome of the corrected formula, not
  a sign the fix didn't work.
- Re-running the full-ranking audit (all IRIS at score ≥ 3): the count
  of access-worst-quartile IRIS with a raw `access_time` ≤ 2 minutes
  went from 22 of 22 (100%, pre-fix) to **23 of 23 (still 100%,
  post-fix)** — expected, not a failure of the fix. The rank transform
  removes *extreme, disproportionate* distortion (the 15.3 case), it
  doesn't and can't manufacture variance that isn't there: at this
  density, access genuinely is fast almost everywhere, so *some*
  IRIS will always rank in the bottom quartile on this one indicator
  by construction, however correctly it's standardized. That residual
  is exactly what the `/ranking` page's driver-specific wording (below)
  exists to communicate honestly, rather than something a formula
  change alone can eliminate.
- Two IRIS dropped out of the score-3 ranking entirely (Val de Grâce 6;
  **Iris 2**, Bagnolet — a ripple effect of re-ranking the whole
  dataset, not itself driven by `access_time`) and three newly entered
  (**Montfort**, Aubervilliers, income €16,430, driven by
  `pedestrian_path_deficit`; **Charles Laffitte 2**, Neuilly-sur-Seine,
  and **Notre-Dame des Champs 8**, Paris 6e — both wealthy, both driven
  by `access_time`, both plausible continuations of the Group B pattern
  already documented above). All five were checked by hand; none looks
  like a new artifact.

**Distribution after the fix** (superseding the numbers quoted
elsewhere in this document before this section): 0 → 908 (33.0%),
1 → 1,146 (41.6%), 2 → 649 (23.6%), 3 → 48 (1.7%), 4 → 1 (0.04%,
Drancy's Économie 1, unaffected by this fix and still the only 4/4).
**This snapshot was itself superseded shortly after** by the
`cool_facility_deficit` fix below — see "Current distribution" at the
end of this document for the authoritative, current numbers (score ≥ 3
is 62 IRIS as of that fix, not 49).

**The `/ranking` page's sentence generator was also corrected**,
independently of the numeric fix, because the numeric fix alone doesn't
remove the residual "genuinely borderline" cases described above.
`access_primary_driver` (which of the 4 access indicators has the
highest z-score for a given "ok" IRIS, kept in the output GeoJSON as a
transparency layer) now drives which phrase the ranking sentence uses —
naming school segregation, sparse pedestrian infrastructure, or travel
time specifically, rather than a single generic "nearby services"
phrase that a full audit found was actively misleading for most rows
(only 2 of the 22 access-flagged IRIS were actually about school-adjacent
segregation being irrelevant; the rest split across three different real
causes). Whenever `access_time` is still the dominant driver and its raw
value is ≤ 2.0 minutes (the cutoff covering 94% of `access_time`-driven
cases in the audit), an explicit caveat is appended: "access itself is
fast here in absolute terms (X min) — this sub-score reflects being
slower than most of the rest of the metro area, not an actual lack of
nearby services."

## cool_facility_deficit's small-population inflation — found, and corrected

The systematic check that caught `access_time` also flagged
`cool_facility_deficit` as having the single most extreme raw z-score
of any indicator in the pipeline (**-47.90**, nearly 3x worse than
`access_time`'s own pre-fix worst case of +15.30). Audited before
touching anything, per this project's standing practice of confirming a
bias by hand rather than patching from a summary statistic alone.

**What the audit found.** The two most extreme rows: **Buttes Chaumont**
(Paris 19e), population 3.3, with 2 cool facilities within 400m, giving
a rate of ~603 facilities per 1,000 residents; and **Jardin des
Plantes** (Paris 5e), population 4.0, 1 facility, ~250 per 1,000. Both
are exactly what their names suggest — a park and a botanical garden —
confirmed by checking every IRIS with a nonzero-but-tiny population: all
15 of them (population between 1.6 and 47) are named parks, a cemetery,
a wholesale market, a forest, or an industrial zone (`Père Lachaise 17`,
`Bois de Notre-Dame`, `Marché d'Intérêt National`, `Silic`, etc.) — not
an undercounted residential population.

**Why this is a different mechanism from `access_time`, and why that
matters for the fix.** `access_time` is floor-clustered: half the
metro area is physically unable to score better than "~1 minute", a
hard lower bound. `cool_facility_deficit` has no such floor — instead,
dividing a small integer count (0-6 facilities) by a population that
can be arbitrarily close to zero produces an unbounded rate, a
classic small-denominator inflation. The existing `population == 0`
guard (already in place to avoid a division by zero) caught the most
degenerate case but not this one — a population of 3 or 4 isn't zero,
so it slipped through, while being just as meaningless a denominator
for a "per 1,000 residents" rate.

**Why a population floor alone doesn't fully fix it.** Raising the
population threshold and recomputing the z-scores shows the standard
deviation is dominated by whichever few points remain most extreme —
excluding the worst 15 shrinks the column's std enough that the
*next*-most-extreme points immediately become new outliers by the same
measure (empirically: nulling everything under 200 population still
left a worst raw z of 25.35, barely better than the unfixed 47.90).
Chasing the tail this way doesn't converge. This is exactly the
scenario the project's own choice of *winsorizing or capping* (rather
than a rank transform, which suits `access_time`'s floor-clustering but
not this heavy right tail) was meant for.

**The fix applied, in two parts**:
1. `MIN_POPULATION_FOR_RATE = 50` — below this many residents, a
   "per-1,000-inhabitants" rate is treated as **not a real neighborhood
   population** and the indicator is left null (`insufficient_data`
   territory for that IRIS, same principle as `population == 0` already
   used, just with a defensible floor instead of an exact-zero check).
   This removes the 15 confirmed park/cemetery/market/industrial IRIS
   from the computation entirely, rather than letting them contribute a
   fabricated rate.
2. **Winsorizing** (capping, not deleting) the resulting rate at its
   own 3rd percentile — chosen empirically as the point where the
   worst remaining raw z-score drops under 3, matching the rest of this
   pipeline's well-behaved indicators. Values more favorable than the
   3rd-percentile cutoff are clipped to that cutoff rather than left
   able to blow out the z-score for everyone else.

**Verified after the fix**:
- Worst raw z-score for this indicator: **-47.90 → -2.78** (below the
  |z| > 3 threshold every other indicator in this pipeline already
  clears, except the still-flagged-as-follow-up `canopy_deficit` and
  `housing_energy_poverty`, see "Known caveats").
- Quartile balance across all 4 sub-scores stayed a clean 25/25/25/25
  among "ok" IRIS.
- **This fix moved the distribution more than `access_time`'s did** —
  expected, since it wasn't just correcting a couple of outlier rows'
  own quartile, it was restoring `cool_facility_deficit`'s actual
  discriminating power for *everyone else*: a few wild outliers had
  been inflating the whole column's standard deviation, which
  compressed every other IRIS's z-score toward zero and made the
  (very real) difference between "0 facilities nearby" and "1-2
  facilities nearby" nearly invisible to the composite thermal score.
  With the outliers capped, that real difference matters again.
- **Score 4/4 grew from 1 IRIS to 4**: Économie 1 (Drancy, unchanged)
  plus three newly-qualifying IRIS — **Les Parclairs** (Le
  Perreux-sur-Marne), **Président Wilson** (Villeneuve-Saint-Georges),
  and **Nonneville 3** (Aulnay-sous-Bois). All four were checked by
  hand: normally-sized residential populations (2,000-2,600, not tiny),
  0-1 cool facilities within 400m, nearly 0% green cover, 77-100%
  artificialized surface, HVI 15.0-17.0 — a fully coherent, unambiguous
  profile, not an artifact of the fix (their own `cool_spots_within_400m`
  values are 0 or 1, an entirely ordinary, non-extreme input; what
  changed is that the composite thermal score can now register that
  input's real signal instead of it being drowned out by outliers
  elsewhere in the same column).
- Score ≥ 3 total grew from 49 to **62 IRIS**. Spot-checked a sample of
  the newly-qualifying rows, including the two smallest populations in
  the list (`Gare 32`, Paris 13e, population 185, 96.3% artificialized,
  0% green, adjacent to a rail yard; `Parcexpo`, Le Bourget, population
  116, 87.0% artificialized, an exhibition-park site) — both plausible,
  genuinely low-facility/high-artificialization zones rather than a new
  sparse-data artifact.

**Distribution after this fix** (superseding the `access_time`-only
numbers quoted earlier in this document): 0 → 874 (31.8%), 1 → 1,230
(44.7%), 2 → 586 (21.3%), 3 → 58 (2.1%), 4 → 4 (0.1%).

**A note on the public ranking's score-4 cap.** The `/ranking` page
caps its public list at score 3, reasoning that n=1 (or n=2, in the
Paris-only era) was too fragile a sample. n=4 changes that calculus
somewhat, but the cap-at-3 policy itself hasn't been revisited as part
of this fix — it's a separate editorial decision, not a direct
consequence of correcting this indicator's standardization, and is
noted here rather than changed silently.

**A note on Group A vs. Group B vs. Group C.** The manual audit of the
access sub-score (see "Access time's compressed distribution" above)
first split the `/ranking` page's list into two groups by whether
access itself is the worst-quartile factor: Group A (a genuine
shortfall in local conditions) and Group B (dense/older housing stock
with decent-to-excellent access). This split matters for exactly the
reason explained in "What this score doesn't measure" above: an
identical cumulative *exposure* score doesn't imply identical
real-world *vulnerability*.

A second, full pass over all 31 access-worst-quartile IRIS — prompted
by re-reading the group rather than a single flagged example — found
that the two-group split still mischaracterized most of Group A: 17 of
the 31 have `access_time` as their access sub-score's sole driver *and*
a fast-in-absolute-terms time (<=2.0 min, the same threshold documented
above), meaning their "under-served" label was a purely relative,
metro-wide artifact, not a real local shortfall. Only 14 of the
original 31 have a genuine driver — school segregation, sparse
pedestrian infrastructure, or an access_time that's actually slow. The
17 fast-artifact rows (e.g. Notre-Dame des Champs 8, 6th arrondissement)
were moved into a new **Group C**: their real story is the same
dense/older-fabric pattern as Group B, just with access nominally
flagged as worst-quartile too. Splitting the group, rather than only
softening each affected row's sentence within a single Group A, is what
keeps the *group-level* framing ("residents here have less access to
nearby services" — worded since the v0 launch as a measured gap in equal
access to public services, never "the city hasn't brought X": the
perimeter spans 143 communes and many actors, and no institution is
named as the cause) honest — a per-row caveat buried after a group-level claim had
already been tried once (see "Access time's compressed distribution")
and still let a reader who stops at the group heading walk away with
the wrong impression.

The three groups' wording says so explicitly — Group A's copy names a
genuine service shortfall consistent with limited means to compensate
for it; Group C's copy states plainly that access is fast in absolute
terms and the real driver is the same dense-fabric pattern as Group B;
Group B's copy states plainly that access isn't the issue at all and
several of its neighborhoods are among the metro area's wealthiest, so
their being exposed shouldn't be read as evidence they lack the means
to cope with it. None of the three groups' phrasing implies they're
equally vulnerable — only that they're comparably *exposed*, which is a
narrower and more defensible claim.

## Cumulative score

```
cumulative_vulnerability_score = count of sub-scores where quartile == 4
```

Range 0-3 (0-4 before the v0 launch, when access was still counted). An
IRIS missing data for every sub-score gets a null cumulative score
rather than being silently treated as "not exposed".
`n_subscores_evaluated` records how many of the 3 sub-scores had data
for that IRIS, for transparency.

## Electrical thermosensitivity (housing's second indicator, Phase 3)

`pct_thermosensitive` (script 17) is Enedis' `part_thermosensible`: the
share of a zone's *residential* electricity consumption that swings with
outdoor temperature (winter heating load, specifically — Enedis doesn't
publish a summer-cooling equivalent). A zone with high thermosensitivity
has electricity use that responds sharply to cold, which points at
poorly-insulated, electric-heating-dependent housing — the same building
envelope that's also expensive to keep cool in summer, just measured
from the winter side because that's the data that exists. Paired with
DPE F/G share, it answers a sharper question than DPE alone: not just
"is this housing stock poorly insulated" but "is it also stuck on
electric heating with no cheap way to compensate for heat either."

Both indicators are **required** (see "Minimum-indicator threshold"
above) — a deliberate tightening, not a bug. Enedis itself already
enforces a ≥10-active-site privacy floor per zone, so no additional
sample-size masking was layered on top of what the source does.

## Population-normalized cool-facility count (Phase 5)

`cool_facility_deficit` used to be a raw count of cool facilities
(pools, museums, libraries) within 400m of an IRIS's centroid. At MGP
scale, with communes of very different densities sitting side by side,
a raw count would make a bigger or denser IRIS look better-served purely
by having more people nearby — not because it actually has more cool
facilities *per resident*. It's now **a rate per 1,000 residents**,
using `population_iris.geojson` (script 21, INSEE Recensement de la
population 2021 — same vintage as Filosofi's income data, for
consistency). IRIS with zero population (non-residential — a park, a
transport interchange) get a null rate rather than a division-by-zero
or a misleading 0, the same `insufficient_data`-not-fabricated principle
used everywhere else in this pipeline.

This is a genuine, repeated pattern in this project: population data
also normalized the raw BPE facility counts used as inputs upstream, and
retroactively normalized the RNA associational-density context layer
(script 20) from "per km²" to "per 1,000 inhabitants" — each change
moves the distribution again, on purpose, because a raw count was
quietly measuring density of *people* as much as density of *service*.

## Artificialization / sealed surface (thermal's 4th indicator, Phase 5)

`pct_artificialized` (script 22) is the share of an IRIS's surface
classified as built or paved ground, from IDF's MOS (Mode d'Occupation
du Sol) land-use survey — **54 of its 79 categories** count as
artificialized: housing (28-35), economic/industrial/utility (36-54),
covered sports facilities (55-59), institutional equipment (60-72),
transport infrastructure (73-79), plus tennis courts (18) and paved
esplanades/squares (24). Forests, natural/agricultural land, parks and
green space, water and vegetated leisure areas, cemeteries and vacant
land are **not** counted as artificialized.

**Why MOS, not IGN's official OCS GE.** IGN's "Occupation du Sol à
Grande Échelle" (OCS GE) is the closest thing to a national, legally-
grounded artificialization dataset — but its public-facing product is
WMTS/WMS tile imagery only (fine for a map background, useless for
computing an area statistic per IRIS), and the genuine vector data
requires bulk per-department downloads through a JS-rendered portal with
no discoverable direct URL or WFS/Features API. IDF's own MOS dataset,
by contrast, is a real queryable vector layer covering the whole region
uniformly. The artificialized-category list above is modeled closely on
France's official artificialisation definition, but isn't a certified
reproduction of it — there's no single published crosswalk from MOS's
79-category regional legend to the legal nomenclature. Treat
`pct_artificialized` as a close, defensible proxy, not an official
figure.

**Why it belongs in the thermal sub-score, not a duplicate of `hvi`.**
Built and paved ground holds and re-radiates heat rather than absorbing
or evaporating it away — that's a *structural cause* of local heat
retention, distinct from `hvi` (a modeled temperature/vulnerability
index) and from the cool-facility/canopy indicators (proximity to
relief, not exposure to the underlying cause). It enriches the
sub-score rather than measuring the same thing twice.

**Coverage confirmed before integrating**: all 2,752 IRIS across the 4
departments have a value (min 2.1%, median 82.5%, mean 79.7%, max
100.0% after clipping a floating-point overshoot from the area-weighted
overlay). The dataset's stated millésime is uniform across Paris and
the three inner-suburb departments — no per-department vintage mismatch
to document.

**Urban-biodiversity reading, not separately scored.** Artificialized
ground is also lost habitat — this layer doubles as a rough proxy for
urban biodiversity loss, worth noting even though it isn't scored
separately for wildlife: no animal mortality or stress data comparable
to what's available for humans exists at this grain.

## Known caveats (read before trusting the numbers)

- **564 IRIS have `insufficient_data` for access, 76 for housing, 2 for
  thermal** (fewer than a strict majority of indicators available —
  typically very small or non-residential IRIS; the 2nd thermal case
  came from the `MIN_POPULATION_FOR_RATE` floor below). Their
  `n_subscores_evaluated` is reduced accordingly, and they're excluded
  from that sub-score's quartile ranking entirely (see "Minimum-
  indicator threshold" above).
- **`access_time` is now rank-standardized rather than raw-z-scored**
  (see "Access time's compressed distribution" above) after audit found
  it producing a raw z-score of +15.3 — from a floor-clustered
  distribution where half the metro area ties at "1 minute". Fixed at
  the scoring level, not just in the `/ranking` page's wording, though
  some IRIS with an objectively fast access time will still land in the
  worst access quartile by construction (there genuinely isn't much
  variance to work with at this density) — the `/ranking` page's
  `access_primary_driver`-based phrasing exists precisely for that
  residual case.
- **`cool_facility_deficit` is now population-floored and winsorized**
  (see "cool_facility_deficit's small-population inflation" above)
  after audit found it producing a raw z-score of -47.9 — nearly 3x
  `access_time`'s own pre-fix worst case — from a handful of park,
  cemetery, market, and industrial IRIS with a near-zero population
  denominator. Fixed at the scoring level: `MIN_POPULATION_FOR_RATE`
  excludes IRIS with under 50 residents from this indicator, and the
  resulting rate is capped at its own 3rd percentile. Worst raw z-score
  dropped to -2.78. The score-4 count grew from 1 to 4 IRIS as a direct,
  verified consequence (see above) — a genuine correction to a
  previously-distorted indicator, not a new artifact.
- **Two other indicators show a milder version of the same z-score
  extremity, from the same "long right tail on a rate" mechanism**
  (`canopy_deficit`, worst raw |z| 8.4; `housing_energy_poverty`, worst
  raw |z| 7.9 — small-sample noise for the latter, since its
  denominator is the DPE sample size, not population). Flagged as a
  follow-up, not fixed in this pass — each needs its own manual audit
  before changing, per this project's own practice of auditing before
  correcting rather than patching from a summary statistic alone.
- **Enedis thermosensitivity is a winter-heating signal, not a direct
  summer-cooling measurement** — Enedis doesn't publish one. Using it as
  a proxy for "can't compensate for heat" rests on the assumption that a
  poorly-insulated, electric-heating-dependent home is also hard to keep
  cool, which is physically reasonable (same building envelope) but not
  independently verified against actual summer electricity data here.
- **Thermal ICU coverage is 2,618/2,752 IRIS** (script 02): the
  Sat4BDNB source uses a coarser "grouped IRIS" geography that doesn't
  cover 100% of the metro area; the other three thermal indicators
  (cool facilities, canopy, artificialization) do cover all 2,752, so
  the thermal sub-score itself is missing only 1 IRIS overall (see
  completeness table above) — only `hvi` specifically is sometimes
  unavailable and gets skipped for that IRIS's average.
- **400m cool-spot buffer is centroid-based**, not a true walking
  distance — a straight-line buffer from the IRIS centroid, which will
  under/over-count for oddly-shaped or elongated IRIS.
- **PMR accessibility (`pct_pmr_accessible`, script 12) is crowdsourced
  and sparsely documented**: only ~19% of Acceslibre entries nationally
  have their wheelchair-accessible-entrance field filled in at all; the
  percentage is computed only over documented entries, not all ERPs, and
  1,064 of 2,752 IRIS (39%) have no documented entry at all — a
  notably higher share than Paris intra-muros alone had (115/992,
  11.6%), since crowdsourced coverage thins out further from the
  center.
- **Footway density (`footway_density_m_per_km2`, script 15) comes from
  OpenStreetMap** (`highway=footway` ways via Overpass), not an official
  accessibility audit — it measures how much dedicated pedestrian
  infrastructure is *mapped*, not its physical condition (width, curb
  cuts, obstacles). Full 2,752/2,752 IRIS coverage, no missing data.
- **The artificialized-surface classification is a close proxy for
  France's official artificialisation definition, not a certified
  reproduction of it** — see "Artificialization / sealed surface"
  above for the full reasoning and the OCS GE substitution decision.
- **Access times measure distance to the nearest facility, never its
  capacity or how busy it is** — a deliberate, known blind spot of this
  version, not an oversight. A nearby school or health clinic that's
  overcrowded looks identical here to one with room to spare; nothing
  in this pipeline currently measures equipment load or waiting times.

## Expanding beyond Paris (Phase 5)

Underlaid originally covered Paris intra-muros only (992 IRIS,
department 75). It now covers the full Métropole du Grand Paris
"Petite Couronne" — Paris plus Hauts-de-Seine, Seine-Saint-Denis and
Val-de-Marne — **2,752 IRIS**. Most source datasets (BPE, Filosofi, IPS,
DPE, Acceslibre, Airparif/Bruitparif, Sat4BDNB ICU, Enedis, OSM, IRIS
contours themselves, QPV, RNA) were already national or Île-de-France-
region datasets, filtered down to Paris in-script — extending them was
a filter change, not a new source.

Two thermal indicators were Paris-only by construction and had no
region-wide equivalent under their old sourcing:

- **Cool facilities** used to come from `opendata.paris.fr`. It's now
  built from the BPE (Base Permanente des Équipements, already used
  elsewhere in this pipeline) filtered to swimming pools (F101),
  museums (F305) and libraries (F307) — a genuinely region-wide,
  uniform source, re-sourced for Paris too, not just extended to the
  new departments.
- **Cool green space** used to come from `opendata.paris.fr`'s parks
  layer. It's now built from IDF's region-wide open/publicly-accessible
  green and wooded space dataset, same re-sourcing logic.

Re-sourcing both, uniformly, was a deliberate choice: it means Paris's
own already-shipped thermal indicators changed composition again, but
the alternative — one methodology for Paris and a different one for the
new departments — would make the sub-score not genuinely comparable
across the whole metro area, defeating the point of expanding at all.

Street lighting, tree-age proxy and the hand-compiled school-AC context
(scripts 13/19, 18, 16) have **no region-wide equivalent and stay
Paris-only** — shown as context layers in the frontend, explicitly
labeled as such, not silently omitted or forced onto a dataset that
doesn't exist.

**A new example at 4/4.** For the first time, one IRIS reaches the
maximum score: **Économie 1, in Drancy (Seine-Saint-Denis)** — median
income €18,020, 99.6% artificialized surface, population ~2,642.
Unlike the earlier Porte Dauphine/Madeleine examples, this isn't a
tiny-IRIS data-sparsity artifact: it's a normally-sized residential
zone (~0.58 km²), with genuinely high artificialization, low documented
accessibility, and low income — a pattern consistent with real,
well-documented disadvantage in that department.

**Verified against real-world imagery** (IGN Géoportail aerial
orthophotography, centered on the IRIS centroid at 48.9329°N,
2.4505°E) — the one first-wave example that had only ever been checked
against raw data, never imagery, unlike Porte Dauphine/Madeleine which
were at least checked that way. The image confirms every one of the 4
unfavorable sub-scores has a visible physical cause, not just a
statistical one:

- **Thermal / artificialization**: the IRIS sits immediately alongside
  the **Gare de triage du Bourget** (a large freight rail marshalling
  yard administratively named for Le Bourget but physically located in
  Drancy — one of only 4 remaining gravity-sorting rail yards in France
  and the last one in Île-de-France), a multi-track ballast corridor
  running the width of the area. Dense small-house residential streets
  border it directly, with almost no tree canopy visible anywhere in
  the frame — consistent with 99.6% artificialization and 0.36% cool
  green area.
- **Pollution**: the rail yard (freight/shunting operations) and a
  road overpass crossing it directly border the residential streets —
  a plausible, visible source of the ambient noise/air co-exposure the
  pollution sub-score measures (Airparif/Bruitparif data), not
  something that has to be taken on faith from the number alone. Worth
  keeping distinct from a separate, more serious fact found while
  checking this: the yard has an official Plan Particulier
  d'Intervention (PPI) for hazardous-material accidents — ~220,000
  wagons sorted annually, over 5% carrying dangerous goods, a
  2,600m emergency perimeter covering Drancy and 5 other communes, and
  a resident phone-alert system. That's a real, well-documented,
  separately-sourced risk (major-accident hazard, not ambient
  pollution) — cited here as additional context on what this facility
  is, not as evidence for the pollution sub-score specifically, which
  measures something narrower and already independently sourced.
- **Access**: the rail corridor is wide enough to function as a
  physical barrier between this residential pocket and whatever lies
  on its far side, consistent with reduced nearby service density.
- **Housing**: the visible building stock is small, older row/terrace
  housing — consistent with (though not proof of) the DPE F/G share and
  electrical thermosensitivity driving the housing sub-score.

This is now the strongest-verified single-IRIS example in the project:
checked against both raw indicators (above) and real-world imagery,
the same standard applied retroactively to Porte Dauphine/Madeleine
(data only, no imagery) and now met more fully here. Still treat it as
provisional rather than a permanent flagship, per this project's
standing rule that any single-IRIS example is provisional until
re-checked against whatever the data looks like at the time — but it
isn't dismissable as an artifact the way the first two were, and now
isn't resting on data alone either.

## Quartile thresholds: inhabited IRIS only

Since the v0 launch, each sub-score's quartile thresholds are computed
on IRIS with at least **50 residents** only (`MIN_POPULATION_FOR_RATE`,
the same floor as `cool_facility_deficit`'s per-resident rate). The 62
IRIS below it — parks, river banks, rail yards, stations, business
blocks — are then placed against those thresholds
(`quartiles_against_reference()` in script 11): they keep a quartile and
a score on the map, flagged "very sparsely populated" in the detail
panel, but no longer take quartile slots that belong to neighborhoods
people live in.

Why: an exposure score describes where people live. These IRIS took
74% of their slots in the worst air/noise quartile (they sit along rail
lines and expressways), 22% in thermal and 38% in housing (8 IRIS with
housing data), pushing inhabited IRIS out of the worst quartiles.
Effect: among the 2,690 inhabited IRIS, each sub-score is now split into
exactly 25/25/25/25; 34 inhabited IRIS changed score (1.3%); one enters
3/3 (Folie Méricourt 6, Paris 11e), none leaves.

## Current distribution (MGP — Paris + Petite Couronne, 2,752 IRIS)

3 sub-scores (thermal, air/noise pollution, housing), after access left
the count at the v0 launch (see "Why access to services left the
score"), quartile thresholds on inhabited IRIS (see above):

| Cumulative score | IRIS count | Share |
|---|---|---|
| 0 | 1,119 | 40.7% |
| 1 | 1,223 | 44.4% |
| 2 | 378 | 13.7% |
| 3 | 32 | 1.2% |

Inhabited IRIS only (≥ 50 residents, 2,690): 1,110 / 1,178 / 371 / 31.
Before the inhabited-thresholds rule: 1,144 / 1,202 / 375 / 31. Before
access left the count (4 sub-scores): 874 / 1,230 / 586 / 58 / 4.

The 32 IRIS at 3/3: 20 in Paris (mostly dense 8th, 11th, 12th, 15th,
16th, 17th arrondissements), 5 in Hauts-de-Seine (Neuilly-sur-Seine ×4,
Asnières), 3 in Seine-Saint-Denis (Aulnay ×2, Drancy), 4 in
Val-de-Marne (Villeneuve-Saint-Georges ×2, Champigny, Le Perreux). One
of them is not inhabited (Chaussée d'Antin 2, 0 residents).

**Public ranking (`/ranking`).** Lists the IRIS at 3/3 with at least
**50 residents** — the same floor as `cool_facility_deficit`'s
per-resident rate (`MIN_POPULATION_FOR_RATE`): below it an IRIS is a
park, a station or a business block, not a neighborhood people live in.
This removes 1 of the 32 (Chaussée d'Antin 2, 0 residents); such IRIS
stay on the map, flagged "very sparsely populated" in the detail panel
(62 IRIS in all are under 50 residents). The 31 listed IRIS are grouped
by the means-to-cope tertile (5 lowest, 5 middle, 18 highest, 3 without
published income), never by an implied cause, ordered by commune then
name, and each row shows the figures behind the three categories
(sealed ground, air/noise index, F/G-rated homes) plus median income,
each against the metro-wide median. A paragraph above the list states
finding 1 (same score, not the same exposures depending on means) so
the list is never read without it.

This is a live demonstration of the score's core caveat, repeatedly now:
it's an **estimate that shifts with every methodological correction and
every extension of scope**, not a fixed ground truth. Treat any single-
IRIS "flagship example" as provisional until cross-checked against the
raw indicators, the way every one of them has been so far, each time.

## Automated re-runs and why a large shift doesn't auto-publish

`.github/workflows/update-pipeline.yml` re-runs the full pipeline
quarterly (see README's "Keeping the data current" for the schedule and
mechanics) and re-derives this same table from scratch each time, since
upstream sources move: a new BPE/DPE/Acceslibre edition, an INSEE
Filosofi refresh, etc. `scripts/23_diff_report.py` compares the fresh
distribution against whatever is currently published (entries/exits on
score >= 3, and the shift in each category's share) before anything
goes live, and stops to open a pull request for manual review instead of
publishing if either moves more than a documented threshold (15%
turnover on score >= 3, or a 5 percentage-point shift in any single
category's share — both adjustable via the script's CLI flags, not
hardcoded assumptions about what "normal" looks like forever).

This isn't a hypothetical safeguard: it's the automated form of an audit
this project already had to do by hand twice, for exactly the reason a
large shift needs a person to look at it. `access_time`'s compressed
distribution produced a z-score of +15.3 and `cool_facility_deficit`'s
small-population inflation produced one of -47.9 — both real bugs, not
real changes in the world, and both were only caught because someone
looked directly at the numbers rather than trusting an automated run
(see the two sections above). A quarterly unattended re-run has no one
in the loop to do that unless the pipeline itself stops and asks.
