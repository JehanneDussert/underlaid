"""Download and normalize the national urban heat island (ICU) indicators.

Source: data.gouv.fr, dataset "Cartographie nationale des indicateurs lies
a l'ilot de chaleur urbain" (CSTB / Sat4BDNB-IMPROVE project), resource
indicateurs-icu.zip. Confirmed by inspection: the layer has no commune
name/code field, only `code_giris` (a custom "grouped IRIS" code, 7
digits, coarser than the standard 9-digit IRIS — small-population IRIS
appear to be merged), so rows are matched by spatial intersection with
the IRIS reference's bounding box rather than by attribute — this scales
to any extent automatically, Petite Couronne included, since it derives
its area purely from whatever the IRIS reference covers.

Because `code_giris` doesn't line up with our IRIS reference's
`code_iris`, values are area-weighted onto IRIS zones via spatial overlay
rather than an attribute join.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.download import download_file, extract_zip, find_datagouv_resource, find_extracted_file
from utils.geo import areal_weighted_aggregate, check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

RAW_ZIP = config.DATA_RAW / "icu_sat4bdnb" / "indicateurs-icu.zip"
EXTRACT_DIR = config.DATA_RAW / "icu_sat4bdnb" / "extracted"

VALUE_FIELD_PATTERNS = ("uhi", "hvi")


def download() -> Path:
    url = find_datagouv_resource(config.ICU_SAT4BDNB_DATASET_SLUG, config.ICU_SAT4BDNB_RESOURCE_TITLE)
    zip_path = download_file(url, RAW_ZIP)
    extract_zip(zip_path, EXTRACT_DIR)
    return EXTRACT_DIR


def find_layer(extract_dir: Path) -> gpd.GeoDataFrame:
    # The zip ships one GeoPackage (plus a CSV, PDF and QGIS project files).
    layer = find_extracted_file(extract_dir, r".+\.(gpkg|shp|geojson)", "Sat4BDNB heat-island layer")
    return gpd.read_file(layer)


def filter_to_mgp(gdf: gpd.GeoDataFrame, iris: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.to_crs(iris.crs)
    mgp_gdf = gpd.clip(gdf, iris.total_bounds)
    if mgp_gdf.empty:
        raise RuntimeError("No rows intersect the MGP IRIS reference bounding box.")
    print(f"{len(mgp_gdf)} zones found within MGP bounds "
          f"(covering {mgp_gdf.geometry.area.sum() / 1e6:.1f} km2).")
    return mgp_gdf


def normalize(mgp_gdf: gpd.GeoDataFrame, iris: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    value_cols = [c for c in mgp_gdf.columns if any(p in c.lower() for p in VALUE_FIELD_PATTERNS)]
    if not value_cols:
        raise RuntimeError(f"No UHI/HVI-like columns found among {list(mgp_gdf.columns)}.")

    aggregated = areal_weighted_aggregate(mgp_gdf, iris, value_cols, config.IRIS_JOIN_COLUMN)
    check_unmatched_codes(aggregated, iris, config.IRIS_JOIN_COLUMN)

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(aggregated, on=config.IRIS_JOIN_COLUMN, how="left")
    return result.to_crs(config.CRS_LATLON)


def main():
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    extract_dir = download()
    gdf = find_layer(extract_dir)
    mgp_gdf = filter_to_mgp(gdf, iris)
    result = normalize(mgp_gdf, iris)
    save_geojson(result, config.DATA_PROCESSED / "icu_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
