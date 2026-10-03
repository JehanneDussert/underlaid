"""Normalize the housing overcrowding rate per IRIS (INSEE).

Source: the same INSEE "Logement en 2021" base infra-communale file
already downloaded by 24_secondary_residences.py (2021 vintage, matching
Filosofi and population_iris) — download() is shared with script 24 and
skips the download if the file is already on disk.

Phase 8, adaptive-capacity axis — never merged into any sub-score or the
cumulative exposure score (see SCORING.md, "Adaptive capacity"). An
overcrowded dwelling leaves no room to get away from the heat inside
one's own home: a direct limit on the means to cope, independent of how
exposed the neighborhood is.

Census 2022 since 3 October 2026. INSEE changed the definition with that
edition: the 2021 variable (C21_RP_HSTU1P_SUROCC, main residences
excluding studios occupied by one person) no longer exists; the 2022 base
gives moderate and severe overcrowding over all main residences
(C22_RP_SUROCC_MOD + C22_RP_SUROCC_ACC). Both come from INSEE's
complementary (sample-based) count, so the denominator is the sum of all
occupation categories of that same count (C22_RP_NORME, _SOUSOCC_MOD,
_ACC, _TACC, _SUROCC_MOD, _ACC): dividing by the main count P22_RP gave a
rate above 1 in one neighbourhood. The median
rate goes from 13.5% to 24.4% because of this change of definition, not of
a real change (published in the method as part of the 2021/2022
sensitivity check).
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config
from utils.geo import check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

OVERCROWDED_FIELDS = ["C22_RP_SUROCC_MOD", "C22_RP_SUROCC_ACC"]
DENOMINATOR_FIELDS = ["C22_RP_NORME", "C22_RP_SOUSOCC_MOD", "C22_RP_SOUSOCC_ACC", "C22_RP_SOUSOCC_TACC", *OVERCROWDED_FIELDS]
# Same floor as pct_secondary_residences (script 24): below 20 dwellings a
# rate is a handful of households, not a neighborhood figure.
MIN_DWELLINGS_FOR_RATE = 20


def load_secondary_residences_module():
    # Script 24 owns the download of this shared INSEE file; its numbered
    # filename can't be imported with a plain import statement.
    path = Path(__file__).resolve().parent / "24_secondary_residences.py"
    spec = importlib.util.spec_from_file_location("secondary_residences", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(df: pd.DataFrame, iris_code_candidates) -> pd.DataFrame:
    iris_col = next((c for c in iris_code_candidates if c in df.columns), None)
    if iris_col is None:
        raise RuntimeError(f"Could not find an IRIS code column among {list(df.columns)}.")
    missing = [c for c in DENOMINATOR_FIELDS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Columns {missing} not found — INSEE may have renamed them for a new vintage.")

    df = df.copy()
    df[config.IRIS_JOIN_COLUMN] = df[iris_col].astype(str)
    df = df[df[config.IRIS_JOIN_COLUMN].str[:2].isin(config.MGP_DEP_CODES)]

    overcrowded = sum(pd.to_numeric(df[f], errors="coerce") for f in OVERCROWDED_FIELDS)
    dwellings = sum(pd.to_numeric(df[f], errors="coerce") for f in DENOMINATOR_FIELDS)
    denom = dwellings.where(dwellings >= MIN_DWELLINGS_FOR_RATE)
    # 0-1 fraction, like every other pct_* field in this pipeline. np.nan
    # (never 0) where the floor isn't met.
    df["pct_overcrowded"] = (overcrowded / denom).astype(float)
    df.loc[denom.isna(), "pct_overcrowded"] = np.nan
    return df[[config.IRIS_JOIN_COLUMN, "pct_overcrowded"]]


def main():
    shared = load_secondary_residences_module()
    raw_path = shared.download()
    df = shared.load_raw(raw_path)
    result_df = normalize(df, shared.IRIS_CODE_FIELD_CANDIDATES)

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_LATLON)
    check_unmatched_codes(result_df, iris, config.IRIS_JOIN_COLUMN)
    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(result_df, on=config.IRIS_JOIN_COLUMN, how="left")
    save_geojson(
        result,
        config.DATA_PROCESSED / "overcrowding_iris.geojson",
        required_cols=[config.IRIS_JOIN_COLUMN, "geometry"],
    )


if __name__ == "__main__":
    main()
