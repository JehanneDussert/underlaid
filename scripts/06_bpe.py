"""Normalize the geolocated Base Permanente des Equipements (BPE) for the
Metropole du Grand Paris (Petite Couronne).

Source: INSEE "Equipements geolocalises 2025" file (BPE25.zip), downloaded
from the stable /fr/statistiques/fichier/{page_id}/{filename} pattern
(confirmed working; see BPE_ZIP_URL in config.py). Covers all of France,
so rows are filtered to MGP_DEP_CODES while the CSV is being read in
chunks to avoid loading the whole country into memory.

Filters to the 4 MGP departments and to the health/education/transport
domains (BPE domain codes C/D/E), then counts equipments per IRIS and per
domain.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.download import download_file, extract_zip
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson

# BPE field names as documented by INSEE; adjust if a future edition uses
# different casing/labels.
COMMUNE_FIELD = "DEPCOM"
DOMAIN_FIELD = "TYPEQU"  # equipment type code; first letter = domain
LON_FIELD_CANDIDATES = ("LONGITUDE", "longitude", "lon")
LAT_FIELD_CANDIDATES = ("LATITUDE", "latitude", "lat")

CHUNK_SIZE = 200_000


def download() -> Path:
    zip_path = download_file(config.BPE_ZIP_URL, config.BPE_RAW_ZIP)
    extract_dir = config.DATA_RAW / "bpe" / "extracted"
    extract_zip(zip_path, extract_dir)
    candidates = list(extract_dir.rglob("*.csv"))
    if not candidates:
        raise RuntimeError(f"No CSV found after extracting {zip_path}; inspect its contents manually.")
    return candidates[0]


def load_raw(csv_path: Path) -> pd.DataFrame:
    chunks = []
    for chunk in pd.read_csv(csv_path, sep=";", low_memory=False, chunksize=CHUNK_SIZE):
        mgp_chunk = chunk[chunk[COMMUNE_FIELD].astype(str).str[:2].isin(config.MGP_DEP_CODES)]
        if not mgp_chunk.empty:
            chunks.append(mgp_chunk)
    if not chunks:
        raise RuntimeError(f"No rows matched departments {config.MGP_DEP_CODES} in {csv_path}.")
    return pd.concat(chunks, ignore_index=True)


def filter_domains(df: pd.DataFrame) -> pd.DataFrame:
    domain_mask = df[DOMAIN_FIELD].astype(str).str[0].isin(config.BPE_DOMAINS_OF_INTEREST)
    return df[domain_mask].copy()


def to_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    lon_col = next((c for c in LON_FIELD_CANDIDATES if c in df.columns), None)
    lat_col = next((c for c in LAT_FIELD_CANDIDATES if c in df.columns), None)
    if not lon_col or not lat_col:
        raise RuntimeError(f"Could not find lat/lon columns among {list(df.columns)}.")

    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs=config.CRS_LATLON
    )


def normalize(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    joined = join_points_to_iris(points, iris, config.IRIS_JOIN_COLUMN)
    joined["domain"] = joined[DOMAIN_FIELD].astype(str).str[0]

    by_domain = joined.groupby([config.IRIS_JOIN_COLUMN, "domain"]).size().unstack(fill_value=0)
    by_domain.columns = [f"bpe_count_domain_{c}" for c in by_domain.columns]
    by_domain["bpe_count_total"] = by_domain.sum(axis=1)

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(by_domain, on=config.IRIS_JOIN_COLUMN, how="left")
    for col in by_domain.columns:
        result[col] = result[col].fillna(0).astype(int)

    return result.to_crs(config.CRS_LATLON)


def main():
    csv_path = download()
    df = load_raw(csv_path)
    df = filter_domains(df)
    points = to_geodataframe(df)
    result = normalize(points)
    save_geojson(result, config.DATA_PROCESSED / "bpe_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
