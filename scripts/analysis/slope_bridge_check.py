"""Bridges and the slope network (check asked on 2026-10-07): were segments
on or near bridges removed for slope? The pre-registration (2026-10-04)
keeps bridges and tunnels out of the slope calculation; script 44 skips
ways tagged bridge / tunnel / covered / layer != 0 and ignores altitude
points within 20 m of such a structure.

Removed segments = node-to-node segments of walkable ways in the no-stairs
network that are absent from the slope-8 network. For each: tags of its
way, distance to the nearest bridge or tunnel, and whether it crosses a
railway, a waterway or a motorway / trunk road (which a street can only do
on a bridge or in a tunnel, or at a level crossing).
Writes data/interim/analysis/slope_bridge_check.txt and
data/interim/access/slope8_removed_segments.csv.
"""
import sys
from pathlib import Path

import numpy as np
import osmium
import pandas as pd
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

A = config.DATA_INTERIM / "access"
OUT = config.DATA_INTERIM / "analysis" / "slope_bridge_check.txt"
NOT_WALK = {"motorway", "motorway_link", "trunk", "trunk_link", "construction", "proposed", "raceway",
            "bus_guideway", "escape", "abandoned", "elevator", "steps"}
T = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)


class Edges(osmium.SimpleHandler):
    def __init__(self, full):
        super().__init__()
        self.full = full
        self.edges = {}
        self.structures, self.barriers = [], []

    def way(self, w):
        t = w.tags
        try:
            nodes = [(n.ref, n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        if self.full:
            if t.get("bridge", "no") != "no" or t.get("tunnel", "no") != "no" or t.get("man_made") == "bridge" or t.get("covered", "no") != "no":
                self.structures.append(nodes)
            if (t.get("railway") in ("rail", "light_rail", "subway", "tram", "narrow_gauge")
                    or t.get("waterway") in ("river", "canal", "stream")
                    or t.get("highway") in ("motorway", "trunk", "motorway_link", "trunk_link")):
                if t.get("bridge", "no") == "no" and t.get("tunnel", "no") == "no" and t.get("layer", "0") == "0":
                    self.barriers.append(nodes)
        hw = t.get("highway")
        if hw is None or hw in NOT_WALK or len(nodes) < 2:
            return
        info = (w.id if w.id < 50_000_000_000 else -1, hw, t.get("bridge", ""), t.get("tunnel", ""), t.get("layer", ""), t.get("name", ""))
        for a, b in zip(nodes, nodes[1:]):
            self.edges[(a[0], b[0])] = (a[1], a[2], b[1], b[2]) + info


def line(nodes):
    x, y = T.transform([n[1] for n in nodes], [n[2] for n in nodes])
    return LineString(list(zip(x, y)))


def main():
    full = Edges(True)
    full.apply_file(str(A / "idf_no_stairs.osm.pbf"), locations=True, idx="flex_mem")
    s8 = Edges(False)
    s8.apply_file(str(A / "idf_no_stairs_slope8.osm.pbf"), locations=True, idx="flex_mem")
    kept = set(s8.edges)
    removed = [(k, v) for k, v in full.edges.items() if k not in kept and (k[1], k[0]) not in kept]
    df = pd.DataFrame([dict(a=k[0], b=k[1], lon0=v[0], lat0=v[1], lon1=v[2], lat1=v[3], way=v[4], highway=v[5], bridge=v[6],
                            tunnel=v[7], layer=v[8], name=v[9]) for k, v in removed])
    geoms = [LineString(list(zip(*T.transform([r.lon0, r.lon1], [r.lat0, r.lat1])))) for r in df.itertuples()]
    st = STRtree([line(n) for n in full.structures if len(n) >= 2])
    br = STRtree([line(n) for n in full.barriers if len(n) >= 2])
    idx, dist = st.query_nearest(geoms, return_distance=True, all_matches=False)
    d = np.full(len(geoms), np.inf)
    d[idx[0]] = dist
    df["dist_structure_m"] = d
    hit = br.query(geoms, predicate="crosses")
    df["crosses_barrier"] = False
    df.loc[np.unique(hit[0]), "crosses_barrier"] = True
    df["len_m"] = [g.length for g in geoms]
    df.to_csv(A / "slope8_removed_segments.csv", index=False)

    lines = ["Slope-8 network: removed segments on or near bridges", "=" * 60,
             f"removed segments: {len(df):,} ({df.len_m.sum() / 1000:.1f} km)",
             f"  way tagged bridge / tunnel / layer != 0: {int(((df.bridge.fillna('') != '') & (df.bridge != 'no') | (df.tunnel.fillna('') != '') & (df.tunnel != 'no') | ((df.layer.fillna('') != '') & (df.layer != '0'))).sum())}",
             f"  crossing a railway, waterway or motorway / trunk without a bridge or tunnel tag: {int(df.crosses_barrier.sum())} ({df.loc[df.crosses_barrier, 'len_m'].sum():.0f} m)"]
    for lo, hi in [(0, 20), (20, 30), (30, 50), (50, 100), (100, np.inf)]:
        m = (df.dist_structure_m >= lo) & (df.dist_structure_m < hi)
        lines.append(f"  distance to the nearest bridge or tunnel {lo}-{hi} m: {int(m.sum()):,} segments, {df.loc[m, 'len_m'].sum() / 1000:.1f} km")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(df[df.crosses_barrier].head(20)[["way", "highway", "name", "lat0", "lon0", "len_m"]].to_string())


if __name__ == "__main__":
    main()
