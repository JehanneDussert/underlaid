"""Download and normalize Priority Neighborhood (QPV) boundaries for the
Metropole du Grand Paris (Petite Couronne).

Source: data.iledefrance.fr, dataset "qp-politiquedelaville-shp"
(Opendatasoft Explore API v2.1), published by Agence nationale de la
cohesion des territoires. 162 QPV zones across the 4 MGP departments
(75: 21, 92: 19, 93: 75, 94: 47 — confirmed via direct query).

This is a VALIDATION layer only — used to visually check whether the
cumulative exposure score rediscovers neighborhoods already flagged as
priority by the state, never as an input to the score itself. Not
joined to code_iris (QPV boundaries don't align with IRIS boundaries;
comparison happens by overlaying both layers on the map).

Note: the dataset's own `insee_com` field is an array and uses Paris's
legacy single-commune code (["75056"]) for Paris rows, inconsistent with
the per-arrondissement codes used elsewhere in this project. Filtering
by `insee_dep` (department code) instead sidesteps that entirely and
scales cleanly to all 4 departments — no need to enumerate ~131 commune
names.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.io import save_geojson
from utils.opendatasoft import export_dataset

RAW_PATH = config.DATA_RAW / "qpv_boundaries" / "qpv_mgp_raw.geojson"


def download() -> Path:
    dep_list = ",".join(f'"{d}"' for d in config.MGP_DEP_CODES)
    return export_dataset(
        base_url=config.QPV_OPENDATASOFT_BASE,
        dataset_id=config.QPV_DATASET_ID,
        dest_path=RAW_PATH,
        fmt="geojson",
        where=f"insee_dep in ({dep_list})",
    )


def normalize(raw_path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(raw_path)
    gdf = gdf[["code_qp", "lib_qp", "geometry"]]
    return gdf.to_crs(config.CRS_LATLON)


def main():
    raw_path = download()
    result = normalize(raw_path)
    save_geojson(result, config.DATA_PROCESSED / "qpv_boundaries_mgp.geojson", required_cols=["code_qp", "geometry"])


if __name__ == "__main__":
    main()
