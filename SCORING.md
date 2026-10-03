# Cumulative environmental exposure score — methodology

Computed by `scripts/11_compute_vulnerability_score.py`, run after scripts
01-10, 12, 15, 17, 21, 22, 24 and 27-32. Output: `data/processed/vulnerability_score_iris.geojson`.
Travel times to key destinations (scripts 33-39) are information only,
never part of the score: see "Routes to key destinations".

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

**v0.2 note (October 2026)**: access is back in the count, rebuilt from
scratch as **access to care** (GPs and pharmacies reachable on foot and
by public transport, weighted by how many people share them). The score
counts **4** sub-scores again — thermal, air/noise pollution, housing,
access to care — and ranges **0-4**. Inclusive mobility (what a
wheelchair user keeps of that access) is computed and published for
information, not counted. See "Rebuilding access to services" below.
The old 0-4 score (until September 2026) and this one share a range but
not a definition: the access sub-score is a different measure.

**Census 2022 note (3 October 2026)**: population, overcrowding and
secondary residences now come from the 2022 census; income stays
Filosofi 2021, the latest vintage published at IRIS level. Decided
before seeing any result, whatever the result. The pre-registered
verdicts, computed with 2021, remain the official results; each was
redone with 2022 and confirmed. See "Census 2022: reference and
sensitivity check" below. Unless stated otherwise, figures in this file
that predate 3 October 2026 are 2021-census figures.

**"Highly exposed" (3 October 2026)**: 2 or more of the **3 exposures**
— thermal, air/noise pollution, housing — in their worst quartile.
Access to care is a separate axis and is never counted in "highly
exposed" (it is still one of the 4 sub-scores of the cumulative score).
Some findings below were first computed with "2+ of the 4 sub-scores";
they say so.

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
(INSEE, 2022 census since 3 October 2026, 2021 before,
`scripts/24_secondary_residences.py`) is the share of each
IRIS's housing stock that's a secondary residence or occasional
dwelling — a direct proxy for the capacity to physically leave during a
heatwave, unlike median income, which only captures that possibility
indirectly. Shown in the map's IRIS detail panel next to median income,
**it is never merged into any sub-score or the cumulative score** — it
is one of the three indicators of the separate adaptive-capacity axis
(see below) — adding it as a scored indicator
would just relabel the same "vulnerability, not exposure" conflation
this whole section exists to avoid. `P22_RSECOCC` (the INSEE source
variable; `P21_RSECOCC` before) counts secondary residences and occasional/seasonal dwellings
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

**Indicators** (all at IRIS level; income from Filosofi 2021, the
latest IRIS vintage; the two housing indicators from the 2022 census
since 3 October 2026, 2021 before):

| Indicator | Source variable | Direction | Masked (of 2,752) |
|---|---|---|---|
| Median disposable income | Filosofi `DISP_MED21` | higher = more means | 223 (8.1%) |
| Overcrowded homes (INSEE definition, moderate + severe) | RP 2022 logement `(C22_RP_SUROCC_MOD + C22_RP_SUROCC_ACC) /` sum of all occupation categories of the complementary count | higher = fewer means | 72 (2.6%) with the 2021 variable |
| Secondary residences & occasional dwellings | RP 2022 logement `P22_RSECOCC / P22_LOG` | higher = more means (option to leave) | 64 (2.3%) with 2021 |

Rates are suppressed below 20 dwellings (same floor as elsewhere).

**Overcrowding changed definition at INSEE in 2022.** The 2021 variable
(`C21_RP_HSTU1P_SUROCC / C21_RP_HSTU1P`) excluded studios occupied by one
person; it no longer exists. The 2022 base gives moderate and severe
overcrowding over all main residences. Both come from INSEE's
complementary (sample-based) count, so the denominator is the sum of all
occupation categories of that same count — dividing by the main count of
main residences gave a rate above 1 in one neighbourhood. The median
rate goes from 13.5% to 24.6%: a change of definition, not a change in
how people live.

**Construction.** Each indicator is turned into a percentile rank (0-1,
oriented so higher = more means); the index is their plain mean. Ranks,
not z-scores, because two of the three are heavily skewed (2021 census:
overcrowding skew 1.7, max |z| 11; secondary residences skew 4.1, max
|z| 14) — the
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
1 / 2+ — scores 3 and 4 together are only 3% of IRIS, too few for a
class of their own.

**Candidates measured and rejected.** Poverty rate (Spearman −0.91 with
median income and masked on exactly the same IRIS — a duplicate that
would double-weight income); share of social housing (ambiguous: the
landlord, not the household, can act on the building); households
without a car (in dense Paris, a way of life rather than a lack of
means). Home ownership (capacity to insulate or install shutters) was
considered and left out: it adds little to the grid and its meaning is
muddy in Paris, where many well-off households rent.

**Distribution (exposure score on 4, v0.2 release, 2021 census, 2,529
IRIS with an index; not republished here for 2022):**

| | means: lowest third | middle third | highest third |
|---|---|---|---|
| **exposure 0** | 248 | 301 | 176 |
| **exposure 1** | 404 | 378 | 392 |
| **exposure 2+** | 191 | 164 | 275 |

"2+" means 2, 3 or 4 of the 4 sub-scores in their worst quartile. With
the 3-sub-score score of the v0 launch, the 2+ row was 49 / 95 / 236.

**1. Two profiles, not one scale.** Highly exposed IRIS (2 or more of
the 3 exposures) with the highest means are mostly in Paris and stack
heat and old, energy-inefficient housing — dense, older building stock.
Those with the lowest means are mostly in Seine-Saint-Denis and
Val-de-Marne and stack mainly heat, air pollution and noise. (With the
2021 census and "2+ of the 4 sub-scores", v0.2 release: correlation of
the capacity index with housing +0.66, thermal +0.37, pollution −0.30,
access to care −0.50; 195 of the 275 highly exposed IRIS with the
highest means were in Paris.)

**2. The link between exposure and means is weak**, and slightly
positive because of dense, older central Paris. Spearman(capacity
index, exposure score on 4) = **+0.09** with the 2022 census (+0.11 with
2021; +0.28 with the score on 3 at the v0 launch). Within the
inner-suburb départements it's near zero. Always state it with that
explanation in public copy — never as "the well-off are more exposed",
which the data doesn't show outside Paris.

**3. Where high exposure and low means meet, it's concentrated.** Share
of the highly exposed IRIS (2 or more of the 3 exposures) that are in
the metro area's lowest third of means, 2022 census: Seine-Saint-Denis
**61.8%**, Val-de-Marne 24.5%, Paris 4.5%, Hauts-de-Seine 1.9%. With
the 2021 census and the same definition: 76.5%, 28.6%, 2.4%, 5.8%. The
figure long quoted for Seine-Saint-Denis, 79%, was "2+ of the 4
sub-scores" with 2021. Between the two censuses, 474 of the 2,529 IRIS
with a means index change third, always to a neighbouring one, while
overcrowding changed definition (see "Census 2022" below).

**How this crossing changed the exposure score itself.** The first
version of this grid was computed with the former 4-sub-score exposure
score, and its "2+ / lowest means" cell turned out to be largely built
in: the access sub-score included school social position (IPS), which
reflects families' resources — already measured on this axis, so they
were counted twice (capacity vs access: −0.52).
That finding started the audit that took access out of the score — see
"Why access to services left the score" below. With the 3-sub-score
score, the cell has no such mechanical overlap: none of the three
remaining sub-scores uses a population characteristic. Access to care
(v0.2) doesn't either — it counts GPs and pharmacies against the number
of people who can reach them — yet it is linked to means (Spearman −0.50
with the 2021 census, −0.39 with 2022), mostly through geography: within
each département the link is weak (2021: 92 and 94 −0.16, 93 −0.02;
2022: 92 −0.13, 94 −0.15, 93 +0.04). Its effect on the hypothesis is tested within
départements and at equal density, not metro-wide (see "Working
hypothesis and its test").

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

## The 4 sub-scores

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
| **Access to care** (v0.2) | `-gp_std` (GPs reachable per 10,000 age-weighted residents, E2SFCA, walking + public transport) · `-pharmacy_std` (pharmacies within a 15-min walk per 10,000 residents, E2SFCA); both rank-standardized (skewed: 1.2 and 1.8) | scripts 27-32 |

Each sub-score is the **unweighted mean** of its (standardized) indicator
z-scores, skipping indicators missing for a given IRIS. Weights are equal
by design — there's no principled basis yet to weigh one indicator over
another; revisit this once the tool has real user feedback.

The former access sub-score (scripts 07, 09, 12, 15 — travel time,
school IPS, wheelchair-accessible entrances, OSM footway density) was
counted until the v0 launch. Its raw figures are still in the output,
shown as unscored context in the map's detail panel — see the next
section for why it left, and "Rebuilding access to services" for what
replaced it.

## Why access to services left the score

Found while crossing the score with the adaptive-capacity axis (see
above): the access sub-score moved with residents' means (Spearman
−0.52), and each of its four indicators turned out to fail on its own.
Every alternative was simulated on the full data before deciding,
without touching the published score.

**The four indicators, one by one.**
- **School IPS (social position index)** reflects families' resources,
  which the separate means axis already measures: keeping it in the
  score counted them twice. It was the access driver for most of the
  IRIS whose "high exposure / low means" profile relied on access.
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
  Counting street-tagged sidewalks too fixes Klock but not the root
  problem: the share of street length with *any* sidewalk information is
  75: 96%, 92: 63%, 93: 26%, 94: 47%, and the gap between departments
  reaches 71 points at equal density (rule set beforehand: 15 points
  max). Audit of 2026-10-01 in docs/LESSONS.md and
  `scripts/analysis/osm_sidewalk_completeness.py`; footway density no
  longer appears on the map.
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

**Coming back.** The rule set at the time: access returns only once an
indicator passes both the global and the per-indicator-count quartile
checks. It came back in v0.2 as access to care, built with a 2SFCA on
the 200 m population grid (next section); footway counting was audited
and left out (mapping inequality, see above).

Median income (`08_income_filosofi.py`) is **not** part of the score. It
is carried through to the output for step 4 (correlation between income
and cumulative exposure), on purpose — folding it into the score would
make that correlation circular. It's also one of the three
indicators of the separate adaptive-capacity axis — see "Adaptive
capacity — a separate axis" below.

## Rebuilding access to services (v0.2: access to care is scored)

Access to services is the project's central question. It was rebuilt
from scratch (scripts 27-32) and, after validation, **access to care**
entered the score in v0.2. **Inclusive mobility** is computed with the
same method and published for information, not counted.

### Access without a car

The new measure counts what residents can reach **on foot and by public
transport**, not by car. That's a deliberate choice, coherent with what
the project is about:

- the question is equal access to everyday services for everyone,
  including people who can't drive or don't have a car: children and
  teenagers, many older people, people with disabilities, people with a
  pushchair, and the many households without a car in dense areas
  (most households in Paris, many in the inner suburbs);
- the inclusive-mobility part of the measure (step-free walking,
  accessible public transport) only makes sense for trips made without
  a car;
- it is also why this measure differs from the DREES APL, which uses
  car travel times between communes: the two answer different questions
  and both are useful.

### Structure, and the order in which it was decided

1. **2026-10-02, before any crossing with residents' means**: two
   separate measures, not one — **access to care** (GPs and pharmacies)
   and **inclusive mobility** (the gap described below). They pull in
   opposite directions (rank correlation −0.62 across inhabited IRIS:
   central Paris has the most GPs within reach but loses the most when
   travelling step-free, since the metro is largely inaccessible), so
   averaging them would cancel two distinct phenomena. Planned then: a
   score on 5.
2. **Same day, before any crossing**: the test of the working hypothesis
   was written down (next section).
3. **After reading the result of that test**: the score counts 4
   sub-scores; inclusive mobility is not counted. Reason given: it
   compares two ways of travelling *from the same place* (step-free vs
   standard), while the score compares *places with each other*; it is
   not an exposure of the place. This decision was taken knowing the
   result, and is recorded as such. The verdicts below are unchanged by
   it, and the gap is still computed and published.

Sub-score rules, the same as the others: both indicators required (2 of
2); quartile thresholds on inhabited IRIS; IRIS whose population cells
can't be routed (e.g. the La Défense deck) get `insufficient_data`.
Completeness: 2,746 of 2,752 IRIS; 25/25/25/25 among inhabited IRIS.

### Working hypothesis and its test (pre-registered)

Hypothesis, written on 2026-10-01 before any result: residents of the
neighbourhoods with the fewest means are structurally disadvantaged in
access to services and inclusive mobility. Test fixed on 2026-10-02,
before computing the sub-scores and before any crossing with means, for
each measure S and each département d (inhabited IRIS; means thirds of
the whole metropolis):

- gap_d = share of S's worst quarter in the lowest third of means −
  share in the highest third; ρ_d = Spearman(means index, S);
- **clearly unfavourable in d** if gap_d ≥ +10 points and ρ_d ≤ −0.10;
  a département is assessed only if each third has ≥ 20 IRIS there;
- **supported** if clearly unfavourable in ≥ 2 départements, at least
  one other than Seine-Saint-Denis, and the metro-wide gap ≥ +10 points;
- **refuted** if the metro-wide gap ≤ −10 points or ≥ 2 départements are
  clearly reversed; **qualified** otherwise;
- for inclusive mobility, the conclusion holds only if identical with
  unknown accessibility counted as "no" and as "yes".

Results (`scripts/analysis/access_step4.py`, `access_score4.py`; 2021
census — the official results):

- **Access to care: supported.** In Hauts-de-Seine, 41% of the
  neighbourhoods in the lowest third of means are in the worst quarter
  for access to care, against 24% in the highest third (+17 points);
  Val-de-Marne, 41% against 24% (+17 points). At equal population
  density (density fifths), the gap holds and widens: +23 points in
  both. Paris: almost every neighbourhood has very good access, so the
  gap is small (+4 points). Metro-wide, the gap (+29 points) mixes in
  the difference between Paris and the inner suburbs, which is largely
  a matter of density; the within-département and equal-density figures
  are the ones that test the hypothesis.
- **Seine-Saint-Denis could not be assessed** by the rule: a single IRIS
  there is in the metro-wide highest third of means. A limit of the
  rule, not a finding (see docs/LESSONS.md); next pre-registrations use
  thirds computed within each département, or absolute shares.
- **Inclusive mobility: refuted**, identical with both variants. The
  share of GP access lost when travelling step-free is largest in
  central Paris, where standard access relies on a largely inaccessible
  metro, whatever the means of the neighbourhood (worst quarter: 10% in
  the lowest third, 42% in the highest). This does not mean wheelchair
  access is good elsewhere: in number of GPs reachable step-free, the
  median is lower than in Paris in each inner-suburb département
  (Paris 7.5 per 10,000; 92: 7.0; 93: 5.8; 94: 6.8) and in each third of
  means.

**Check with the 2022 census (3 October 2026): both verdicts confirmed.**
The same test, same rule, redone after the census change (rule fixed
before the results: the 2021 verdicts stay official; a verdict not
confirmed would be said plainly, not replaced). Access to care:
Hauts-de-Seine 39.3% against 24.0% (+15.2 points), Val-de-Marne 38.8%
against 27.9% (+10.9), both clearly unfavourable; metro-wide gap +22.9
points (+29.4 with 2021); at equal density, 20.7 points in
Hauts-de-Seine and 17.3 in Val-de-Marne; Paris +3.2. Seine-Saint-Denis
still can't be assessed (8 of its IRIS in the metro-wide highest third,
fewer than the 20 required). Inclusive mobility: Paris still clearly
reversed (52.3% in the lowest third against 66.2% in the highest), 13.2%
against 35.0% metro-wide, identical with both variants. Outputs:
`data/interim/analysis/access_step4_rp2021.txt` and
`access_step4_rp2022.txt` (git-ignored working files).

The consequence, stated plainly: a neighbourhood where GPs are easy to
reach by car but far on foot or by bus scores low here. That's what the
measure is meant to show, not an error.

### Method (E2SFCA)

Enhanced two-step floating catchment area (Luo & Qi 2009), with the
DREES APL's distance decay (under 10 min: 1; 10-15: 2/3; 15-20: 1/3;
beyond: 0) for GPs, and a 15-minute walk for pharmacies. Demand is the
INSEE 200 m population grid (Filosofi 2021), weighted by age with the
DREES weights for GPs. Supply and demand cover the whole of
Île-de-France so neighbourhoods at the edge of the inner ring see
services across the boundary. Travel times: R5 (r5py) on OpenStreetMap
and the Île-de-France Mobilités timetables, Tuesday 13 October 2026,
departures 10:00-11:00 (sensitivity: 17:30-18:30), walking 4.5 km/h.
Full parameters and their sources are in the docstrings of scripts
29-32.

Timetables: contains information from "Horaires prévus sur les lignes de
transport en commun d'Île-de-France (GTFS Datahub)", made available by
Île-de-France Mobilités under the terms of the "Licence Mobilités".

Inclusive mobility: GP access is recomputed with step-free walking
(OpenStreetMap steps plus paths along IGN staircases missing from
OpenStreetMap) and public transport restricted to stops and trips marked
accessible in the timetables, with the competition for each practice
kept as in the standard scenario. The gap (accessible access / standard
access, between 0 and 1) is the share of reachable GP capacity a resident
keeps when travelling step-free.

### General practitioners: who is counted

GPs from the national directory (RPPS), liberal or salaried in a health
centre, the same field as the DREES APL. Left out by sector:
teleconsultation companies, hospitals, maternal and child health
centres, social security, workplace health. Then left out by an explicit
list, decided on 2026-10-02 after reviewing by hand every address with
15 or more GPs: structures registered as practices or health centres
that don't offer local, everyday GP consultations — teleconsultation
platforms (their headcount is the remote workforce), on-call and
home-visit services (their doctors are registered at every on-call
point), hospital and clinic emergency departments, and services reserved
to one population.

| Reason | Structure(s) / address | GPs registered there | How identified |
|---|---|---|---|
| SOS 92 on-call point (Boulogne-Billancourt) | 27 Rue De Sevres, 92100 Boulogne-Billancourt | 44 | address, checked |
| SOS Médecins 91 (Chevannes) | 19 Rue De La Liberation, 91750 Chevannes | 20 | address, checked |
| SOS Médecins Paris (centre and home visits) | 87 Boulevard De Port Royal, 75013 Paris | 139 | address, checked |
| SOS Médecins Paris 17 | 2 Rue Francis Garnier, 75017 Paris | 48 | address, checked |
| SOS Médecins Paris 19 | 128 Boulevard Macdonald, 75019 Paris | 70 | address, checked |
| SOS Médecins on-call point (Marly-le-Roi) | 14 Rue Titreville, 78160 Marly-le-Roi | 19 | address, checked |
| Urgences Médicales de Paris | 24 Rue De L Est, 75020 Paris | 45 | address, checked |
| Urgences Médicales de Paris / Urgences Franciliennes (Clinique du Parc Monceau) | 21 Rue De Chazelles, 75017 Paris | 24 | address, checked |
| clinic (Clinique de l'Estrée, Stains) | 35 Rue D Amiens, 93240 Stains | 16 | address, checked |
| SOS Médecins 77 network (Chelles) | 18 Rue Gustave Nast, 77500 Chelles | 28 | address, same doctors as a checked site |
| SOS Médecins 77 network (Coulommiers) | 14 Allee De La Rotonde, 77120 Coulommiers | 28 | address, same doctors as a checked site |
| SOS Médecins 77 network (Crécy-la-Chapelle) | Place Michel Houel, 77580 Crécy-la-Chapelle | 26 | address, same doctors as a checked site |
| SOS Médecins 77 network (Meaux) | 35 Rue Des Cordeliers, 77100 Meaux | 28 | address, same doctors as a checked site |
| SOS Médecins 77 network (Roissy-en-Brie) | 5 Place De La Revolution, 77680 Roissy-en-Brie | 27 | address, same doctors as a checked site |
| SOS Médecins 77 network (Serris) | 1 Rue Du Theatre, 77700 Serris | 26 | address, same doctors as a checked site |
| SOS Médecins 95 network (Argenteuil) | 54 Rue Vigneronde, 95100 Argenteuil | 15 | address, same doctors as a checked site |
| SOS Médecins 95 network (Saint-Ouen-l'Aumône) | 21 Rue Des Freres Capucins, 95310 Saint-Ouen-l'Aumône | 20 | address, same doctors as a checked site |
| SOS Médecins 95 network (Taverny) | 2 Place Des 7 Fontaines, 95150 Taverny | 40 | address, same doctors as a checked site |
| on-call network (Bondy) | 17 Avenue Henri Varagnat, 93140 Bondy | 18 | address, same doctors as a checked site |
| on-call network (Groslay) | 5 Rue Des Ouches, 95410 Groslay | 18 | address, same doctors as a checked site |
| on-call network (Lieusaint) | 18 Trait D Union, 77127 Lieusaint | 15 | address, same doctors as a checked site |
| on-call network (Épinay-sur-Seine) | 12 Rue Du General Julien, 93800 Épinay-sur-Seine | 19 | address, same doctors as a checked site |
| on-call network, same doctors as Bondy and Épinay (Drancy) | 17 Avenue Henri Barbusse, 93700 Drancy | 17 | address, same doctors as a checked site |
| on-call network, same doctors as SOS Médecins 91 (Brie-Comte-Robert) | 37 Rue Du General Leclerc, 77170 Brie-Comte-Robert | 18 | address, same doctors as a checked site |
| on-call network, same doctors as SOS Médecins 91 (Melun) | 11 Boulevard De L Almont, 77000 Melun | 14 | address, same doctors as a checked site |
| on-call network, same doctors as Urgences Médicales de Paris (rue de Bagnolet) | 122 Rue De Bagnolet, 75020 Paris | 26 | address, same doctors as a checked site |
| on-call network, same doctors as Urgences Médicales de Paris (rue de Vaugirard) | 178 Bis Rue De Vaugirard, 75015 Paris | 21 | address, same doctors as a checked site |
| on-call point, same doctors as SOS 92 (Antony) | 14 Rue De L Abbaye, 92160 Antony | 30 | address, same doctors as a checked site |
| airport medical service | CTRE SOINS PREVENTION AEROPORTS PARIS (Orly) | 8 | name pattern |
| hospital or clinic emergency department | SEL URG HPMC (Brou-sur-Chantereine); SELARL DES URGENCES FRANCILIENNES (Champigny-sur-Marne); SELARL DES URGENCES FRANCILIENNES (Jossigny); SELARL DES URGENCES FRANCILIENNES (Magny-le-Hongre); SELARL DES URGENCES FRANCILIENNES (Paris); SELARL DES URGENCES FRANCILIENNES (Pontault-Combault); SELARL URGENCES HOPITAL PRIVE ANTONY (Antony); URGENCE TRAUMATOLOGIE DU SPORT (Issy-les-Moulineaux); URGENCE TRAUMATOLOGIE DU SPORT (Paris); URGENCES ORANGERIE (Le Perreux-sur-Marne); URGENCES ORANGERIE (Nogent-sur-Marne) | 47 | name pattern |
| reserved to students (university health service) | CDS SSE SERVICE DE SANTE ETUDIANTE (Paris 6e arr.) | 32 | name pattern |
| teleconsultation platform (Livi) | CDS JONQUIERE LIVI (Paris 17e arr.) | 57 | name pattern |
| teleconsultation platform (Medadom / Mediksanté) | CDS MEDIKSANTE (Paris 17e arr.); CDS MEDIKSANTE PARIS 2 (Paris 2e arr.) | 103 | name pattern |
| teleconsultation platform (Qare / Access Santé) | CDS ACCESS SANTE PARIS 17 (Paris 17e arr.); CDS QARE (Saint-Maur-des-Fossés) | 105 | name pattern |

764 GPs have at least one excluded registration. GP capacity in Île-de-France goes from 9,873 to 9,294; a GP who also practises elsewhere keeps their capacity there.

Known limits of the supply: one GP counts 1 whatever their working time
(actual activity per GP, used by the APL, isn't public), so health
centres with many part-time GPs weigh more here than in the APL;
pharmacies all count the same.

## Routes to key destinations (October 2026, information only)

Scripts 33-39. Travel times from each neighbourhood to the **nearest**
destination of each type, on foot and by public transport, for several
ways of travelling and times of day. Everything in this section was
pre-registered on 2026-10-02, before any of these times was computed
(destinations, inclusion rules, profiles, time slots, aggregation,
controls and the test below). **None of it enters the score.**

### Destinations and inclusion rules (script 33)

Same kind of service in all four départements, decided before computing
anything; supply covers the whole of Île-de-France (same edge rule as
the E2SFCA). Every excluded record is written, with its reason, to
`data/processed/access/route_destinations_excluded.csv`.

| Type | Source | Rule |
|---|---|---|
| Emergency department | BPE 2025 `D106` | general emergency departments only; units reserved to one specialty or to children excluded by name (Quinze-Vingts, Trousseau, Necker, Robert-Debré). Children's access to paediatric emergencies is therefore not measured |
| Town hall | BPE 2025 `A129` | one per commune (per arrondissement in Paris), duplicates at the same point counted once; town-hall annexes are not in the BPE and are not counted (a limit that can penalise large suburban communes that have them) |
| France Travail | BPE 2025 `A122` | local agencies ("APE") only; specialised agencies ("APES": performing arts, airport) excluded |
| Post office | BPE 2025 `A206` | post-office counters; relay points and communal postal agencies left out (partial services) |
| France Services | ANCT list | fixed sites and antennas; mobile buses excluded (no fixed location) |
| CAF, CPAM | DILA public-administration directory | the fund's own offices open to all ("accueil de …", "siège de …", "accueil national"); excluded: "Point d'accueil" sessions hosted by partner organisations and reserved to specific groups, specialised services, four offices hosted by a partner or reserved to one group |
| GP, pharmacy | scripts 27 and 28 | the cleaned supply of access to care |
| Station | IDFM GTFS | heavy-network stop points (metro, RER, Transilien, tram), reached **on foot only**; for step-free profiles, accessible stop points only |

### Excluded destinations (full list)

The 62 records set aside by the rules above, as written by script 33 (`data/processed/access/route_destinations_excluded.csv`, run of 2 October 2026). INSEE commune code given for each.

| Type | Name | Commune | Reason |
|---|---|---|---|
| Emergency department | CENTRE NATIONAL D OPHTALMOLOGIE DES QUINZE VINGTS DE PARIS | 75112 | ophthalmology only |
| Emergency department | GHU APHP SORBONNE UNIVERSITE SITE TROUSSEAU | 75112 | children only |
| Emergency department | GHU APHP CENTRE UNIVERSITE PARIS CITE NECKER ENFANTS MALADES | 75115 | children only |
| Emergency department | GHU APHP NORD UNIVERSITE PARIS CITE SITE ROBERT DEBRE | 75119 | children only |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil CSAPA 110 Les Halles | 75102 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil ESI Famille Bonne Nouvelle - CASP | 75102 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - accueil de Saint-Martin-Armée du Salut | 75103 | office hosted by a partner or reserved to one group |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - accueil Mairie du 9ème | 75109 | office hosted by a partner or reserved to one group |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Amicale du Nid | 75110 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Boy Zelensky - Restos du Coeur | 75110 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil CAFDA | 75110 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil La salle de consommation à moindre risque | 75110 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil PASTT | 75110 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - accueil La Maison dans la rue - CASP | 75110 | office hosted by a partner or reserved to one group |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Emmaüs Solidarité - Agora | 75111 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Gaïa Paris CSAPA | 75111 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Les Petits Frères des Pauvres | 75111 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris -  Point d'accueil SAMU Social | 75112 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Boutique Solidarité - La Maison dans la Rue - Emmaüs Solidarité | 75112 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Mairie du 12ème | 75112 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil PSA Bastille | 75112 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Service des Relations Internationales | 75112 | specialised service |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Service des risques professionnels | 75112 | specialised service |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Association Charonne | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Aurore | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil La Mie de Pain | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Les Olympiades | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Plateforme AGATE SAMU Social | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil SPIP | 75113 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Cité Universitaire | 75114 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil La halle Saint Didier | 75116 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil PSA Gauthey | 75117 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil ESI Championnet | 75118 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Permanence CPAM - CSAPA EGO | 75118 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Pôle santé Goutte d'Or | 75118 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Sleep In | 75118 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Maison du Partage | 75119 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Relais du Coeur | 75119 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Service installation et accompagnement des PS | 75119 | specialised service |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Espace solidarité - Halte aux femmes battues | 75120 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil Les Amis du Bus des femmes | 75120 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - Point d'accueil PSA Belleville | 75120 | session hosted by a partner organisation, reserved to specific groups |
| CPAM | Caisse primaire d'assurance maladie (CPAM) de Paris - accueil Les Hauts de Belleville AME | 75120 | office hosted by a partner or reserved to one group |
| France Travail | APES AGENCE SPECTACLE DF DROM MED | 75115 | specialised agency |
| France Travail | APES AVS PLACEMENT ARTISTES | 75115 | specialised agency |
| France Travail | APES CINÉMA SPECTACLE PARIS | 75115 | specialised agency |
| France Travail | APES CINÉMA SPECTACLE OUEST ET NORD | 92025 | specialised agency |
| France Travail | APES AVS TECHNICIEN & JOURNALISTE | 93066 | specialised agency |
| France Travail | APES AÉROPORTUAIRE ROISSY CDG | 95527 | specialised agency |
| France Services | Bus France services Plaines et Monts de France | 77153 | mobile bus, no fixed location |
| France Services | Bus France services Pimms Médiation Nemours | 77333 | mobile bus, no fixed location |
| France Services | Bus France services de la Communauté de communes des 2 Vallées | 91405 | mobile bus, no fixed location |
| France Services | Bus France services Prox e-Bus de Morangis, Wissous et Savigny-sur-Orge | 91432 | mobile bus, no fixed location |
| France Services | Bus France services d'Aulnay-sous-Bois | 93005 | mobile bus, no fixed location |
| France Services | Bus France services Solibus | 93014 | mobile bus, no fixed location |
| France Services | Bus France services La Courneuve | 93027 | mobile bus, no fixed location |
| France Services | Bus France services Pimms Médiation - Noisy Le Grand | 93051 | mobile bus, no fixed location |
| France Services | Bus France services de Noisy-le-Sec | 93053 | mobile bus, no fixed location |
| France Services | Bus France services de Saint Denis | 93066 | mobile bus, no fixed location |
| France Services | Bus France services Pimms Médiation Sevran | 93071 | mobile bus, no fixed location |
| France Services | Bus France services départemental du Val d'Oise | 95127 | mobile bus, no fixed location |
| France Services | Bus France services CIAS de la Communauté de communes Carnelle Pays-de-France | 95352 | mobile bus, no fixed location |

The accessibility of the destination building itself is unknown.

### Profiles, time slots, aggregation (scripts 34, 36)

- **No constraint**: full OpenStreetMap network and full IDFM timetables,
  walking 4.5 km/h.
- **Slow walking**: same networks, **3.4 km/h** (0.943 m/s, women aged
  80-99, Bohannon & Andrews 2011, *Physiotherapy* 97(3):182-189; the
  lower of the women's and men's values).
- **Step-free** (wheelchair, pushchair): network without stairs (script
  30) and timetables restricted to accessible stops and trips, walking
  4.5 km/h, in two variants: unknown accessibility counted as "no" (shown
  on the site as "wheelchair") and as "yes". A conclusion on this profile
  holds only if identical in both. One profile for both uses, because the
  data don't distinguish them (the timetables only code wheelchair
  accessibility; no open history of lift outages). Presented everywhere
  as a **lower bound**: no lift outages, pavement condition, reduced
  speed or accessibility of the destination building.
- **Time slots**: Tuesday 13 October 2026 at 10:00 (main), 21:00 and
  1:00 (night, Noctilien included); Sunday 11 October 2026 at 10:00.
  Departures over 60 minutes, R5 median time. Rule for later runs: the
  first Tuesday / Sunday at least 7 days after the timetable download,
  outside school holidays (zone C) and public holidays.
- **Origins**: every inhabited 200 m cell of the MGP (Filosofi 2021
  grid). Maximum 90 minutes; a cell that doesn't reach a type counts as
  +∞ (never 0, never dropped). Value of a neighbourhood = population-
  weighted median of its cells; if more than half its population doesn't
  reach the type, it is "more than 90 min". Imposed detour = step-free
  time − standard time, per cell, then the same median.

### Controls (pre-registered, before any crossing)

`scripts/analysis/routes_controls.py` (output
`data/interim/analysis/routes_controls.txt`), Tuesday 10:00, 2,688
inhabited neighbourhoods with a value:
- **Floor**: the nearest GP and pharmacy are 2 minutes or less for 44.1%
  and 38.3% of neighbourhoods (no constraint) — the same
  squashed-against-the-floor signature as the old `access_time`. Public
  services don't have it (1.6% or less at 2 minutes; post office 6.8%).
- **Completeness**: population not reaching a type within 90 min, no
  constraint: 0.1% for every type.
- **Step-free vs no constraint**: median ratio 1.00 for most types; CAF
  1.09 (Paris 1.22), CPAM 1.03 (Paris 1.14). The nearest destinations
  are mostly reached on foot and by bus, largely accessible according to
  the timetables; only trips that rely on the metro get longer.
- **Stability of the two step-free variants**: Spearman 0.993 to 1.000
  by type; 2.3% of neighbourhoods change quarter on the public-services
  indicator.

**Decision of 3 October 2026, before any crossing with means, for a
reason of method**: travel times to public services stay
**information, not a scored sub-score**. They measure distance to the
nearest office, with no capacity data, whereas access to care is scored
because it accounts for shared capacity (E2SFCA). GP and pharmacy
times are information only too (floor effect above).

### Selected results (script 38, `routes_summary.json`)

Median of the neighbourhoods, Tuesday 10:00, minutes:

| Destination | No constraint | Slow walking | Wheelchair |
|---|---|---|---|
| Emergency department | 18 | 22 | 21 |
| GP | 3 | 4 | 3 |
| Pharmacy | 3 | 4 | 3 |
| Town hall | 12 | 15 | 14 |
| France Services | 16 | 19 | 18 |
| CAF | 24 | 27 | 29 |
| CPAM | 19 | 22 | 21 |
| France Travail | 16 | 19 | 18 |
| Post office | 7 | 9 | 7 |

Nearest station on foot, median by département (Paris / 92 / 93 / 94):
no constraint 3 / 8 / 10 / 12 min; slow walking 5 / 11 / 14 / 16;
nearest **accessible** stop point (wheelchair) 11 / 11 / 13 / 15.

Emergency department at night (Tuesday 1:00, on foot and by public
transport, no constraint): median 19 min in Paris, 13.5% of
neighbourhoods over 30 min and 1.4% over 45; inner suburbs median 27
min, 40.8% over 30 and 13.3% over 45.

**Display rules (3 October 2026).** Public services, GP and pharmacy:
information, never a sub-score. At night, only emergency departments and
stations are shown — never the CAF, the town hall or other offices,
whose opening hours aren't in the data. Every night-time duration says
"on foot and by public transport". Evening, night and Sunday are shown
for emergency departments and stations only.

### Public services and residents' means (pre-registered test)

Hypothesis (2026-10-02, before any time was computed): neighbourhoods
whose residents have the fewest means are more often far from public
services. Indicator: mean percentile rank of the times to the town hall,
France Services, CAF, CPAM, France Travail and post office, Tuesday
10:00, (a) no constraint and (b) step-free (conclusion held only if
identical in both variants). Worst quarter defined on the inhabited
neighbourhoods of the MGP. Learning from the Seine-Saint-Denis lesson
(see "Working hypothesis and its test" and docs/LESSONS.md), **thirds of
means are computed within each département**. For each département d:
gap_d = share in the worst quarter among the lowest third − share among
the highest third; ρ_d = Spearman(means index, indicator, higher =
farther). **Supported** if gap_d ≥ +10 points and ρ_d ≤ −0.10 in at
least 2 départements, at least one other than Seine-Saint-Denis;
**refuted** if at least 2 départements are clearly reversed (gap_d ≤
−10 and ρ_d ≥ +0.10); qualified otherwise. Complementary check reported
without changing the verdict: the same at equal density (density
fifths).

**Result (3 October 2026, `scripts/analysis/routes_means.py`; 2021
census, the official result): refuted, and reversed.** Share of
neighbourhoods in the farthest quarter, (a) no constraint:

| Département | Lowest third of means | Highest third | Gap (points) | ρ |
|---|---|---|---|---|
| Paris | 1.7% | 3.8% | −2.1 | +0.24 |
| Hauts-de-Seine | 27.2% | 48.2% | −21.0 | +0.28 |
| Seine-Saint-Denis | 25.4% | 45.5% | −20.1 | +0.22 |
| Val-de-Marne | 25.1% | 46.2% | −21.1 | +0.18 |

Clearly reversed in Hauts-de-Seine, Seine-Saint-Denis and Val-de-Marne;
at equal density the gap stays negative (−13.0, −3.7 and −13.6 points;
Paris −1.6). (b) Step-free: clearly reversed in all four départements,
in both variants (unknown = no: gaps −14.9 / −27.2 / −19.6 / −21.1
points for Paris / 92 / 93 / 94). No indicator, profile, time slot or
destination was changed after this crossing.

**What it does and doesn't say.** Neighbourhoods with the most means are
more often far from public services. The indicator measures travel time
on foot and by public transport only: it doesn't account for the need to
use these services, car use or online procedures, and the data don't
establish why.

**Check with the 2022 census: confirmed.** (a) no constraint: Paris 1.7%
against 6.2%, Hauts-de-Seine 26.7% against 48.2%, Seine-Saint-Denis
22.2% against 49.7%, Val-de-Marne 25.1% against 45.3%; reversed in 92,
93 and 94. (b) step-free: reversed in all four, both variants. Outputs:
`data/interim/analysis/routes_means_rp2021.txt` and
`routes_means_rp2022.txt` (git-ignored working files).

### Everyday places and per-commune files (scripts 37, 39)

Script 37 prepares seven everyday places for the "Votre quartier" page,
pre-registered and validated on 2026-10-03, all for information: crèches
(BPE `D502`, establishments receiving a CAF service grant — mostly
crèches charging the CAF income-based rate; micro-crèches with free
pricing are largely absent; the BPE lags about two years), food stores
(BPE `B104`, `B105`, `B201`; groceries under 120 m² excluded; the
supermarket category includes non-food shops of the same size), public
nursery schools (`C107`, `C108`, public sector; the nearest school is
not necessarily the assigned one), national police stations open to the
public (`A140`), social centres (`D506`), local-authority libraries
(`F307`) and parks (regional inventory of open green spaces, points
every 100 m along each outline since entrances are unknown). Markets were
dropped: OpenStreetMap is the only source and it isn't mapped evenly
across départements. Same method as the routes, Tuesday 10:00, the four
profiles; no crossing with means is pre-registered for them.

Script 39 writes one small file per commune (per arrondissement in
Paris) with everything the page shows about each neighbourhood —
exposures, rank shares, means, travel times — so the page no longer
loads the whole 5 MB score to find one address.

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
became its 4th indicator), 2 of 2 for access to care (3 of 4 for the
former access sub-score), 1 of 1 for pollution (a
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

Range 0-4 since v0.2 (0-3 at the v0 launch; 0-4 before it, with the
former access sub-score). An IRIS missing data for every sub-score gets
a null cumulative score rather than being silently treated as "not
exposed". `n_subscores_evaluated` records how many of the 4 sub-scores
had data for that IRIS, for transparency.

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
population — 2021 at first, to match Filosofi's income data; 2022 since
3 October 2026, see "Census 2022"). IRIS with zero population (non-residential — a park, a
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
- **DPE labels of small dwellings are already on the 2024 scale.** The
  2021 method rated dwellings under 40 m² too harshly (fixed water-heating
  and heating needs spread over a small surface); the order of 25 March
  2024 changed their class thresholds from 1 July 2024. ADEME's open data
  has no field saying whether a label was recalculated, so this was
  checked (2026-10-02, `scripts/analysis/dpe_2024_thresholds.py` and
  `dpe_small_surfaces.py`): every MGP certificate was reclassified from its
  own consumption and emissions with the official thresholds. Small-dwelling
  certificates issued **before** the reform match the 2024 rule for 99.8%
  of them (the 2021 rule: 92.9%), and those issued after it for 99.95% —
  the published labels have been recalculated. Applying the exact rule
  everywhere changes 0.06% of certificates and 10 IRIS scores, so nothing
  is applied. Small dwellings still have more F/G labels after the official
  correction (in Paris, 27.5% under 30 m² against 7.7% over 70 m²): that
  is in the data, not a scale artefact.
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

## Census 2022: reference and sensitivity check

**Decision (3 October 2026, before seeing any result, whatever the
result).** The 2022 census becomes the reference for population
(script 21), secondary residences (script 24) and overcrowding (script
25). Income stays Filosofi 2021: there is no later IRIS vintage
(Filosofi 2022 was never produced; the 2023 edition is published down to
the commune only, with a changed method). The 200 m population grid used
for access to care and the routes is also Filosofi 2021 (no later grid).
The differences with 2021 are published as a sensitivity check; the
verdicts of the pre-registered tests, computed with 2021, remain the
official results.

**Step 1 — differences with 2021, no crossing with means**
(`scripts/analysis/rp2022_sensitivity.py`, output
`data/interim/analysis/rp2022_sensitivity.txt`):
- population 6,852,439 → 6,862,396; inhabited IRIS 2,690 → 2,690;
- score on 4, inhabited IRIS: 765 / 1,248 / 597 / 76 / 4 → 765 / 1,249 /
  595 / 77 / 4; 16 IRIS change score, all by one point; IRIS at 3 or 4:
  80 → 81 (none leaves; Javel 21, Paris 15e, enters at 3); the same four
  IRIS at 4/4;
- highly exposed (2 of the 3 exposures): 406 → 407 (5 leave, 6 enter);
  access to care in the worst quarter: 672 → 672 (1 leaves, 1 enters);
  quarter changes: thermal 34 IRIS (1.2%), air/noise 3, housing 3,
  access to care 0;
- means axis: overcrowding median 13.5% → 24.6% (definition change, see
  "Adaptive capacity"), secondary residences median 2.4% → 2.5%; 474 of
  the 2,529 IRIS with an index change third (18.7%), always to a
  neighbouring third (none goes from lowest to highest or back); by
  département: Paris 21.2%, 92 19.7%, 93 12.9%, 94 20.1%.

**Step 2 — the published crossings redone with 2022, as a control**
(rule fixed before the results: each verdict gets a line "confirmed /
not confirmed" with its figures; a verdict not confirmed would be said
plainly, not replaced). All three are **confirmed**:
- access to care, supported — metro-wide gap +22.9 points (+29.4 with
  2021); Hauts-de-Seine 39.3% against 24.0%, Val-de-Marne 38.8% against
  27.9%;
- inclusive mobility, refuted — Paris still clearly reversed (52.3%
  against 66.2%); metro-wide 13.2% against 35.0%;
- public services, refuted and reversed — reversed in 92, 93 and 94 with
  no constraint, in all four step-free.

Details under each test above. The site's key figures (script 35) now
use 2022: 81 inhabited IRIS at 3 or 4; in Seine-Saint-Denis, 61.8% of
the highly exposed IRIS are in the lowest third of means (76.5% with
2021); Spearman(means, score) +0.09 (+0.11).

To revisit when INSEE publishes the 2023 census at IRIS level, or an
IRIS or grid version of the new Filosofi.

## Current distribution (MGP — Paris + Petite Couronne, 2,752 IRIS)

4 sub-scores (thermal, air/noise pollution, housing, access to care,
v0.2), quartile thresholds on inhabited IRIS (see above), 2022 census
(`data/processed/key_figures.json`):

| Cumulative score | IRIS count | Share |
|---|---|---|
| 0 | 774 | 28.1% |
| 1 | 1,287 | 46.8% |
| 2 | 608 | 22.1% |
| 3 | 79 | 2.9% |
| 4 | 4 | 0.1% |

Inhabited IRIS only (≥ 50 residents, 2,690): 765 / 1,249 / 595 / 77 / 4
(2021 census: 765 / 1,248 / 597 / 76 / 4). With the 2021 census, all
IRIS: 774 / 1,286 / 610 / 78 / 4. At the v0 launch (3 sub-scores,
inhabited IRIS): 1,113 / 1,171 / 375 / 31; the 31 inhabited IRIS at 3/3
all stayed at 3 or more with the score on 4, and the 49 that entered
scores 3-4 all did so through access to care (2021 census).

The 4 IRIS at 4/4: Asnières-sur-Seine Flachat I, Aulnay-sous-Bois
Nonneville 3 and Nonneville 4, Champigny-sur-Marne Quatre Cités 3
(unchanged by the census switch). The 81 inhabited IRIS at 3 or 4: 22 in
Paris, 23 in Hauts-de-Seine, 18 in Seine-Saint-Denis, 18 in Val-de-Marne
(2021: 80, with 21 in Paris).

Findings, 2022 census ("highly exposed" = 2 or more of the 3 exposures;
see "Adaptive capacity" for the detail): (1) highly exposed
neighbourhoods with the lowest means are mostly in Seine-Saint-Denis and
Val-de-Marne and combine mainly heat, air pollution and noise; those
with the highest means are mostly in Paris and combine mainly heat and
energy-inefficient housing. (2) The link between exposure and means is
weak, and slightly positive because of dense, older central Paris
(Spearman +0.09; +0.11 with 2021). (3) Share of the highly exposed in
the lowest third of means: Seine-Saint-Denis 61.8%, Val-de-Marne 24.5%,
Paris 4.5%, Hauts-de-Seine 1.9%. Access to care, separately: share of
inhabited IRIS in its worst quarter, Paris 2.2%, Hauts-de-Seine 28.4%,
Seine-Saint-Denis 50.0%, Val-de-Marne 32.5%.

Previous distributions: at the v0 launch, all IRIS, 1,122 / 1,216 / 382
/ 32; before access left the count (old 4 sub-scores), 874 / 1,230 / 586
/ 58 / 4.

**Public ranking (`/ranking`).** Lists the IRIS at 3 or 4 out of 4 with
at least **50 residents** — the same floor as `cool_facility_deficit`'s
per-resident rate (`MIN_POPULATION_FOR_RATE`): below it an IRIS is a
park, a station or a business block, not a neighborhood people live in
(62 IRIS in all are under 50 residents; they stay on the map, flagged
"very sparsely populated" in the detail panel). The 81 listed IRIS (80
with the 2021 census): the 4 at 4/4 first, flagged; then the others at
3/4 grouped by the means-to-cope tertile (lowest, middle, highest,
without published income), never by an implied cause, ordered by commune then name. Each row shows
one figure per category (sealed ground, air/noise index, F/G-rated
homes, GPs within reach) plus median income, each against the
metro-wide median. A department filter (native select, keyboard and
screen-reader ready, count announced) narrows the list. A paragraph
above the list states that it is not a ranking.

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
