"""Common attachment points for the travel-time runs (decided 2026-10-04).

Diagnostic (CLAUDE.md, 4 October 2026): R5 attaches every origin and
destination to the nearest element of each street network separately. In
the standard network that element is sometimes a stairway or a path that
forces a detour, so some step-free durations came out shorter than the
standard ones, and some standard durations were overestimated.

Correction: every point is moved beforehand onto a way of the network
without stairs, which exists in the standard network too, so R5 attaches
it to the same way in all four profiles (the point lies on it):
  1. the nearest street (primary, secondary, tertiary and their links,
     residential, unclassified, living_street, pedestrian) if within 60 m;
  2. else the nearest walkable way of any kind (footway, path, service,
     track, cycleway…) if within 150 m (e.g. points on a park outline);
  3. else the point is kept as it was (e.g. stations outside Île-de-France,
     beyond the OSM extract), and the tier is recorded.
Not foot=no / use_sidepath, not access=no / private.

Inputs: inhabited MGP cells (script 34 origins) and the three destination
files (scripts 33, 37, 41). Output: data/processed/access/snapped_points.csv
(set, id, lon, lat, moved_m, tier), read by script 34 when ROUTES_VERSION=2.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import osmium
import shapely
import pandas as pd
from shapely import STRtree, line_locate_point, line_interpolate_point
from shapely.geometry import LineString

import config

ACCESS = config.DATA_PROCESSED / "access"
PBF = config.DATA_INTERIM / "access" / "idf_no_stairs.osm.pbf"
OUT = ACCESS / "snapped_points.csv"
STREETS = {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link",
           "residential", "unclassified", "living_street", "pedestrian"}
NOT_WALKABLE = {"motorway", "motorway_link", "trunk", "trunk_link", "steps", "construction", "proposed",
                "raceway", "bus_guideway", "escape", "abandoned", "platform", "elevator", "corridor"}
STREET_MAX_M = 60
ANY_MAX_M = 150
NO_FOOT = {"no", "use_sidepath"}
NO_ACCESS = {"no", "private"}
DEST_FILES = {
    "key": "route_destinations_idf.geojson",
    "neighbourhood": "neighbourhood_destinations_idf.geojson",
    "paris": "paris_amenities_idf.geojson",
}


class Streets(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.streets = []
        self.walkable = []

    def way(self, w):
        t = w.tags
        hw = t.get("highway")
        if hw is None or hw in NOT_WALKABLE or t.get("foot") in NO_FOOT or t.get("access") in NO_ACCESS:
            return
        if t.get("area") == "yes":
            return
        try:
            coords = [(n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if len(coords) >= 2:
            line = LineString(coords)
            self.walkable.append(line)
            if hw in STREETS:
                self.streets.append(line)


def nearest_on(pts: np.ndarray, lines: np.ndarray, tree: STRtree):
    nearest = lines[tree.nearest(pts)]
    on = line_interpolate_point(nearest, line_locate_point(nearest, pts))
    return on, shapely.distance(pts, on)


def snap(points: gpd.GeoSeries, nets) -> pd.DataFrame:
    pts = points.to_crs(config.CRS_PROJECTED).to_numpy()
    (s_lines, s_tree), (w_lines, w_tree) = nets
    on_s, d_s = nearest_on(pts, s_lines, s_tree)
    on_w, d_w = nearest_on(pts, w_lines, w_tree)
    tier = np.where(d_s <= STREET_MAX_M, "street", np.where(d_w <= ANY_MAX_M, "walkable", "kept"))
    on = np.where(tier == "street", on_s, np.where(tier == "walkable", on_w, pts))
    moved = np.where(tier == "street", d_s, np.where(tier == "walkable", d_w, 0.0))
    g = gpd.GeoSeries(on, crs=config.CRS_PROJECTED).to_crs(config.CRS_LATLON)
    return pd.DataFrame({"lon": g.x.to_numpy(), "lat": g.y.to_numpy(), "moved_m": moved, "tier": tier})


def origin_cells() -> gpd.GeoDataFrame:
    """Same rule as script 34: inhabited cells whose centre lies in an MGP IRIS."""
    cells = gpd.read_file(ACCESS / "demand_grid_idf.geojson")[["cell_id", "pop", "geometry"]]
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(cells.crs)
    inside = gpd.sjoin(cells, iris, predicate="within", how="inner")
    inside = inside[inside["pop"] > 0].drop_duplicates("cell_id")
    return inside[["cell_id", "geometry"]].rename(columns={"cell_id": "id"}).to_crs(config.CRS_LATLON)


def main():
    h = Streets()
    h.apply_file(str(PBF), locations=True, idx="flex_mem")
    nets = []
    for lines in (h.streets, h.walkable):
        arr = gpd.GeoSeries(lines, crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED).to_numpy()
        nets.append((arr, STRtree(arr)))
    print(f"{len(h.streets):,} streets, {len(h.walkable):,} walkable ways", flush=True)

    parts = []
    o = origin_cells()
    parts.append(snap(o.geometry, nets).assign(set="origin", id=o["id"].astype(str).to_numpy()))
    for name, f in DEST_FILES.items():
        d = gpd.read_file(ACCESS / f)
        parts.append(snap(d.geometry, nets).assign(set=name, id=d["dest_id"].astype(str).to_numpy()))
    out = pd.concat(parts, ignore_index=True)[["set", "id", "lon", "lat", "moved_m", "tier"]]
    out.to_csv(OUT, index=False)
    print(pd.crosstab(out["set"], out["tier"]).to_string())
    print(out[out.tier != "kept"].groupby("set")["moved_m"].describe(percentiles=[0.5, 0.9, 0.99]).round(1).to_string())


if __name__ == "__main__":
    main()
