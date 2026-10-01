"""Download and normalize median disposable income per IRIS (INSEE Filosofi).

Source: INSEE statistics page for "Revenus, pauvrete et niveau de vie en
2021 (Iris)" — the most recent Filosofi edition published at IRIS
granularity. INSEE only exposes a human-facing download page whose direct
file URL changes every edition, so the link is scraped rather than
hardcoded (see find_download_link in utils/download.py).

Unlike the other sources, Filosofi rows already carry the full 9-digit
IRIS code directly in a single "IRIS" column (confirmed by inspection:
filtering it to the 4 MGP department codes yields exactly the 2,752 IRIS
in our reference) — no spatial join needed, just an attribute join.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

import config
from utils.download import download_file, find_download_link
from utils.geo import check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "income_filosofi"

# Field names confirmed from the 2021 "BASE_TD_FILO_IRIS_2021_DISP" file:
# IRIS (full 9-digit code), DISP_MED21 (median disposable income),
# DISP_TP6021 (poverty rate), DISP_GI21 (Gini index). Adjust the "21"
# year suffix once INSEE publishes a newer edition.
IRIS_CODE_FIELD_CANDIDATES = ("IRIS", "iris")
MEDIAN_INCOME_PATTERN = "DISP_MED"
POVERTY_RATE_PATTERN = "TP60"
GINI_PATTERN = "DISP_GI"


def download() -> Path:
    # Confirmed by inspecting the page: INSEE ships both a "DEC" (deciles)
    # and a "DISP" (disposable income) file per format; we want DISP/CSV.
    file_url = find_download_link(config.INCOME_FILOSOFI_PAGE, r"BASE_TD_FILO_IRIS_\d{4}_DISP_CSV\.zip")
    dest = RAW_DIR / Path(file_url).name
    downloaded = download_file(file_url, dest)

    if downloaded.suffix == ".zip":
        from utils.download import extract_zip, find_extracted_file
        extract_zip(downloaded, RAW_DIR / "extracted")
        # The data file, not the "meta_…" data dictionary shipped alongside it.
        return find_extracted_file(
            RAW_DIR / "extracted", r"BASE_TD_FILO_IRIS_\d{4}_DISP\.(csv|xlsx)", "Filosofi IRIS income file"
        )
    return downloaded


def load_raw(path: Path) -> pd.DataFrame:
    if path.suffix == ".xlsx":
        return pd.read_excel(path, sheet_name=0, skiprows=5)  # INSEE files usually have a header block
    return pd.read_csv(path, sep=";")


def normalize(df: pd.DataFrame):
    iris_col = next((c for c in IRIS_CODE_FIELD_CANDIDATES if c in df.columns), None)
    if iris_col is None:
        raise RuntimeError(f"Could not find an IRIS code column among {list(df.columns)}.")

    df[config.IRIS_JOIN_COLUMN] = df[iris_col].astype(str)
    df = df[df[config.IRIS_JOIN_COLUMN].str[:2].isin(config.MGP_DEP_CODES)]

    median_col = next((c for c in df.columns if MEDIAN_INCOME_PATTERN in c.upper()), None)
    if median_col is None:
        raise RuntimeError(f"No median-income column matching '{MEDIAN_INCOME_PATTERN}*' found among {list(df.columns)}.")
    poverty_col = next((c for c in df.columns if POVERTY_RATE_PATTERN in c.upper()), None)
    gini_col = next((c for c in df.columns if GINI_PATTERN in c.upper()), None)

    keep_cols = {median_col: "median_income", **({poverty_col: "poverty_rate"} if poverty_col else {}), **({gini_col: "gini_index"} if gini_col else {})}
    result_df = df[[config.IRIS_JOIN_COLUMN, *keep_cols.keys()]].rename(columns=keep_cols)

    # INSEE encodes statistically masked small-IRIS values as "ns" (non
    # significatif) and uses a comma decimal separator (French locale).
    for col in keep_cols.values():
        result_df[col] = (
            result_df[col].astype(str).str.replace(",", ".", regex=False).replace("ns", pd.NA)
        )
        result_df[col] = pd.to_numeric(result_df[col], errors="coerce")

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_LATLON)
    check_unmatched_codes(result_df, iris, config.IRIS_JOIN_COLUMN)

    return iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(result_df, on=config.IRIS_JOIN_COLUMN, how="left")


def main():
    raw_path = download()
    df = load_raw(raw_path)
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "income_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
