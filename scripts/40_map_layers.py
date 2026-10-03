"""Background layers of the "Explorer la carte" page (redesign D4, map
style B: no tiles, no grey background, no outer outline).

- communes: boundaries shared by two communes of the metropolis (Paris by
  arrondissement counts as one commune here: only the Paris outline is
  drawn), as lines — the outer edge of the metropolis is left out;
- paris: the outline of Paris (union of its 20 arrondissements);
- rivers: the Seine and the Marne inside the metropolis plus a 2 km margin,
  OpenStreetMap waterway=river lines (© OpenStreetMap contributors, ODbL),
  drawn as a blue line bordered with white.

Coordinates rounded to 5 decimals (~1 m) and simplified (5 m): these are
drawing aids, not data. Output: data/processed/map_layers.geojson, copied
to frontend/public/data/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import osmium
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import linemerge, unary_union

import config

OUT = config.DATA_PROCESSED / "map_layers.geojson"
PBF = config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"
RIVERS = {"La Seine", "Seine", "La Marne", "Marne"}


class Rivers(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def way(self, w):
        if w.tags.get("waterway") == "river" and w.tags.get("name") in RIVERS:
            try:
                coords = [(n.lon, n.lat) for n in w.nodes]
            except osmium.InvalidLocationError:
                return
            if len(coords) >= 2:
                self.lines.append({"name": "Seine" if "Seine" in w.tags["name"] else "Marne", "geometry": LineString(coords)})


def main():
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED)
    iris["insee_com"] = iris["code_iris"].str[:5]
    iris["unit"] = iris["insee_com"].where(~iris["insee_com"].str.startswith("75"), "75056")
    communes = iris.dissolve("unit").reset_index()[["unit", "geometry"]]
    communes["geometry"] = communes.buffer(0)
    outer = unary_union(communes.geometry).boundary.buffer(2)
    inner = unary_union([g.boundary for g in communes.geometry]).difference(outer)
    paris = communes.loc[communes.unit == "75056", "geometry"].iloc[0].boundary

    handler = Rivers()
    handler.apply_file(str(PBF), locations=True)
    rivers = gpd.GeoDataFrame(handler.lines, geometry="geometry", crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED)
    area = unary_union(communes.geometry).buffer(2000)
    rivers = rivers[rivers.intersects(area)]
    river_rows = []
    for name, g in rivers.groupby("name"):
        merged = linemerge(unary_union(list(g.geometry)))
        river_rows.append({"layer": "river", "name": name, "geometry": merged.intersection(area)})

    rows = [{"layer": "communes", "name": "", "geometry": inner}, {"layer": "paris", "name": "Paris", "geometry": paris}, *river_rows]
    out = gpd.GeoDataFrame(rows, geometry="geometry", crs=config.CRS_PROJECTED)
    out["geometry"] = out.simplify(5)
    out = out.to_crs(config.CRS_LATLON)
    OUT.write_text(out.to_json(drop_id=True), encoding="utf-8")
    # Round coordinates (~1 m) to keep the file small.
    import json

    data = json.loads(OUT.read_text(encoding="utf-8"))

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]

    for f in data["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.name} ({OUT.stat().st_size / 1e3:.0f} kB): " + ", ".join(f"{r['layer']} {r['name']}".strip() for r in rows))


if __name__ == "__main__":
    main()
