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

import geopandas as gpd
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

def test_subscore_status_values_are_known():
    gdf = load("vulnerability_score_iris.geojson")
    for name in ["thermal", "pollution", "access", "housing"]:
        values = set(gdf[f"subscore_{name}_status"].dropna().unique())
        assert values <= {"ok", "insufficient_data"}, (
            f"subscore_{name}_status has unexpected values: {values - {'ok', 'insufficient_data'}}"
        )


def test_cumulative_score_is_in_valid_range():
    gdf = load("vulnerability_score_iris.geojson")
    scored = gdf["cumulative_vulnerability_score"].dropna()
    assert scored.between(0, 4).all(), "cumulative_vulnerability_score must be 0-4 (or null)"


def test_cumulative_score_distribution_is_plausible():
    """Regression guard for the exact bias this test suite exists to catch:

    before the minimum-indicator threshold fix, sparse-data IRIS landed in
    a sub-score's worst quartile at ~47% instead of the ~25% chance rate.
    If any single cumulative score value balloons past a third of all
    IRIS, or if score=4 becomes implausibly common, something regressed.
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
    for name in ["thermal", "pollution", "access", "housing"]:
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
    status_cols = [f"subscore_{name}_status" for name in ["thermal", "pollution", "access", "housing"]]
    expected_n = (gdf[status_cols] == "ok").sum(axis=1)
    assert (gdf["n_subscores_evaluated"] == expected_n).all(), (
        "n_subscores_evaluated doesn't match the count of 'ok' sub-score statuses"
    )
