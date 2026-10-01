"""Download and normalize the secondary-residence rate per IRIS (INSEE).

Source: INSEE statistics page "Logement en 2021" (Recensement de la
Population, "base infra-communale/IRIS"), 2021 vintage — matching
Filosofi's and population_iris's vintage deliberately, same
scrape-a-stats-page pattern as scripts 08/21 (INSEE only exposes a
human-facing download page whose direct file URL changes every
edition).

Not a scored indicator, and never merged into any sub-score or the
cumulative score — see SCORING.md's "What this score doesn't measure".
A high secondary-residence rate is a direct proxy for the capacity to
physically leave during a heatwave (a second home elsewhere), which
median income only captures indirectly. Kept alongside median_income in
11_compute_vulnerability_score.py's output as unscored context, in the
same spot and for the same reason.

P21_RSECOCC counts "résidences secondaires et logements occasionnels"
together — INSEE doesn't publish a IRIS-level breakdown that isolates
pure secondary residences from occasional/seasonal dwellings, so the
rate below is a proxy for both combined, not secondary residences alone.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import config
from utils.download import download_file, extract_zip, find_download_link, find_extracted_file
from utils.geo import check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "secondary_residences_iris"
SECONDARY_RESIDENCES_PAGE = "https://www.insee.fr/fr/statistiques/8268838"

# Field names confirmed from the 2021 "base-ic-logement" data dictionary:
# IRIS (full 9-digit code), P21_LOG (total housing units), P21_RSECOCC
# (secondary residences + occasional dwellings).
IRIS_CODE_FIELD_CANDIDATES = ("IRIS", "iris")
TOTAL_HOUSING_FIELD_PATTERN = "P21_LOG"
SECONDARY_RESIDENCES_FIELD_PATTERN = "P21_RSECOCC"


def download() -> Path:
    file_url = find_download_link(SECONDARY_RESIDENCES_PAGE, r"base-ic-logement-2021_csv\.zip")
    dest = RAW_DIR / Path(file_url).name
    downloaded = download_file(file_url, dest)

    extract_zip(downloaded, RAW_DIR / "extracted")
    # Same INSEE layout as script 21: "base-ic-logement-<year>.CSV" + "meta_…".
    return find_extracted_file(
        RAW_DIR / "extracted", r"base-ic-logement-\d{4}\.csv", "INSEE IRIS housing file"
    )


def load_raw(path: Path) -> pd.DataFrame:
    # IRIS codes read as text: parsed as numbers, codes with a leading zero
    # (e.g. Ariège, "09...") lose it and some then start with "92", slipping
    # through the MGP department filter as bogus 8-digit codes.
    return pd.read_csv(path, sep=";", dtype={code: str for code in IRIS_CODE_FIELD_CANDIDATES}, low_memory=False)


def normalize(df: pd.DataFrame):
    iris_col = next((c for c in IRIS_CODE_FIELD_CANDIDATES if c in df.columns), None)
    if iris_col is None:
        raise RuntimeError(f"Could not find an IRIS code column among {list(df.columns)}.")

    df[config.IRIS_JOIN_COLUMN] = df[iris_col].astype(str)
    df = df[df[config.IRIS_JOIN_COLUMN].str[:2].isin(config.MGP_DEP_CODES)]

    total_col = next((c for c in df.columns if TOTAL_HOUSING_FIELD_PATTERN in c.upper()), None)
    if total_col is None:
        raise RuntimeError(f"No column matching '{TOTAL_HOUSING_FIELD_PATTERN}' found among {list(df.columns)}.")
    secondary_col = next((c for c in df.columns if SECONDARY_RESIDENCES_FIELD_PATTERN in c.upper()), None)
    if secondary_col is None:
        raise RuntimeError(f"No column matching '{SECONDARY_RESIDENCES_FIELD_PATTERN}' found among {list(df.columns)}.")

    result_df = df[[config.IRIS_JOIN_COLUMN, total_col, secondary_col]].rename(
        columns={total_col: "total_housing_units", secondary_col: "secondary_residences_count"}
    )
    result_df["total_housing_units"] = pd.to_numeric(result_df["total_housing_units"], errors="coerce")
    result_df["secondary_residences_count"] = pd.to_numeric(result_df["secondary_residences_count"], errors="coerce")

    # Same population-floor reasoning already applied to cool_facility_deficit
    # (see SCORING.md): a tiny non-residential IRIS with 2 housing units, one
    # of them a secondary residence, would show a 50% rate that says nothing
    # meaningful. This is context, not a scored indicator, so no winsorizing
    # is applied — just a floor to avoid a divide-by-near-zero rate showing
    # up in the UI as a real percentage.
    MIN_HOUSING_UNITS_FOR_RATE = 20
    denom = result_df["total_housing_units"].where(result_df["total_housing_units"] >= MIN_HOUSING_UNITS_FOR_RATE)
    # Stored as a 0-1 fraction, not 0-100 — matches every other pct_*
    # field already in this pipeline (pct_artificialized, pct_dpe_fg,
    # etc.), which the frontend's formatPercent()/cityMedianNote()
    # helpers multiply by 100 at display time.
    result_df["pct_secondary_residences"] = result_df["secondary_residences_count"] / denom

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_LATLON)
    check_unmatched_codes(result_df, iris, config.IRIS_JOIN_COLUMN)

    return iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(
        result_df[[config.IRIS_JOIN_COLUMN, "pct_secondary_residences"]], on=config.IRIS_JOIN_COLUMN, how="left"
    )


def main():
    raw_path = download()
    df = load_raw(raw_path)
    result = normalize(df)
    save_geojson(
        result,
        config.DATA_PROCESSED / "secondary_residences_iris.geojson",
        required_cols=[config.IRIS_JOIN_COLUMN, "geometry"],
    )


if __name__ == "__main__":
    main()
