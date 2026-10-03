"""Download and normalize municipal population per IRIS (INSEE recensement).

Source: INSEE statistics page "Population en 2021" (Recensement de la
Population, "base infra-communale/IRIS"), 2021 vintage — matching
Filosofi's vintage deliberately, so income and population figures refer
to the same reference year. Same scrape-a-stats-page pattern as
Filosofi in script 08 (INSEE only exposes a human-facing download page
whose direct file URL changes every edition).

Used to normalize count-based indicators (raw facility/association
counts) as rates per 1,000 inhabitants rather than raw counts or
per-km2 density alone — a larger or smaller IRIS/commune shouldn't look
better or worse served purely because of its size. Not itself a scored
indicator.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import config
from utils.download import download_file, extract_zip, find_download_link, find_extracted_file
from utils.geo import check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "population_iris"

# Field names confirmed from the 2021 "base-ic-evol-struct-pop" file:
# IRIS (full 9-digit code), P22_POP (total population). Census 2022 since
# 3 October 2026 (2021 before; the differences are published as a
# sensitivity check, scripts/analysis/rp2022_sensitivity.py).
IRIS_CODE_FIELD_CANDIDATES = ("IRIS", "iris")
POPULATION_FIELD_PATTERN = "P22_POP"


def download() -> Path:
    file_url = find_download_link(config.POPULATION_IRIS_PAGE, r"base-ic-evol-struct-pop-2022_csv\.zip")
    dest = RAW_DIR / Path(file_url).name
    downloaded = download_file(file_url, dest)

    extract_zip(downloaded, RAW_DIR / "extracted")
    # INSEE ships "base-ic-evol-struct-pop-<year>.CSV" (uppercase extension)
    # next to a "meta_…" data dictionary — match the data file by name.
    return find_extracted_file(
        RAW_DIR / "extracted", r"base-ic-evol-struct-pop-\d{4}\.csv", "INSEE IRIS population file"
    )


def load_raw(path: Path) -> pd.DataFrame:
    # IRIS codes as text: read as numbers, codes with a leading zero (Ariège,
    # "09...") lose it and some start with "92", like the bug fixed in script 24.
    return pd.read_csv(path, sep=";", dtype={"IRIS": str, "COM": str}, low_memory=False)


def normalize(df: pd.DataFrame):
    iris_col = next((c for c in IRIS_CODE_FIELD_CANDIDATES if c in df.columns), None)
    if iris_col is None:
        raise RuntimeError(f"Could not find an IRIS code column among {list(df.columns)}.")

    df[config.IRIS_JOIN_COLUMN] = df[iris_col].astype(str)
    df = df[df[config.IRIS_JOIN_COLUMN].str[:2].isin(config.MGP_DEP_CODES)]

    pop_col = next((c for c in df.columns if POPULATION_FIELD_PATTERN in c.upper()), None)
    if pop_col is None:
        raise RuntimeError(f"No population column matching '{POPULATION_FIELD_PATTERN}' found among {list(df.columns)}.")

    result_df = df[[config.IRIS_JOIN_COLUMN, pop_col]].rename(columns={pop_col: "population"})
    result_df["population"] = pd.to_numeric(result_df["population"], errors="coerce")

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_LATLON)
    check_unmatched_codes(result_df, iris, config.IRIS_JOIN_COLUMN)

    return iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(result_df, on=config.IRIS_JOIN_COLUMN, how="left")


def main():
    raw_path = download()
    df = load_raw(raw_path)
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "population_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
