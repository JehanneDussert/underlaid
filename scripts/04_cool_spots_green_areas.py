"""Download and normalize the "cool green area" thermal indicator.

Phase 5 re-sourcing: the original dataset (opendata.paris.fr,
"ilots-de-fraicheur-espaces-verts-frais", APUR-classified) only ever
existed for the city of Paris — no Petite Couronne equivalent found.
Re-sourced to data.iledefrance.fr's "espaces-verts-et-boises-surfaciques
-ouverts-ou-en-projets-douverture-au-public" (green/wooded open spaces,
region-wide, 14,258 records), filtered to currently-open spaces only
(`statouvlib="Ouvert"` — excludes "planned to open," "restricted
opening," and "closed" spaces, matching the spirit of the original
indicator: places that are actually a cool refuge *now*, not eventually).

Polygon geometries; normalized here as the share of each IRIS's surface
covered by open green/wooded space, same as before.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.geo import area_share_per_iris, load_iris_reference
from utils.io import save_geojson
from utils.opendatasoft import export_dataset

RAW_PATH = config.DATA_RAW / "cool_spots_green_areas" / "cool_spots_green_areas_raw.geojson"


def download() -> Path:
    return export_dataset(
        base_url=config.IDF_OPENDATASOFT_BASE,
        dataset_id=config.COOL_GREEN_SPACE_DATASET_ID,
        dest_path=RAW_PATH,
        fmt="geojson",
        where='statouvlib="Ouvert"',
    )


def normalize(raw_path: Path) -> gpd.GeoDataFrame:
    polygons = gpd.read_file(raw_path)
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)

    shares = area_share_per_iris(polygons, iris, config.IRIS_JOIN_COLUMN, out_col="pct_cool_green_area")
    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(shares, on=config.IRIS_JOIN_COLUMN, how="left")
    result["pct_cool_green_area"] = result["pct_cool_green_area"].fillna(0)

    return result.to_crs(config.CRS_LATLON)


def main():
    raw_path = download()
    result = normalize(raw_path)
    save_geojson(result, config.DATA_PROCESSED / "cool_spots_green_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
