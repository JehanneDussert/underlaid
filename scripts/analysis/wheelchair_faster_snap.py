"""Diagnostic, second part (4 October 2026): is the step-free profile
faster because of where R5 attaches ("snaps") a point to each street
network?

For the cells where the step-free time to the nearest place of a
walkable type (crèche, nursery school, food store, park) is the most below
the standard time, walking only (no transit), both street networks
(standard OSM, OSM without stairs), from the cell centre and from 8 points
20 m and 40 m around it. If the standard time drops back to the step-free
time when the origin moves by a few metres, the gap comes from the
attachment of the origin to the network, not from a shorter route.
Changes nothing; writes data/interim/analysis/wheelchair_faster_snap.txt.
"""
import datetime as dt
import math
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

ACCESS_I = config.DATA_INTERIM / "access"
ACCESS_P = config.DATA_PROCESSED / "access"
OUT = config.DATA_INTERIM / "analysis" / "wheelchair_faster_snap.txt"
TYPES = ["creche", "nursery_school", "food_store", "park"]
N_CELLS = 12


def load(task):
    files = sorted((ACCESS_I / "routes_ttm_neighbourhood").glob(f"{task}_[0-9][0-9].parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def main():
    import r5py

    std = load("standard_tue10")
    sf = load("step_free_no_tue10")
    m = std.merge(sf, on=["cell_id", "type"], suffixes=("_std", "_sf"))
    m = m[m.type.isin(TYPES)]
    m["diff"] = m.minutes_sf - m.minutes_std
    worst = m.sort_values("diff").head(N_CELLS)

    cells = gpd.read_file(ACCESS_P / "demand_grid_idf.geojson")[["cell_id", "geometry"]].set_index("cell_id")
    dest = gpd.read_file(ACCESS_P / "neighbourhood_destinations_idf.geojson")
    cells_l93 = cells.to_crs("EPSG:2154")

    origins = []
    for _, w in worst.iterrows():
        c = cells_l93.loc[w.cell_id].geometry.centroid
        origins.append((f"{w.cell_id}|{w.type}|centre", w.cell_id, w.type, c))
        for r in (20, 40):
            for k in range(8):
                a = 2 * math.pi * k / 8
                origins.append((f"{w.cell_id}|{w.type}|{r}m{k}", w.cell_id, w.type, Point(c.x + r * math.cos(a), c.y + r * math.sin(a))))
    og = gpd.GeoDataFrame(pd.DataFrame(origins, columns=["id", "cell_id", "type", "geometry"]), geometry="geometry", crs="EPSG:2154").to_crs(config.CRS_LATLON)
    dests = dest[dest["type"].isin(TYPES)][["dest_id", "type", "geometry"]].rename(columns={"dest_id": "id"})

    lines = ["Step-free faster than standard: attachment of the origin to the network (walking only)", "=" * 80,
             "cell / type: published cell times std -> step-free; then, recomputed walking only,",
             "centre std/sf, and the range of std/sf over 16 points 20-40 m around", ""]
    results = {}
    for key, osm in [("std", config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), ("sf", ACCESS_I / "idf_no_stairs.osm.pbf")]:
        net = r5py.TransportNetwork(str(osm), [])
        ttm = pd.DataFrame(r5py.TravelTimeMatrix(net, origins=og[["id", "geometry"]], destinations=dests[["id", "geometry"]],
                                                 transport_modes=[r5py.TransportMode.WALK], speed_walking=4.5,
                                                 max_time=dt.timedelta(minutes=45), snap_to_network=True,
                                                 departure=dt.datetime(2026, 10, 13, 10, 0)))
        ttm = ttm.dropna(subset=["travel_time"])
        ttm["type"] = ttm["to_id"].map(dests.set_index("id")["type"])
        ttm = ttm.merge(og[["id", "type"]], left_on=["from_id", "type"], right_on=["id", "type"])
        results[key] = ttm.groupby("from_id")["travel_time"].min()
        del net

    both = pd.DataFrame(results)
    both["cell_id"] = both.index.str.split("|").str[0].astype(worst.cell_id.dtype)
    both["type"] = both.index.str.split("|").str[1]
    both["where"] = both.index.str.split("|").str[2]
    cleared = 0
    for _, w in worst.iterrows():
        b = both[(both.cell_id == w.cell_id) & (both["type"] == w.type)]
        c = b[b["where"] == "centre"]
        ring = b[b["where"] != "centre"]
        inv_ring = (ring.sf < ring["std"]).mean() * 100 if len(ring) else float("nan")
        same_near = ((ring["std"] - c["std"].iloc[0]).abs() if len(c) else pd.Series(dtype=float))
        lines.append(f"cell {w.cell_id} {w.type}: published {w.minutes_std} -> {w.minutes_sf} | "
                     f"centre {c['std'].iloc[0] if len(c) else 'nan'}/{c['sf'].iloc[0] if len(c) else 'nan'} | "
                     f"around: std {ring['std'].min()}-{ring['std'].max()}, sf {ring.sf.min()}-{ring.sf.max()}, "
                     f"step-free faster at {inv_ring:.0f}% of the 16 points")
        if len(ring) and ring["std"].min() <= c["sf"].iloc[0]:
            cleared += 1
    lines.append("")
    lines.append(f"{cleared} of {len(worst)} cells: moving the origin by 20-40 m gives a standard time as short as the step-free one.")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
