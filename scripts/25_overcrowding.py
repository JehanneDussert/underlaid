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

Uses INSEE's own overcrowding definition (the "exploitation
complémentaire" variable C21_RP_HSTU1P_SUROCC): main residences, studios
occupied by one person excluded, with fewer rooms than the household's
"normal" need. Denominator C21_RP_HSTU1P is the same restricted set, so
the rate is exactly INSEE's published one.
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

OVERCROWDED_FIELD = "C21_RP_HSTU1P_SUROCC"
DENOMINATOR_FIELD = "C21_RP_HSTU1P"
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
    missing = [c for c in (OVERCROWDED_FIELD, DENOMINATOR_FIELD) if c not in df.columns]
    if missing:
        raise RuntimeError(f"Columns {missing} not found — INSEE may have renamed them for a new vintage.")

    df = df.copy()
    df[config.IRIS_JOIN_COLUMN] = df[iris_col].astype(str)
    df = df[df[config.IRIS_JOIN_COLUMN].str[:2].isin(config.MGP_DEP_CODES)]

    overcrowded = pd.to_numeric(df[OVERCROWDED_FIELD], errors="coerce")
    dwellings = pd.to_numeric(df[DENOMINATOR_FIELD], errors="coerce")
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
