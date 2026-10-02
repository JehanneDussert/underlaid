"""Audit: are OpenStreetMap steps (highway=steps) mapped evenly across the MGP?

One-off analysis, not part of the pipeline. The accessible-walking
scenario of the access rebuild drops highway=steps from the pedestrian
network; that only treats every department alike if steps are mapped
about as completely everywhere. OSM has no ground truth of its own, so
this compares it with IGN BD TOPO, an official source: road segments of
nature "Escalier" (Licence Ouverte 2.0, fetched through the Géoplateforme
WFS).

For each department: staircase length in each source, and the share of
BD TOPO staircase length that has an OSM highway=steps way within
MATCH_BUFFER_M ("BD TOPO staircases found in OSM"), plus the reverse.

Usage: python scripts/analysis/osm_steps_completeness.py
(needs the Geofabrik extract downloaded by osm_sidewalk_completeness.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import pandas as pd
import pyogrio
import requests

import config
from osm_sidewalk_completeness import PBF_PATH

WFS_URL = "https://data.geopf.fr/wfs/ows"
PAGE = 5000
MATCH_BUFFER_M = 15
OUT_DIR = config.DATA_INTERIM / "analysis"


def fetch_bdtopo_steps(bbox) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = bbox
    frames, start = [], 0
    while True:
        params = {
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeNames": "BDTOPO_V3:troncon_de_route", "outputFormat": "application/json",
            "srsName": "EPSG:4326", "count": PAGE, "startIndex": start,
            "CQL_FILTER": f"nature='Escalier' AND BBOX(geometrie,{minx},{miny},{maxx},{maxy},'EPSG:4326')",
        }
        r = requests.get(WFS_URL, params=params, timeout=120)
        r.raise_for_status()
        feats = r.json()["features"]
        if not feats:
            break
        frames.append(gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326"))
        if len(feats) < PAGE:
            break
        start += PAGE
    return pd.concat(frames, ignore_index=True)


def main():
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(config.CRS_PROJECTED)
    iris["dep"] = iris.code_iris.str[:2]
    deps = iris.dissolve(by="dep").reset_index()[["dep", "geometry"]]
    bbox = tuple(iris.to_crs(config.CRS_LATLON).total_bounds)

    ign = fetch_bdtopo_steps(bbox).to_crs(config.CRS_PROJECTED)
    osm = pyogrio.read_dataframe(PBF_PATH, layer="lines", where="highway = 'steps'", bbox=bbox).to_crs(config.CRS_PROJECTED)

    ign = gpd.overlay(ign[["geometry"]], deps, how="intersection", keep_geom_type=True)
    osm = gpd.overlay(osm[["geometry"]], deps, how="intersection", keep_geom_type=True)
    rows = []
    for dep, d in deps.groupby("dep"):
        a, b = ign[ign.dep == dep], osm[osm.dep == dep]
        a_in_b = a.intersection(b.buffer(MATCH_BUFFER_M).union_all()).length.sum()
        b_in_a = b.intersection(a.buffer(MATCH_BUFFER_M).union_all()).length.sum()
        rows.append({
            "dep": dep,
            "bdtopo_steps_km": round(a.length.sum() / 1000, 1),
            "osm_steps_km": round(b.length.sum() / 1000, 1),
            "bdtopo_found_in_osm_%": round(100 * a_in_b / a.length.sum(), 1),
            "osm_found_in_bdtopo_%": round(100 * b_in_a / b.length.sum(), 1),
        })
    out = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_DIR / "osm_steps_vs_bdtopo_dep.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
