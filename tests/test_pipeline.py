"""Minimal regression tests for the data pipeline and scoring.

Run after scripts/run_all.py (or at minimum after
11_compute_vulnerability_score.py) has produced data/processed/*.geojson.
Not run on every commit — there's no CI wired to this repo's normal push/PR
flow, only .github/workflows/update-pipeline.yml's quarterly re-run of the
pipeline itself (see README/SCORING.md). This is the "does a new source
silently break something" smoke test, plus a standing regression guard for
the sparse-data quartile bias found early in this project.

Run with: pytest tests/ -v
"""
import sys
from pathlib import Path

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import config

# Metropole du Grand Paris, Petite Couronne (Phase 5): 2,752 IRIS across
# 4 departments (75 Paris: 992, 92 Hauts-de-Seine: 616, 93
# Seine-Saint-Denis: 614, 94 Val-de-Marne: 530), confirmed via direct
# query against the source IRIS dataset.
EXPECTED_IRIS_COUNT = 2752


def load(name: str) -> gpd.GeoDataFrame:
    path = config.DATA_PROCESSED / name
    if not path.exists():
        pytest.skip(f"{name} not found — run the pipeline first")
    return gpd.read_file(path)


# --- Every per-IRIS layer must have exactly 2,752 rows, one per IRIS ---

PER_IRIS_LAYERS = [
    "iris_mgp.geojson",
    "icu_iris.geojson",
    "cool_spots_facilities_iris.geojson",
    "cool_spots_green_iris.geojson",
    "air_noise_iris.geojson",
    "bpe_iris.geojson",
    "equipment_access_iris.geojson",
    "income_iris.geojson",
    "social_index_iris.geojson",
    "energy_performance_iris.geojson",
    "accessibility_iris.geojson",
    "street_lighting_iris.geojson",
    "pedestrian_paths_iris.geojson",
    "enedis_thermosensitivity_iris.geojson",
    "artificialization_iris.geojson",
    "population_iris.geojson",
    "secondary_residences_iris.geojson",
    "overcrowding_iris.geojson",
    "vulnerability_score_iris.geojson",
]


@pytest.mark.parametrize("filename", PER_IRIS_LAYERS)
def test_layer_has_all_iris(filename):
    gdf = load(filename)
    assert len(gdf) == EXPECTED_IRIS_COUNT, (
        f"{filename} has {len(gdf)} rows, expected {EXPECTED_IRIS_COUNT} "
        "(one per MGP IRIS) — a join probably dropped or duplicated rows"
    )


def test_code_iris_is_unique_and_well_formed():
    gdf = load("vulnerability_score_iris.geojson")
    assert gdf["code_iris"].is_unique, "duplicate code_iris values in the scored output"
    dept_pattern = "|".join(config.MGP_DEP_CODES)
    assert gdf["code_iris"].str.match(rf"^({dept_pattern})\d{{7}}$").all(), (
        f"code_iris should be 9 digits starting with one of {config.MGP_DEP_CODES}"
    )


# --- Layers with a different, documented granularity ---

def test_qpv_boundaries_is_mgp_subset():
    gdf = load("qpv_boundaries_mgp.geojson")
    # Documented: 162 across the 4 departments (75: 21, 92: 19, 93: 75,
    # 94: 47), confirmed via direct query. Allow some drift if ANCT
    # revises QPV boundaries, but not an order-of-magnitude jump.
    assert 0 < len(gdf) <= 250, "QPV MGP count looks implausible (expected ~162, documented count)"


def test_school_ac_context_has_20_arrondissements():
    gdf = load("school_ac_context_arrondissement.geojson")
    # Paris-only by design (Phase 5): the source is hand-compiled from
    # Paris press coverage, no equivalent exists for 92/93/94.
    assert len(gdf) == 20, "school AC context is one row per Paris arrondissement, expected 20"


def test_tree_age_context_has_20_arrondissements():
    gdf = load("tree_age_context_arrondissement.geojson")
    # Paris-only by design (Phase 5): opendata.paris.fr's tree inventory
    # has no Petite Couronne equivalent.
    assert len(gdf) == 20, "tree age context is one row per Paris arrondissement, expected 20"
    assert gdf["avg_circumference_cm"].notna().all(), "every arrondissement has trees, none should be null"


def test_street_lighting_context_has_20_arrondissements():
    gdf = load("street_lighting_context_arrondissement.geojson")
    # Paris-only by design (Phase 5): opendata.paris.fr's lighting
    # dataset has no Petite Couronne equivalent.
    assert len(gdf) == 20, "street lighting context is one row per Paris arrondissement, expected 20"
    assert gdf["lamps_per_km2"].notna().all(), "every Paris arrondissement has street lighting, none should be null"


def test_associational_density_context_covers_all_mgp_communes():
    gdf = load("associational_density_context_commune.geojson")
    # RNA is genuinely region-wide (Phase 5): rescoped from 20
    # arrondissement rows to ~143 commune rows across all 4 departments.
    assert len(gdf) >= 130, "associational density context should cover ~143 MGP communes, not just Paris"
    # Confirmed by direct query (not a pagination bug): the source has a
    # genuine, complete gap for Pierrefitte-sur-Seine (93059) — zero RNA
    # records under that commune code at any status, despite it being a
    # real town of ~30k residents. One known gap is tolerated; more would
    # signal a real join/fetch problem, not a source quirk.
    n_missing = gdf["associations_per_km2"].isna().sum()
    assert n_missing <= 2, f"{n_missing} communes missing associational data — expected at most 1 (Pierrefitte-sur-Seine)"
    assert gdf["associations_per_1000_inhabitants"].notna().sum() >= len(gdf) - 2, "population should be present for nearly every commune"


# --- Known, documented NaN patterns — these should NOT silently change shape ---

def test_income_masking_rate_is_in_expected_range():
    gdf = load("income_iris.geojson")
    n_masked = gdf["median_income"].isna().sum()
    # Documented: 223/2752 as of this writing (Phase 5, MGP scale). Allow
    # drift if INSEE ships a new Filosofi edition, but a big jump signals
    # something else broke.
    assert 100 <= n_masked <= 600, (
        f"{n_masked}/2752 IRIS have a masked median_income — expected roughly "
        "200-300 based on Filosofi's small-population masking; investigate "
        "if this moved a lot (either the source changed, or the join broke)"
    )


def test_income_related_columns_are_masked_together():
    gdf = load("income_iris.geojson")
    # Where median_income is null, poverty_rate/gini_index should be null
    # too (INSEE masks the whole row, not individual columns).
    masked = gdf[gdf["median_income"].isna()]
    assert masked["poverty_rate"].isna().all(), "poverty_rate present without median_income — masking logic changed?"
    assert masked["gini_index"].isna().all(), "gini_index present without median_income — masking logic changed?"


def test_secondary_residences_rate_is_a_0_to_1_fraction():
    gdf = load("secondary_residences_iris.geojson")
    # Stored as a 0-1 fraction like every other pct_* field in this
    # pipeline (see 11_compute_vulnerability_score.py's output_cols
    # comment) — a value > 1 would mean it was accidentally left on the
    # 0-100 scale the frontend's formatPercent()/cityMedianNote() don't
    # expect.
    values = gdf["pct_secondary_residences"].dropna()
    assert len(values) > 0, "pct_secondary_residences is entirely null — join likely broke"
    assert values.between(0, 1).all(), "pct_secondary_residences should be a 0-1 fraction, found a value outside that range"


# --- Scoring output sanity ---

# The 4 scored sub-scores. Access left the count at the v0 launch and came
# back in v0.2 as "access to care" (E2SFCA, scripts 27-32; SCORING.md,
# "Access to care"). The inclusive-mobility gap is information only.
SCORED_SUBSCORES = ["thermal", "pollution", "housing", "access_care"]

def test_subscore_status_values_are_known():
    gdf = load("vulnerability_score_iris.geojson")
    for name in SCORED_SUBSCORES:
        values = set(gdf[f"subscore_{name}_status"].dropna().unique())
        assert values <= {"ok", "insufficient_data"}, (
            f"subscore_{name}_status has unexpected values: {values - {'ok', 'insufficient_data'}}"
        )


def test_cumulative_score_is_in_valid_range():
    gdf = load("vulnerability_score_iris.geojson")
    scored = gdf["cumulative_vulnerability_score"].dropna()
    assert scored.between(0, 4).all(), "cumulative_vulnerability_score must be 0-4 (or null)"


def test_access_care_is_scored_and_mobility_is_information_only():
    """Access to care is a scored sub-score; the inclusive-mobility gap is
    carried for information and must never become a sub-score (it compares
    two ways of travelling in the same place, not places — decision of
    2026-10-02, CLAUDE.md)."""
    gdf = load("vulnerability_score_iris.geojson")
    columns = set(gdf.columns)
    assert {"subscore_access_care", "subscore_access_care_quartile", "subscore_access_care_status"} <= columns
    assert not {c for c in columns if c.startswith("subscore_mobility")}, "inclusive mobility must not be a sub-score"
    assert {"gp_std", "pharmacy_std", "gp_acc_no", "gp_gap_no", "gp_gap_yes"} <= columns
    gap = gdf["gp_gap_no"].dropna()
    # Accessible travel can't beat unrestricted travel (script 32 caps each
    # pair); 1.01 leaves room for rounding in the IRIS averages.
    assert gap.between(0, 1.01).all(), f"inclusive-mobility gap outside [0, 1]: {gap.min():.3f}-{gap.max():.3f}"
    # Unroutable IRIS (no GP or pharmacy reached at all) are rare.
    assert gdf["gp_std"].isna().sum() <= 10, "too many IRIS without an access value — routing broke?"


def test_access_file_covers_every_iris():
    df = pd.read_csv(config.DATA_PROCESSED / "access_e2sfca_iris.csv", dtype={"code_iris": str})
    assert len(df) == 2752 and df["code_iris"].is_unique


def test_cumulative_score_distribution_is_plausible():
    """Regression guard for the exact bias this test suite exists to catch:

    before the minimum-indicator threshold fix, sparse-data IRIS landed in
    a sub-score's worst quartile at ~47% instead of the ~25% chance rate.
    If any single cumulative score value balloons past a third of all
    IRIS, or if the top scores (3/4, 4/4) become implausibly common, something regressed.
    """
    gdf = load("vulnerability_score_iris.geojson")
    counts = gdf["cumulative_vulnerability_score"].value_counts(normalize=True, dropna=True)

    assert counts.get(0, 0) < 0.60, "over 60% of IRIS at score 0 would be an implausibly clean city"
    for score in (3, 4):
        share = counts.get(score, 0)
        assert share < 0.15, (
            f"score={score} accounts for {share:.1%} of IRIS — implausibly high; "
            "check whether a sub-score's quartile ranking is skewed again "
            "(see SCORING.md's minimum-indicator threshold section)"
        )


def test_subscore_quartiles_are_roughly_balanced():
    """The actual regression test for the 47%-vs-25% bias: among IRIS with

    a valid ("ok") sub-score, no quartile should dominate. A skew here is
    exactly the signature of sparse-data IRIS distorting the percentile
    ranking, which is what the minimum-indicator threshold exists to
    prevent (see SCORING.md).
    """
    gdf = load("vulnerability_score_iris.geojson")
    for name in SCORED_SUBSCORES:
        ok = gdf[gdf[f"subscore_{name}_status"] == "ok"]
        if ok.empty:
            continue
        share = ok[f"subscore_{name}_quartile"].value_counts(normalize=True)
        max_share = share.max()
        assert max_share < 0.35, (
            f"subscore_{name}: one quartile holds {max_share:.1%} of 'ok' IRIS "
            "(expected close to 25%) — likely the sparse-data bias is back; "
            "check SUB_SCORE_MIN_INDICATORS in 11_compute_vulnerability_score.py"
        )


def test_n_subscores_evaluated_is_consistent():
    gdf = load("vulnerability_score_iris.geojson")
    status_cols = [f"subscore_{name}_status" for name in SCORED_SUBSCORES]
    expected_n = (gdf[status_cols] == "ok").sum(axis=1)
    assert (gdf["n_subscores_evaluated"] == expected_n).all(), (
        "n_subscores_evaluated doesn't match the count of 'ok' sub-score statuses"
    )


# --- Phase 8: adaptive-capacity axis (separate from the exposure score) ---

def load_capacity() -> pd.DataFrame:
    path = config.DATA_PROCESSED / "adaptive_capacity_iris.json"
    if not path.exists():
        pytest.skip("adaptive_capacity_iris.json not found — run the pipeline first")
    return pd.DataFrame(json.loads(path.read_text(encoding="utf-8"))["iris"])


def test_overcrowding_rate_is_a_0_to_1_fraction():
    values = load("overcrowding_iris.geojson")["pct_overcrowded"].dropna()
    assert len(values) > 2000, "pct_overcrowded mostly null — join or column name likely broke"
    assert values.between(0, 1).all(), "pct_overcrowded should be a 0-1 fraction"


def test_capacity_file_has_one_row_per_iris():
    cap = load_capacity()
    score = load("vulnerability_score_iris.geojson")
    assert len(cap) == EXPECTED_IRIS_COUNT and cap["code_iris"].is_unique
    assert set(cap["code_iris"]) == set(score["code_iris"])


def test_capacity_masking_follows_income_masking():
    """Documented null share: the index exists only where INSEE publishes
    median income (the anchor) — 223/2,752 masked as of the 2021 vintage.
    Never imputed: masked IRIS must stay null, not become 0 or a median.
    """
    cap = load_capacity().merge(
        load("vulnerability_score_iris.geojson")[["code_iris", "median_income"]], on="code_iris"
    )
    n_masked = cap["capacity_index"].isna().sum()
    assert 100 <= n_masked <= 600, f"{n_masked} IRIS without a capacity index — expected ~223"
    assert (cap["capacity_index"].isna() == cap["median_income"].isna()).all(), (
        "capacity_index should be null exactly where median_income is masked"
    )
    assert (cap["capacity_class"].isna() == cap["capacity_index"].isna()).all()


def test_capacity_tertiles_are_balanced():
    share = load_capacity()["capacity_class"].value_counts(normalize=True)
    assert set(share.index) == {0, 1, 2}
    assert share.between(0.30, 0.37).all(), f"capacity tertiles unbalanced: {share.to_dict()}"


def test_exposure_class_matches_cumulative_score():
    cap = load_capacity().merge(
        load("vulnerability_score_iris.geojson")[["code_iris", "cumulative_vulnerability_score"]], on="code_iris"
    )
    expected = cap["cumulative_vulnerability_score"].clip(upper=2)
    assert (cap["exposure_class"] == expected).all(), "exposure_class should be 0, 1, or 2 for a score of 2+"


def test_no_bivariate_cell_is_anomalously_overrepresented():
    """Anti-bias guard, same spirit as the quartile-balance test above: no
    cell of the 3x3 grid should hold wildly more IRIS than it would if
    exposure and capacity were independent, and the masked IRIS must not
    pile up in one exposure class (they'd then silently vanish from one
    part of the map).

    Bound history: first run (4-sub-score exposure) 0.72-1.31x, guarded at
    0.4-2.0x. With access out of the score (v0 launch), exposure follows
    means more (Spearman +0.28, driven by dense, older central Paris):
    "2+ exposures / highest means" is 1.88x, "2+ / lowest means" 0.36x —
    a documented finding, not a data artefact. Bounds now 0.2-2.5x: the
    ceiling catches a cell anomalously over-filled; the floor sits well
    below the lowest real cell (0.36x) — a cell under-filled because of
    the data is a result to report, not a bias — and only catches a future
    bug that would empty a cell (e.g. a broken join or class mapping).
    """
    cap = load_capacity()
    rated = cap.dropna(subset=["capacity_class"])
    grid = pd.crosstab(rated["exposure_class"], rated["capacity_class"])
    expected = np.outer(grid.sum(axis=1), grid.sum(axis=0)) / grid.values.sum()
    ratio = grid.values / expected
    assert ratio.max() < 2.5 and ratio.min() > 0.2, f"bivariate grid badly skewed (obs/expected): {ratio.round(2).tolist()}"

    overall = cap["exposure_class"].value_counts(normalize=True)
    masked = cap[cap["capacity_class"].isna()]["exposure_class"].value_counts(normalize=True)
    gap = (masked.reindex(overall.index, fill_value=0) - overall).abs().max()
    assert gap < 0.10, f"masked IRIS concentrated in one exposure class (max gap {gap:.1%})"


def test_capacity_never_leaks_into_the_exposure_score():
    """Non-negotiable principle (CLAUDE.md/SCORING.md): adaptive capacity is
    a separate axis. The exposure score output must not carry it."""
    columns = set(load("vulnerability_score_iris.geojson").columns)
    leaked = {c for c in columns if "capacity" in c or c == "pct_overcrowded"}
    assert not leaked, f"capacity fields found in the exposure score output: {leaked}"


# --- Sparse-data bias, per indicator count (not just overall) ---

def _indicator_availability(gdf):
    """Which of each sub-score's indicators are present per IRIS, rebuilt
    from the raw figures carried in the scored output (same validity rules
    as 11_compute_vulnerability_score.py: cool-facility rate needs
    population >= 50)."""
    return {
        "thermal": [
            gdf["hvi"].notna(),
            gdf["cool_spots_within_400m"].notna() & (gdf["population"] >= 50),
            gdf["pct_cool_green_area"].notna(),
            gdf["pct_artificialized"].notna(),
        ],
        "housing": [gdf["pct_dpe_fg"].notna(), gdf["pct_thermosensitive"].notna()],
        "pollution": [gdf["air_noise_coexposure_class"].notna()],
        "access_care": [gdf["gp_std"].notna(), gdf["pharmacy_std"].notna()],
    }


MIN_GROUP_SIZE = 100
MAX_Q4_RATIO = 1.5


@pytest.mark.parametrize("name", SCORED_SUBSCORES)
def test_worst_quartile_share_does_not_depend_on_indicator_count(name):
    """The overall quartile check above can pass while the bias it exists
    to catch is still there: every sub-score is split into exact quartiles
    overall, so the skew only shows up when IRIS are grouped by how many of
    its indicators they actually have. IRIS computed from fewer indicators
    must not land in the worst quartile much more (or less) often than
    fully-documented ones.

    Threshold: among groups of >= 100 IRIS, the highest worst-quartile share
    must stay under 1.5x the lowest. The original sparse-data bias (47% vs
    25%, ratio ~1.9) fails it; thermal as of this writing (30.2% with 3
    indicators vs 24.6% with 4, ratio 1.23) passes. Access failed it (29.6%
    with 3 indicators vs 17.6% with 4, ratio 1.68) — one of the reasons it
    left the score at the v0 launch. Access to care (v0.2) passes it: both
    its indicators come from the same routing run, so an IRIS has both or
    neither.
    """
    gdf = load("vulnerability_score_iris.geojson")
    n_available = sum(col.astype(int) for col in _indicator_availability(gdf)[name])
    ok = gdf[f"subscore_{name}_status"] == "ok"
    groups = (
        pd.DataFrame({"n": n_available[ok], "q4": gdf.loc[ok, f"subscore_{name}_quartile"] == 4})
        .groupby("n")["q4"]
        .agg(["size", "mean"])
    )
    groups = groups[groups["size"] >= MIN_GROUP_SIZE]
    if len(groups) < 2:
        return  # a single indicator-count group: nothing to compare
    ratio = groups["mean"].max() / groups["mean"].min()
    detail = ", ".join(f"{int(n)} indicators: {row['mean']:.1%} of {int(row['size'])}" for n, row in groups.iterrows())
    assert ratio < MAX_Q4_RATIO, (
        f"subscore_{name}: worst-quartile share depends on how many indicators an IRIS has "
        f"({detail}; ratio {ratio:.2f} >= {MAX_Q4_RATIO}) — sparse-data bias"
    )


def test_quartile_thresholds_come_from_inhabited_iris():
    """Quartile thresholds are set by IRIS with >= 50 residents only
    (MIN_POPULATION_FOR_RATE, see SCORING.md "Quartile thresholds:
    inhabited IRIS only"): among them, every scored sub-score is split
    into exact quartiles. IRIS under 50 residents are placed against those
    thresholds afterwards — they must still get a quartile, never be
    silently dropped from the map."""
    gdf = load("vulnerability_score_iris.geojson")
    inhabited = gdf["population"] >= 50
    assert (~inhabited).sum() > 0, "expected some IRIS under 50 residents (parks, stations...)"
    for name in SCORED_SUBSCORES:
        ok = gdf[f"subscore_{name}_status"] == "ok"
        share = gdf.loc[ok & inhabited, f"subscore_{name}_quartile"].value_counts(normalize=True)
        assert share.between(0.24, 0.26).all(), (
            f"subscore_{name}: quartiles among inhabited IRIS are not exact ({share.round(3).to_dict()}) — "
            "thresholds may be computed on the wrong population"
        )
        assert gdf.loc[ok & ~inhabited, f"subscore_{name}_quartile"].notna().all(), (
            f"subscore_{name}: an IRIS under 50 residents lost its quartile"
        )


def test_key_figures_match_the_published_score():
    """The figures quoted in the site's sentences (script 35) come from the
    published score, not from a hand-typed copy that could drift."""
    figures = json.loads((config.DATA_PROCESSED / "key_figures.json").read_text(encoding="utf-8"))
    score = load("vulnerability_score_iris.geojson")
    s = score["cumulative_vulnerability_score"]
    inhabited = score[score["population"] >= 50]
    assert figures["n_iris"] == len(score)
    assert figures["distribution"] == {str(k): int((s == k).sum()) for k in range(5)}
    assert sum(figures["distribution_inhabited"].values()) == len(inhabited)
    assert len(figures["at_max"]) == int((inhabited["cumulative_vulnerability_score"] == 4).sum())
    assert figures["n_three_plus_inhabited"] == int((inhabited["cumulative_vulnerability_score"] >= 3).sum())
    assert sum(figures["three_plus_by_department"].values()) == figures["n_three_plus_inhabited"]
    example = score[score["code_iris"] == figures["example"]["code_iris"]].iloc[0]
    assert figures["example"]["score"] == int(example["cumulative_vulnerability_score"])
    # "Highly exposed" = 2 or more of the 3 exposures, access to care never
    # counted (decision of 3 October 2026).
    cap = pd.DataFrame(json.loads((config.DATA_PROCESSED / "adaptive_capacity_iris.json").read_text(encoding="utf-8"))["iris"])
    df = score.merge(cap[["code_iris", "capacity_class"]], on="code_iris")
    df = df[df["capacity_class"].notna()]
    exposures = sum((df[f"subscore_{k}_quartile"] == 4).astype(int) for k in ["thermal", "pollution", "housing"])
    high93 = df[(exposures >= 2) & (df["code_iris"].str[:2] == "93")]
    assert figures["highly_exposed_lowest_third_pct"]["93"] == round(100 * float((high93["capacity_class"] == 0).mean()), 1)
