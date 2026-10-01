"""Download and normalize the "cool facilities" thermal indicator.

Phase 5 re-sourcing: the original indicator (opendata.paris.fr,
"ilots-de-fraicheur-equipements-activites") only ever existed for the
city of Paris — no Petite Couronne equivalent. Re-sourced to the BPE
(Base Permanente des Equipements, already used in script 06), which
turns out to carry exactly the same categories as the original Paris
dataset's namesake examples (pools, libraries, museums) as its own
equipment-type codes, confirmed against INSEE's official nomenclature:

- F101: BASSIN DE NATATION (swimming pool)
- F305: MUSEE (museum)
- F307: BIBLIOTHEQUE (library)

This is a strictly better fit than introducing a new regional dataset:
BPE is already integrated, national (not just IDF), and these are
genuine facility inventories rather than funding/grant records (a
region-wide "pools" dataset was considered and rejected for exactly
that reason — it turned out to be a list of subsidized pool projects,
not an inventory of actual pools).

Reuses script 06's already-downloaded/extracted BPE CSV rather than
re-fetching it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.download import download_file, extract_zip, find_extracted_file
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson

COMMUNE_FIELD = "DEPCOM"
DOMAIN_FIELD = "TYPEQU"
LON_FIELD_CANDIDATES = ("LONGITUDE", "longitude", "lon")
LAT_FIELD_CANDIDATES = ("LATITUDE", "latitude", "lat")
COOL_FACILITY_TYPES = ("F101", "F305", "F307")  # pools, museums, libraries

CHUNK_SIZE = 200_000

# 11_compute_vulnerability_score.py recomputes a 400m-buffer count directly
# from this raw-points cache (more precise near IRIS borders than the
# per-IRIS count alone) — kept at the same path/filename as before the
# Phase 5 re-sourcing so that script doesn't need to change.
RAW_POINTS_CACHE = config.DATA_RAW / "cool_spots_facilities" / "cool_spots_facilities_raw.geojson"


def download() -> Path:
    zip_path = download_file(config.BPE_ZIP_URL, config.BPE_RAW_ZIP)
    extract_dir = config.DATA_RAW / "bpe" / "extracted"
    extract_zip(zip_path, extract_dir)
    return find_extracted_file(extract_dir, r"BPE\d{2}\.csv", "BPE equipment file")


def load_cool_facility_rows(csv_path: Path) -> pd.DataFrame:
    chunks = []
    for chunk in pd.read_csv(csv_path, sep=";", low_memory=False, chunksize=CHUNK_SIZE):
        mask = (
            chunk[COMMUNE_FIELD].astype(str).str[:2].isin(config.MGP_DEP_CODES)
            & chunk[DOMAIN_FIELD].isin(COOL_FACILITY_TYPES)
        )
        matched = chunk[mask]
        if not matched.empty:
            chunks.append(matched)
    if not chunks:
        raise RuntimeError(f"No rows matched cool-facility types {COOL_FACILITY_TYPES} in {csv_path}.")
    return pd.concat(chunks, ignore_index=True)


def to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    lon_col = next((c for c in LON_FIELD_CANDIDATES if c in df.columns), None)
    lat_col = next((c for c in LAT_FIELD_CANDIDATES if c in df.columns), None)
    if not lon_col or not lat_col:
        raise RuntimeError(f"Could not find lat/lon columns among {list(df.columns)}.")
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs=config.CRS_LATLON)


def normalize(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    joined = join_points_to_iris(points.to_crs(iris.crs), iris, config.IRIS_JOIN_COLUMN)

    counts = joined.groupby(config.IRIS_JOIN_COLUMN).size().rename("cool_spots_facilities_count")
    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(counts, on=config.IRIS_JOIN_COLUMN, how="left")
    result["cool_spots_facilities_count"] = result["cool_spots_facilities_count"].fillna(0).astype(int)

    by_type = joined.groupby([config.IRIS_JOIN_COLUMN, DOMAIN_FIELD]).size().unstack(fill_value=0)
    by_type.columns = [f"count_{c.lower()}" for c in by_type.columns]
    result = result.merge(by_type, on=config.IRIS_JOIN_COLUMN, how="left")

    return result.to_crs(config.CRS_LATLON)


def main():
    csv_path = download()
    df = load_cool_facility_rows(csv_path)
    points = to_geodataframe(df)

    RAW_POINTS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    points[["geometry"]].to_file(RAW_POINTS_CACHE, driver="GeoJSON")

    result = normalize(points)
    save_geojson(result, config.DATA_PROCESSED / "cool_spots_facilities_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
