"""Download and normalize pedestrian path density per IRIS (OpenStreetMap).

Source: OpenStreetMap via the Overpass API, `highway=footway` ways within
the IRIS reference's bounding box (Paris, then MGP as of Phase 5 — this
scales automatically since the query area is derived from whatever the
IRIS reference covers, not a hardcoded box). The "official" candidate
source, transport.data.gouv.fr's "Cheminements pietons dans Paris
d'apres OpenStreetMap" dataset, only ships NeTEx (an XML
transit-accessibility exchange format, not built for simple footway
geometry) — queries the same underlying OSM data directly via Overpass
instead, in plain GeoJSON-friendly form.

Public Overpass instances reject requests without a real User-Agent
(via a 406 from the reverse proxy, not the Overpass app itself).

Indicator: total footway length per IRIS, normalized by IRIS area
(m of footway per km^2) — a walkability density proxy. Feeds the
"access to services" sub-score.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString

import config
from utils.io import save_geojson

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
RAW_PATH = config.DATA_RAW / "pedestrian_paths" / "footways_mgp_raw.json"
USER_AGENT = "underlaid-research/1.0 (Paris/Grand Paris urban vulnerability mapping project)"


def download() -> Path:
    if RAW_PATH.exists():
        return RAW_PATH

    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)
    min_lon, min_lat, max_lon, max_lat = iris.total_bounds
    bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"

    query = f'[out:json][timeout:120];way["highway"="footway"]({bbox});out geom;'
    response = requests.get(
        OVERPASS_URL, params={"data": query}, timeout=180, headers={"User-Agent": USER_AGENT}
    )
    response.raise_for_status()

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(response.text, encoding="utf-8")
    return RAW_PATH


def load_footways(raw_path: Path) -> gpd.GeoDataFrame:
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    lines = []
    for element in data.get("elements", []):
        geometry = element.get("geometry")
        if not geometry or len(geometry) < 2:
            continue
        lines.append(LineString([(pt["lon"], pt["lat"]) for pt in geometry]))

    if not lines:
        raise RuntimeError(f"No footway geometries found in {raw_path}.")
    return gpd.GeoDataFrame({"geometry": lines}, crs=config.CRS_LATLON)


def normalize(footways: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(config.CRS_PROJECTED)
    footways = footways.to_crs(config.CRS_PROJECTED)

    overlay = gpd.overlay(footways, iris, how="intersection")
    overlay["length_m"] = overlay.geometry.length
    length_per_iris = overlay.groupby("code_iris")["length_m"].sum().rename("footway_length_m")

    iris["_area_km2"] = iris.geometry.area / 1e6
    result = iris.merge(length_per_iris, on="code_iris", how="left")
    result["footway_length_m"] = result["footway_length_m"].fillna(0)
    result["footway_density_m_per_km2"] = result["footway_length_m"] / result["_area_km2"]
    result = result.drop(columns=["_area_km2"])

    return result.to_crs(config.CRS_LATLON)


def main():
    raw_path = download()
    footways = load_footways(raw_path)
    result = normalize(footways)
    save_geojson(result, config.DATA_PROCESSED / "pedestrian_paths_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
