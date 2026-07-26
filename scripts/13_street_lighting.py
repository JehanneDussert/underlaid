"""Download and normalize street lighting density per IRIS.

Source: opendata.paris.fr, dataset "eclairage-public" (Opendatasoft
Explore API v2.1) — genuinely Paris-only, no Petite Couronne equivalent
found (Phase 5). Each row is one lamp; counted per IRIS as a density
proxy.

This feeds a "perceived safety" signal that is deliberately
optional/context-only and NOT part of the cumulative sub-score model —
this script only collects and normalizes the data now, it is not wired
into 11_compute_vulnerability_score.py.

Only Paris IRIS get a real 0 for "no lamps counted here"; IRIS outside
Paris are left null rather than 0 — this source simply doesn't cover
them, and a 0 would misrepresent "verified no lighting" as opposed to
"not covered by this source." This matters downstream: script 19
dissolves this to commune grain, and a silent 0 for every Petite
Couronne commune would look like real (and alarming) data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson
from utils.opendatasoft import export_dataset

RAW_PATH = config.DATA_RAW / "street_lighting" / "street_lighting_raw.geojson"


def download() -> Path:
    return export_dataset(
        base_url=config.PARIS_OPENDATASOFT_BASE,
        dataset_id=config.STREET_LIGHTING_DATASET_ID,
        dest_path=RAW_PATH,
        fmt="geojson",
    )


def normalize(raw_path: Path) -> gpd.GeoDataFrame:
    points = gpd.read_file(raw_path)
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)

    joined = join_points_to_iris(points.to_crs(iris.crs), iris, config.IRIS_JOIN_COLUMN)
    counts = joined.groupby(config.IRIS_JOIN_COLUMN).size().rename("street_lighting_count")

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(counts, on=config.IRIS_JOIN_COLUMN, how="left")
    is_paris = result[config.IRIS_JOIN_COLUMN].str[:2] == config.PARIS_DEP_CODE
    result.loc[is_paris, "street_lighting_count"] = result.loc[is_paris, "street_lighting_count"].fillna(0)
    return result.to_crs(config.CRS_LATLON)


def main():
    raw_path = download()
    result = normalize(raw_path)
    save_geojson(result, config.DATA_PROCESSED / "street_lighting_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
