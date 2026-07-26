"""Download and normalize PMR (wheelchair/mobility) accessibility of ERPs per IRIS.

Source: Acceslibre bulk CSV export on static.data.gouv.fr (~524MB, all of
France). The live Acceslibre API requires an API key; this static mirror
doesn't, so it's used instead — filtered to the 4 MGP departments
(code_insee's first 2 digits) while reading in chunks.

Data quality note: this is a crowdsourced database — most fields
(including entree_pmr, the wheelchair-accessible-entrance flag) are only
filled in for a minority of establishments (~19% in a spot check).
pct_pmr_accessible is computed only over establishments where the field
was actually documented, not over all of them.

Intended use (step 2): enriches the "access to services" sub-score
alongside BPE/IPS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson

RAW_CSV = config.DATA_RAW / "accessibility_erp" / "acceslibre.csv"
CHUNK_SIZE = 200_000


def download() -> Path:
    from utils.download import download_file
    return download_file(config.ACCESSIBILITY_CSV_URL, RAW_CSV)


def load_mgp_rows(csv_path: Path) -> pd.DataFrame:
    columns = ["code_insee", "longitude", "latitude", "entree_pmr"]
    chunks = []
    for chunk in pd.read_csv(csv_path, usecols=columns, chunksize=CHUNK_SIZE, low_memory=False):
        mgp_chunk = chunk[chunk["code_insee"].astype(str).str[:2].isin(config.MGP_DEP_CODES)]
        if not mgp_chunk.empty:
            chunks.append(mgp_chunk)
    if not chunks:
        raise RuntimeError(f"No rows matched departments {config.MGP_DEP_CODES} in {csv_path}.")
    return pd.concat(chunks, ignore_index=True)


def normalize(df: pd.DataFrame) -> gpd.GeoDataFrame:
    df = df.dropna(subset=["longitude", "latitude"])
    points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs=config.CRS_LATLON)

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    joined = join_points_to_iris(points.to_crs(iris.crs), iris, config.IRIS_JOIN_COLUMN)
    joined = joined.dropna(subset=[config.IRIS_JOIN_COLUMN])

    # pandas parses this column's "True"/"False" text as actual Python
    # bool objects (not strings) inside an object-dtype column (mixed
    # with NaN for undocumented rows) — compare against booleans, not
    # "True"/"False" strings.
    joined["pmr_documented"] = joined["entree_pmr"].isin([True, False])
    joined["pmr_accessible"] = joined["entree_pmr"] == True  # noqa: E712

    grouped = joined.groupby(config.IRIS_JOIN_COLUMN).agg(
        erp_count=("pmr_documented", "size"),
        pmr_documented_count=("pmr_documented", "sum"),
        pmr_accessible_count=("pmr_accessible", "sum"),
    )
    grouped["pct_pmr_accessible"] = grouped["pmr_accessible_count"] / grouped["pmr_documented_count"]
    grouped = grouped.reset_index()

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(grouped, on=config.IRIS_JOIN_COLUMN, how="left")
    result["erp_count"] = result["erp_count"].fillna(0).astype(int)
    return result.to_crs(config.CRS_LATLON)


def main():
    csv_path = download()
    df = load_mgp_rows(csv_path)
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "accessibility_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
