"""Download and normalize the Airparif/Bruitparif air-noise co-exposure map.

Source: bruitparif.fr open data page, "Couches SIG air-bruit 2024_9_classes"
zip (direct download, no API). Covers all of Ile-de-France at commune/EPCI
scale; clipped here to whatever the IRIS reference covers (MGP) and
area-weighted onto IRIS zones — scales automatically to any extent.

Attribution required by the data provider: "Source des donnees:
Cartographie air-bruit etablie par Airparif et Bruitparif". No formal
open license was found on the source page — confirm reuse terms before
publishing derived data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.download import download_file, extract_zip, find_extracted_file
from utils.geo import areal_weighted_aggregate, check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

RAW_ZIP = config.DATA_RAW / "air_noise" / "air_noise_2024_9_classes.zip"
EXTRACT_DIR = config.DATA_RAW / "air_noise" / "extracted"

# Confirmed by inspecting the extracted shapefile (AirBruit_2024.shp): the
# co-exposure class field is literally named "9" (one 2-digit code per
# 3x3 air-tier x noise-tier combination, e.g. 12, 22, 33).
CLASS_FIELD_CANDIDATES = ("9", "classe", "classe_9", "coexpo", "classe_coexposition")


def download() -> Path:
    zip_path = download_file(config.AIR_NOISE_ZIP_URL, RAW_ZIP, encode_path=True)
    extract_zip(zip_path, EXTRACT_DIR)
    return EXTRACT_DIR


def find_layer(extract_dir: Path) -> gpd.GeoDataFrame:
    # The zip ships one shapefile (AirBruit_<year>.shp and its sidecars).
    layer = find_extracted_file(extract_dir, r".+\.(gpkg|shp|geojson)", "Airparif/Bruitparif air-noise layer")
    return gpd.read_file(layer)


def normalize(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    class_col = next((c for c in CLASS_FIELD_CANDIDATES if c in gdf.columns), None)
    if class_col is None:
        raise RuntimeError(
            f"Could not find a co-exposure class column among {list(gdf.columns)}; "
            "update CLASS_FIELD_CANDIDATES in this script."
        )

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    gdf = gdf.to_crs(iris.crs)
    clipped = gpd.clip(gdf, iris.total_bounds)

    aggregated = areal_weighted_aggregate(clipped, iris, [class_col], config.IRIS_JOIN_COLUMN)
    aggregated = aggregated.rename(columns={class_col: "air_noise_coexposure_class"})
    check_unmatched_codes(aggregated, iris, config.IRIS_JOIN_COLUMN)

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(aggregated, on=config.IRIS_JOIN_COLUMN, how="left")
    return result.to_crs(config.CRS_LATLON)


def main():
    extract_dir = download()
    gdf = find_layer(extract_dir)
    result = normalize(gdf)
    save_geojson(result, config.DATA_PROCESSED / "air_noise_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
