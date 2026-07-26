"""Download and normalize the share of poorly-insulated housing (DPE F/G) per IRIS.

Source: data.ademe.fr, dataset "dpe03existant" (DPE Observatory's energy
performance certificates for existing residential buildings), exposed via
the "api-dpe-logements" service on data.gouv.fr. Filtered to the 4 MGP
departments, geolocated per certificate, joined to IRIS, and aggregated
into a F/G ("passoire thermique") share per zone.

Schema note: data.ademe.fr runs on the "data-fair" platform, not
Opendatasoft, so it has its own query API (/data-fair/api/v1/datasets/
{id}/lines, Lucene-style `qs` filter, cursor-based pagination via the
`next` link) rather than the Explore API v2.1 used by the other portals
in this project. Coordinates come as coordonnee_cartographique_x_ban/
y_ban in Lambert-93 (EPSG:2154) — the same CRS used internally for
spatial joins, so no reprojection is needed before joining to IRIS.

Intended use (step 2): becomes its own "housing vulnerability" sub-score
— indoor thermal exposure, complementary to the outdoor heat sub-score
(heat islands / cool spots).

NOTE: Paris has ~800k+ certificates since July 2021; pagination fetches
~10k rows per request, so this script takes a while to run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
import requests

import config
from utils.download import DEFAULT_TIMEOUT
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson

LINES_URL = f"{config.ADEME_OPENDATASOFT_BASE}/data-fair/api/v1/datasets/{config.ENERGY_PERFORMANCE_DATASET_ID}/lines"
PAGE_SIZE = 10_000
SELECT_FIELDS = "etiquette_dpe,coordonnee_cartographique_x_ban,coordonnee_cartographique_y_ban,code_insee_ban"


def fetch_mgp_records() -> pd.DataFrame:
    dept_query = " OR ".join(f"code_insee_ban:{d}*" for d in config.MGP_DEP_CODES)
    params = {
        "qs": dept_query,
        "select": SELECT_FIELDS,
        "size": PAGE_SIZE,
    }
    url = LINES_URL
    rows = []
    while url:
        response = requests.get(url, params=params if url == LINES_URL else None, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload.get("results", []))
        url = payload.get("next")
        print(f"  fetched {len(rows)} DPE records so far...")
    return pd.DataFrame(rows)


def normalize(df: pd.DataFrame) -> gpd.GeoDataFrame:
    df = df.dropna(subset=["coordonnee_cartographique_x_ban", "coordonnee_cartographique_y_ban"])
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["coordonnee_cartographique_x_ban"], df["coordonnee_cartographique_y_ban"]),
        crs=config.CRS_PROJECTED,
    )

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    joined = join_points_to_iris(points, iris, config.IRIS_JOIN_COLUMN)
    joined = joined.dropna(subset=[config.IRIS_JOIN_COLUMN])

    joined["is_poor_class"] = joined["etiquette_dpe"].isin(config.ENERGY_PERFORMANCE_POOR_CLASSES)
    grouped = joined.groupby(config.IRIS_JOIN_COLUMN).agg(
        dpe_sample_size=("is_poor_class", "size"),
        pct_dpe_fg=("is_poor_class", "mean"),
    ).reset_index()

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(grouped, on=config.IRIS_JOIN_COLUMN, how="left")
    return result.to_crs(config.CRS_LATLON)


def main():
    df = fetch_mgp_records()
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "energy_performance_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
