"""Step-free network without steep segments (pre-registered and validated on
2026-10-04, docs/preregistrations/2026-10-04-profil-fauteuil-roulant.md).

From the network without stairs (script 30), every walkable way of Paris
and the inner suburbs gets an altitude profile from the IGN RGE ALTI 1 m
(Licence Ouverte 2.0): points every 2 m along the way, altitude of the
1 m cell, gradient over a window of about 12 m (6 points on each side) to
smooth the noise of the terrain model. A node-to-node segment whose
largest windowed gradient exceeds the threshold is removed: the way is cut
into the runs that remain (new way ids, same tags). Main threshold 8 %
(tolerance of the arrêté of 15 January 2007 on accessible public roads),
sensitivity 6 % (openrouteservice).

Not evaluated, kept as they are: bridges, tunnels, covered passages and
ways at another level (bridge, tunnel, covered, layer != 0), whose
altitude the terrain model does not give; ways shorter than 12 m (no
window); ways outside the four départements (no terrain model there).

Artefact rules (added on 5 October 2026 after a first run, before any
routing with these networks: the steepest "slopes", up to 139 %, were at
the edges of railway cuttings, where a street crossing the tracks seems to
drop into the cutting because the terrain model gives the ground, not the
bridge): points within 20 m of a bridge or tunnel are not used, and a
windowed gradient above 25 % is treated as an error of the terrain model
(no public street or path open to wheelchairs is that steep), not as a
slope.

Outputs: data/interim/access/idf_no_stairs_slope8.osm.pbf and
idf_no_stairs_slope6.osm.pbf, plus slope_network_report.txt (length
removed by département and threshold, steepest segments for an imagery
check).
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import osmium
import pandas as pd
import rasterio
from pyproj import Transformer
from shapely.geometry import Point

import config

WORK = config.DATA_INTERIM / "access"
SRC = WORK / "idf_no_stairs.osm.pbf"
DEM_DIR = config.DATA_RAW / "rgealti" / "extracted"
REPORT = WORK / "slope_network_report.txt"
THRESHOLDS = (8, 6)
STEP_M = 2.0
HALF = 3  # points on each side: window of 2 * 3 * 2 m = 12 m
NEAR_STRUCTURE_M = 20
MAX_PLAUSIBLE_GRADE = 25.0
NOT_WALKABLE = {"motorway", "motorway_link", "trunk", "trunk_link", "construction", "proposed", "raceway",
                "bus_guideway", "escape", "abandoned", "elevator"}
NEW_WAY_ID = 50_000_000_000  # well above any OSM way id


class Ways(osmium.SimpleHandler):
    def __init__(self, bbox):
        super().__init__()
        self.bbox = bbox
        self.ways = {}
        self.structures = []

    def way(self, w):
        t = w.tags
        structure = (t.get("bridge", "no") != "no" or t.get("tunnel", "no") != "no"
                     or t.get("man_made") == "bridge" or t.get("covered", "no") != "no")
        if structure:
            try:
                self.structures.append([(n.lon, n.lat) for n in w.nodes])
            except osmium.InvalidLocationError:
                pass
        hw = t.get("highway")
        if hw is None or hw in NOT_WALKABLE:
            return
        if structure or t.get("layer", "0") != "0":
            return
        try:
            nodes = [(n.ref, n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError:
            return
        lon = [n[1] for n in nodes]
        lat = [n[2] for n in nodes]
        x0, y0, x1, y1 = self.bbox
        if max(lon) < x0 or min(lon) > x1 or max(lat) < y0 or min(lat) > y1 or len(nodes) < 2:
            return
        self.ways[w.id] = nodes


def dem_tiles():
    """{(x_km, y_km): path} for the 1 km tiles (file name gives the upper-left corner in km)."""
    tiles = {}
    for p in DEM_DIR.rglob("*_MNT_LAMB93_IGN69.asc"):
        parts = p.stem.split("_")
        x, y = int(parts[2]), int(parts[3])
        tiles[(x, y)] = p
    return tiles


def sample_altitudes(x: np.ndarray, y: np.ndarray, tiles) -> np.ndarray:
    """Altitude of the 1 m cell containing each point (NaN outside the model)."""
    z = np.full(len(x), np.nan)
    # Tile of a point: upper-left corner (x_km, y_km), covering x in [x_km, x_km+1) km, y in (y_km-1, y_km] km.
    kx = np.floor(x / 1000).astype(int)
    ky = np.ceil(y / 1000).astype(int)
    order = pd.DataFrame({"kx": kx, "ky": ky, "i": np.arange(len(x))}).groupby(["kx", "ky"])["i"]
    for (tx, ty), idx in order:
        path = tiles.get((tx, ty))
        if path is None:
            continue
        with rasterio.open(path) as src:
            band = src.read(1)
            rows, cols = rasterio.transform.rowcol(src.transform, x[idx.to_numpy()], y[idx.to_numpy()])
            rows, cols = np.asarray(rows), np.asarray(cols)
            ok = (rows >= 0) & (rows < band.shape[0]) & (cols >= 0) & (cols < band.shape[1])
            vals = np.full(len(rows), np.nan)
            vals[ok] = band[rows[ok], cols[ok]]
            vals[vals <= -9999] = np.nan
            z[idx.to_numpy()] = vals
    return z


def main():
    tiles = dem_tiles()
    to_l93 = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    to_ll = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)
    xs = [k[0] * 1000 for k in tiles]
    ys = [k[1] * 1000 for k in tiles]
    lon0, lat0 = to_ll.transform(min(xs), min(ys) - 1000)
    lon1, lat1 = to_ll.transform(max(xs) + 1000, max(ys))
    h = Ways((lon0, lat0, lon1, lat1))
    h.apply_file(str(SRC), locations=True, idx="flex_mem")
    print(f"{len(h.ways):,} walkable ways in the terrain model area", flush=True)

    # Densify every way, keep for each sample its way and segment index.
    way_ids, seg_idx, sx, sy, sdist = [], [], [], [], []
    seg_len = {}
    for wid, nodes in h.ways.items():
        lon = np.array([n[1] for n in nodes])
        lat = np.array([n[2] for n in nodes])
        x, y = to_l93.transform(lon, lat)
        x, y = np.asarray(x), np.asarray(y)
        d = np.hypot(np.diff(x), np.diff(y))
        seg_len[wid] = d
        cum = np.concatenate([[0], np.cumsum(d)])
        if cum[-1] < 2 * HALF * STEP_M:
            continue
        t = np.arange(0, cum[-1] + 1e-9, STEP_M)
        seg = np.clip(np.searchsorted(cum, t, side="right") - 1, 0, len(d) - 1)
        frac = np.where(d[seg] > 0, (t - cum[seg]) / np.where(d[seg] > 0, d[seg], 1), 0)
        way_ids.append(np.full(len(t), wid, dtype=np.int64))
        seg_idx.append(seg)
        sx.append(x[seg] + frac * (x[seg + 1] - x[seg]))
        sy.append(y[seg] + frac * (y[seg + 1] - y[seg]))
        sdist.append(t)
    way_ids = np.concatenate(way_ids)
    seg_idx = np.concatenate(seg_idx)
    sx, sy, sdist = np.concatenate(sx), np.concatenate(sy), np.concatenate(sdist)
    print(f"{len(sx):,} altitude samples", flush=True)
    z = sample_altitudes(sx, sy, tiles)

    # Points near a bridge or a tunnel: not used (the terrain model gives the
    # ground below the bridge, or above the tunnel).
    from shapely import STRtree, points as shp_points
    from shapely.geometry import LineString

    struct = []
    for coords in h.structures:
        if len(coords) >= 2:
            x, y = to_l93.transform([c[0] for c in coords], [c[1] for c in coords])
            struct.append(LineString(list(zip(x, y))))
    tree = STRtree(struct)
    pts = shp_points(np.column_stack([sx, sy]))
    near = np.zeros(len(pts), dtype=bool)
    hit = tree.query(pts, predicate="dwithin", distance=NEAR_STRUCTURE_M)
    near[np.unique(hit[0])] = True
    z[near] = np.nan
    print(f"{near.mean():.1%} of samples within {NEAR_STRUCTURE_M} m of a bridge or tunnel ({len(struct):,} structures)", flush=True)

    # Windowed gradient within each way (no window across two ways).
    grade = np.full(len(z), np.nan)
    starts = np.flatnonzero(np.r_[True, way_ids[1:] != way_ids[:-1]])
    ends = np.r_[starts[1:], len(z)]
    for s, e in zip(starts, ends):
        n = e - s
        if n <= 2 * HALF:
            continue
        zz, dd = z[s:e], sdist[s:e]
        g = np.full(n, np.nan)
        g[HALF:n - HALF] = (zz[2 * HALF:] - zz[:n - 2 * HALF]) / (dd[2 * HALF:] - dd[:n - 2 * HALF])
        grade[s:e] = np.abs(g) * 100
    implausible = grade > MAX_PLAUSIBLE_GRADE
    grade[implausible] = np.nan
    df = pd.DataFrame({"way": way_ids, "seg": seg_idx, "grade": grade, "x": sx, "y": sy})
    seg_max = df.groupby(["way", "seg"])["grade"].max()

    lines = ["Step-free network without steep segments (RGE ALTI 1 m, window 12 m)", "=" * 72,
             f"walkable ways evaluated: {df.way.nunique():,}; samples {len(df):,}; samples without altitude {np.isnan(z).mean():.1%} "
             f"(of which near a bridge or tunnel {near.mean():.1%}); windowed gradients above {MAX_PLAUSIBLE_GRADE:.0f} % "
             f"treated as terrain-model errors: {implausible.mean():.2%} of samples"]
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs("EPSG:2154")[["code_iris", "geometry"]]
    for thr in THRESHOLDS:
        steep = seg_max[seg_max > thr]
        steep_set = defaultdict(set)
        for (wid, sg) in steep.index:
            steep_set[wid].add(sg)
        # Length removed by département (segment midpoints).
        mids = []
        for (wid, sg), gmax in steep.items():
            nodes = h.ways[wid]
            x, y = to_l93.transform([nodes[sg][1], nodes[sg + 1][1]], [nodes[sg][2], nodes[sg + 1][2]])
            mids.append({"way": wid, "seg": sg, "grade": gmax, "len": seg_len[wid][sg], "geometry": Point(np.mean(x), np.mean(y))})
        removed = gpd.GeoDataFrame(mids, geometry="geometry", crs="EPSG:2154")
        removed = gpd.sjoin(removed, iris, predicate="within", how="left")
        removed["dep"] = removed.code_iris.str[:2]
        total = {}
        for wid, d in seg_len.items():
            total.setdefault("all", 0.0)
            total["all"] += float(d.sum())
        by_dep = removed.groupby("dep")["len"].sum() / 1000
        lines.append(f"\nthreshold {thr} %: {len(steep):,} segments removed in {len(steep_set):,} ways, "
                     f"{removed['len'].sum() / 1000:.1f} km of {total['all'] / 1000:,.0f} km evaluated "
                     f"({100 * removed['len'].sum() / total['all']:.2f} %); by département (km): "
                     + ", ".join(f"{k} {v:.1f}" for k, v in by_dep.items()))
        if thr == THRESHOLDS[0]:
            lines.append("steepest segments (for an imagery check):")
            for _, r in removed.sort_values("grade", ascending=False).head(10).iterrows():
                lon, lat = to_ll.transform(r.geometry.x, r.geometry.y)
                lines.append(f"  way {r.way} segment {r.seg}: {r.grade:.1f} %, {r.len:.0f} m, at {lat:.5f},{lon:.5f}")
        write_network(SRC, WORK / f"idf_no_stairs_slope{thr}.osm.pbf", steep_set, h.ways)
        print(lines[-1] if thr != THRESHOLDS[0] else "\n".join(lines[-11:]), flush=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_network(src: Path, dest: Path, steep_set: dict, ways: dict) -> None:
    """Copy the network, cutting each way with steep segments into the runs left."""
    if dest.exists():
        dest.unlink()
    next_id = NEW_WAY_ID
    with osmium.SimpleWriter(str(dest)) as writer:
        for obj in osmium.FileProcessor(str(src)):
            if not (obj.is_way() and obj.id in steep_set):
                writer.add(obj)
                continue
            refs = [n.ref for n in obj.nodes]
            cut = steep_set[obj.id]
            run = [refs[0]]
            for i in range(len(refs) - 1):
                if i in cut:
                    if len(run) >= 2:
                        writer.add(osmium.osm.mutable.Way(id=next_id, nodes=run, tags=dict(obj.tags)))
                        next_id += 1
                    run = [refs[i + 1]]
                else:
                    run.append(refs[i + 1])
            if len(run) >= 2:
                writer.add(osmium.osm.mutable.Way(id=next_id, nodes=run, tags=dict(obj.tags)))
                next_id += 1


if __name__ == "__main__":
    main()
