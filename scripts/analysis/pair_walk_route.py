"""Walking route between the inhabited centres of two neighbourhoods
(launch post, pair chosen on 2026-10-07: Clichy, Maison du Peuple /
Bateliers). Same rules as neighbouring_pairs.py: population-weighted centre
of the inhabited 200 m cells, snapped as in script 42; R5 on the full
street network at 4.5 km/h. Writes the route (GeoJSON), its length, time
and the streets it follows to data/interim/analysis/neighbouring_pairs/.
"""
import datetime as dt
import importlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "10G")]
import config  # noqa: E402

import geopandas as gpd  # noqa: E402
import osmium  # noqa: E402
import pandas as pd  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

A, B = "920240402", "920240303"
OUT = config.DATA_INTERIM / "analysis" / "neighbouring_pairs"


class Names(osmium.SimpleHandler):
    def __init__(self, box):
        super().__init__()
        self.box, self.rows = box, []

    def way(self, w):
        if "highway" not in w.tags:
            return
        try:
            c = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        w0, s0, e0, n0 = self.box
        if len(c) >= 2 and any(w0 <= x <= e0 and s0 <= y <= n0 for x, y in c):
            self.rows.append({"name": w.tags.get("name", ""), "highway": w.tags["highway"], "geometry": LineString(c)})


def main():
    import r5py

    snap42 = importlib.import_module("42_snap_points")
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris")
    cells = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["pop", "geometry"]].to_crs(config.CRS_PROJECTED)
    cells = cells[cells["pop"] > 0].copy()
    cells["geometry"] = cells.geometry.centroid
    centres = {}
    for code in (A, B):
        c = cells[cells.within(iris.at[code, "geometry"])]
        w = c["pop"].to_numpy()
        centres[code] = Point((c.geometry.x * w).sum() / w.sum(), (c.geometry.y * w).sum() / w.sum())
    g = gpd.GeoSeries([centres[A], centres[B]], crs=config.CRS_PROJECTED).to_crs(config.CRS_LATLON)
    sh = snap42.Streets()
    sh.apply_file(str(snap42.PBF), locations=True, idx="flex_mem")
    nets = []
    for lines in (sh.streets, sh.walkable):
        arr = gpd.GeoSeries(lines, crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED).to_numpy()
        nets.append((arr, snap42.STRtree(arr)))
    sn = snap42.snap(g, nets)
    pts = gpd.GeoDataFrame({"id": [A, B]}, geometry=gpd.points_from_xy(sn.lon, sn.lat), crs=config.CRS_LATLON)
    network = r5py.TransportNetwork(str(config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), [str(config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip")])
    it = r5py.DetailedItineraries(network, origins=pts.iloc[[0]], destinations=pts.iloc[[1]], departure=dt.datetime(2026, 10, 13, 10, 0),
                                  transport_modes=[r5py.TransportMode.WALK], speed_walking=4.5, snap_to_network=False)
    it = gpd.GeoDataFrame(it, geometry="geometry", crs=config.CRS_LATLON)
    route = it.iloc[0]
    line = route.geometry
    length = gpd.GeoSeries([line], crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED).length.iloc[0]
    minutes = route["travel_time"].total_seconds() / 60 if hasattr(route["travel_time"], "total_seconds") else float(route["travel_time"])
    b = line.bounds
    h = Names((b[0] - 0.001, b[1] - 0.001, b[2] + 0.001, b[3] + 0.001))
    h.apply_file(str(config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), locations=True, idx="flex_mem")
    ways = gpd.GeoDataFrame(h.rows, geometry="geometry", crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED)
    lp = gpd.GeoSeries([line], crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED).iloc[0]
    streets = []
    for d in range(0, int(lp.length) + 1, 10):
        p = lp.interpolate(d)
        near = ways[ways.distance(p) < 8]
        if len(near):
            name = near.assign(dd=near.distance(p)).sort_values("dd").iloc[0]["name"] or "(sans nom)"
            if not streets or streets[-1] != name:
                streets.append(name)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "clichy_walk_route.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"from": A, "to": B, "minutes": round(minutes, 1), "length_m": round(length)}, "geometry": line.__geo_interface__},
        {"type": "Feature", "properties": {"role": "centre", "code": A}, "geometry": pts.geometry.iloc[0].__geo_interface__},
        {"type": "Feature", "properties": {"role": "centre", "code": B}, "geometry": pts.geometry.iloc[1].__geo_interface__}]}), encoding="utf-8")
    straight = centres[A].distance(centres[B])
    text = (f"Clichy, Maison du Peuple ({A}) -> Bateliers ({B}), walk at 4.5 km/h between the inhabited centres\n"
            f"time {minutes:.1f} min; length {length:.0f} m; straight line {straight:.0f} m\nstreets: " + " -> ".join(streets) + "\n")
    (OUT / "clichy_walk_route.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
