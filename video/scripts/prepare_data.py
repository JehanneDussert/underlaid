"""Data for the launch video "Deux adresses, quelques rues d'écart" (pair
chosen on 2026-10-07: Clichy, Maison du Peuple / Bateliers). Real data
only: neighbourhood outlines (published map file), exposure ranks of the
published neighbourhood files, inhabited centres and the walking time from
scripts/analysis/pair_walk_route.py. Coordinates in Lambert-93 metres,
shifted to the metropolis' bounding box and flipped (y down) for SVG.
Writes video/src/data/clichy.json.
"""
import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

A, B = "920240402", "920240303"
OUT = ROOT / "video" / "src" / "data" / "clichy.json"
ROUTE = Path(sys.argv[1]) if len(sys.argv) > 1 else config.DATA_INTERIM / "analysis" / "neighbouring_pairs" / "clichy_walk_route.geojson"


def path(geom, tf, ndigits=0):
    polys = getattr(geom, "geoms", [geom])
    parts = []
    for p in polys:
        for ring in [p.exterior]:
            pts = [tf(x, y) for x, y in ring.coords]
            parts.append("M" + "L".join(f"{x:.{ndigits}f},{y:.{ndigits}f}" for x, y in pts) + "Z")
    return "".join(parts)


def main():
    iris = gpd.read_file(ROOT / "frontend" / "public" / "data" / "map_iris.geojson").to_crs("EPSG:2154")
    code_col = "code" if "code" in iris.columns else "code_iris"
    x0, y0, x1, y1 = iris.total_bounds
    tf = lambda x, y: (x - x0, y1 - y)
    recs = {}
    for f in (ROOT / "frontend" / "public" / "data" / "quartiers").glob("92024.json"):
        for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
            recs[r["code"]] = r
    simple = iris.copy()
    simple["geometry"] = simple.geometry.simplify(12)
    communes = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs("EPSG:2154").dissolve("nom_com")
    communes["geometry"] = communes.geometry.simplify(12)
    paris = communes[communes.index.str.startswith("Paris")].geometry.union_all()
    clichy = iris[iris[code_col].astype(str).str.startswith("92024")]
    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    centres = {f["properties"]["code"]: f["geometry"]["coordinates"] for f in route["features"] if f["properties"].get("role") == "centre"}
    meta = next(f["properties"] for f in route["features"] if "minutes" in f["properties"])
    cen = gpd.GeoSeries([gpd.points_from_xy([centres[c][0]], [centres[c][1]])[0] for c in (A, B)], crs="EPSG:4326").to_crs("EPSG:2154")
    pair = {}
    for code, pt in zip((A, B), cen):
        r = recs[code]
        g = iris[iris[code_col].astype(str) == code].geometry.iloc[0]
        pair[code] = {
            "name": r["name"], "commune": r["commune"], "population": r["population"],
            "exposures": {k: {"rank": r["exposures"][k]["rank"], "quarter": r["exposures"][k]["quarter"]} for k in ("thermal", "pollution", "housing")},
            "path": path(g, tf, 1), "centre": [round(v, 1) for v in tf(pt.x, pt.y)],
        }
    cb = clichy.total_bounds
    out = {
        "source": "underlaid.fr — published data of 7 October 2026 (neighbourhood files, map outlines); walking time between inhabited centres, R5 at 4.5 km/h",
        "size": [round(x1 - x0), round(y1 - y0)],
        "iris": "".join(path(g, tf) for g in simple.geometry),
        "communes": "".join(path(g, tf) for g in communes.geometry),
        "paris": path(paris, tf),
        "clichy_iris": "".join(path(g, tf, 1) for g in clichy.geometry),
        "clichy_box": [round(v, 1) for v in (cb[0] - x0, y1 - cb[3], cb[2] - cb[0], cb[3] - cb[1])],
        "walk_minutes": round(meta["minutes"]), "walk_m": meta["length_m"],
        "a": pair[A], "b": pair[B],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
