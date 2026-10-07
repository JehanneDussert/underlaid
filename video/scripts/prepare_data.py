"""Data for the launch video (real data only). A pair of neighbourhoods
(CODES=a,b) and the focus neighbourhood of act 2 (FOCUS): outlines of the
published map file, exposure ranks and station times of the published
neighbourhood files, stop names (scripts/analysis/pair_stations.py) and
the two walking routes of act 2 (video/scripts/pair_routes.py).
Coordinates in Lambert-93 metres, shifted to the metropolis' bounding box
and flipped (y down) for SVG. Writes video/src/data/pair.json.
"""
import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

A, B = os.environ["CODES"].split(",")
FOCUS = os.environ["FOCUS"]
OUT = ROOT / "video" / "src" / "data" / "pair.json"
AN = config.DATA_INTERIM / "analysis"


def path(geom, tf, nd=0):
    out = []
    for p in getattr(geom, "geoms", [geom]):
        out.append("M" + "L".join(f"{x:.{nd}f},{y:.{nd}f}" for x, y in (tf(*c) for c in p.exterior.coords)) + "Z")
    return "".join(out)


def line(coords, tf):
    return [[round(v, 1) for v in tf(*c)] for c in coords]


def main():
    iris = gpd.read_file(ROOT / "frontend" / "public" / "data" / "map_iris.geojson").to_crs("EPSG:2154")
    code_col = "code" if "code" in iris.columns else "code_iris"
    x0, y0, x1, y1 = iris.total_bounds
    tf = lambda x, y: (x - x0, y1 - y)
    recs = {}
    for f in (ROOT / "frontend" / "public" / "data" / "quartiers").glob("[0-9]*.json"):
        for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
            if r["code"] in (A, B):
                recs[r["code"]] = r
    simple = iris.copy()
    simple["geometry"] = simple.geometry.simplify(12)
    communes = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs("EPSG:2154").dissolve("nom_com")
    communes["geometry"] = communes.geometry.simplify(12)
    paris = communes[communes.index.str.startswith("Paris")].geometry.union_all()
    stop_names = {}
    for prof in ("free", "wheelchair"):
        s = pd.read_csv(AN / f"pair_stations_{prof}.csv", dtype={"code_iris": str})
        for code, g in s.groupby("code_iris"):
            w = g.groupby(["stop", "wheelchair_boarding"])["pop"].sum().sort_values(ascending=False)
            stop_names[(code, prof)] = {"name": w.index[0][0], "wheelchair_boarding": int(w.index[0][1])}
    # Inhabited centre of each neighbourhood (population-weighted cells).
    cells = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["pop", "geometry"]].to_crs("EPSG:2154")
    cells = cells[cells["pop"] > 0].copy()
    cells["geometry"] = cells.geometry.centroid
    hood = {}
    for code in (A, B):
        r = recs[code]
        g = iris[iris[code_col].astype(str) == code].geometry.iloc[0]
        c = cells[cells.within(g)]
        w = c["pop"].to_numpy()
        cx, cy = (c.geometry.x * w).sum() / w.sum(), (c.geometry.y * w).sum() / w.sum()
        hood[code] = {
            "code": code, "name": r["name"], "commune": r["commune"], "population": r["population"],
            "exposures": {k: {"rank": r["exposures"][k]["rank"], "quarter": r["exposures"][k]["quarter"]} for k in ("thermal", "pollution", "housing")},
            "station": {"free": r["station"]["free"], "wheelchair": r["station"]["wheelchair"],
                        "stopFree": stop_names[(code, "free")], "stopWheelchair": stop_names[(code, "wheelchair")]},
            "path": path(g, tf, 1), "centre": [round(v, 1) for v in tf(cx, cy)],
        }
    routes = {}
    for prof in ("free", "wheelchair"):
        f = json.loads((AN / f"video_route_{prof}.geojson").read_text(encoding="utf-8"))
        assert f["properties"]["focus"] == FOCUS, f"route file is for {f['properties']['focus']}"
        xy = gpd.GeoSeries([shape(f["geometry"])], crs="EPSG:4326").to_crs("EPSG:2154").iloc[0]
        routes[prof] = {"points": line(xy.coords, tf), "stop": f["properties"]["stop"],
                        "routeMinutes": f["properties"]["route_minutes"], "publishedMinutes": f["properties"]["published_minutes"]}
    out = {
        "source": "underlaid.fr — published data (second routing run): neighbourhood files and map outlines; stops: IDFM GTFS of 1 October 2026",
        "size": [round(x1 - x0), round(y1 - y0)],
        "iris": "".join(path(g, tf) for g in simple.geometry),
        "communes": "".join(path(g, tf) for g in communes.geometry),
        "paris": path(paris, tf),
        "a": hood[A], "b": hood[B], "focus": FOCUS, "routes": routes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
