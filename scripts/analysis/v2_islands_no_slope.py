"""Second routing run, neighbourhoods that lose places in wheelchair
(asked on 2026-10-07): the same wheelchair profile (0.8 m/s, stops and
trips marked accessible, unknown = not accessible, Tuesday 10:00) on the
network without stairs but WITHOUT the slope removal. Descriptive only;
the published durations keep the slope removal. Cells of the listed
neighbourhoods only. Writes data/interim/analysis/v2_islands_no_slope.txt.
"""
import datetime as dt
import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ROUTES_VERSION", "2")
sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "10G")]
import config  # noqa: E402

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

CODES = ["751186909", "751187005", "920220101", "930150000", "930470106", "930470110", "930730101", "930780104", "940470000",
         "940480102", "940480103", "940560000", "940700000", "940710107", "940750101", "940750102", "940750103", "940750104"]
A = config.DATA_INTERIM / "access"
OUT = config.DATA_INTERIM / "analysis" / "v2_islands_no_slope.txt"


def main():
    import r5py

    s36 = importlib.import_module("36_route_aggregate")
    s34 = importlib.import_module("34_route_travel_times")
    cells = s36.cells_by_iris()
    cells = cells[cells.code_iris.isin(CODES)]
    grid = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["cell_id", "geometry"]]
    orig = grid[grid.cell_id.isin(cells.cell_id)].to_crs(config.CRS_LATLON).rename(columns={"cell_id": "id"}).reset_index(drop=True)
    orig = s34.snapped(orig, "origin")
    network = r5py.TransportNetwork(str(A / "idf_no_stairs.osm.pbf"), [str(A / "gtfs_accessible_unknown_no.zip")])
    lines = ["Wheelchair profile without the slope removal (0.8 m/s, unknown = not accessible, Tuesday 10:00)", "=" * 90,
             "neighbourhood: place, published (slope removal) -> without slope removal, minutes ('>90' = not reached)"]
    pub = {}
    for name, dest_file, point_set, prefix in [("key", "route_destinations_idf.geojson", "key", "routes_iris_v2_tue10"),
                                              ("neighbourhood", "neighbourhood_destinations_idf.geojson", "neighbourhood", "routes_neighbourhood_v2_tue10")]:
        dest = gpd.read_file(config.DATA_PROCESSED / "access" / dest_file)
        dest = dest[dest["type"] != "station"]
        d = s34.snapped(dest[["dest_id", "geometry"]].rename(columns={"dest_id": "id"}), point_set)
        ttm = pd.DataFrame(r5py.TravelTimeMatrix(network, origins=orig, destinations=d, departure=dt.datetime(2026, 10, 13, 10, 0),
                                                 departure_time_window=dt.timedelta(minutes=60),
                                                 transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
                                                 speed_walking=0.8 * 3.6, max_time=dt.timedelta(minutes=90), snap_to_network=False))
        ttm = ttm.dropna(subset=["travel_time"])
        ttm["type"] = ttm["to_id"].map(dest.set_index("dest_id")["type"])
        best = ttm.groupby(["from_id", "type"], as_index=False)["travel_time"].min().rename(columns={"from_id": "cell_id", "travel_time": "minutes"})
        types = sorted(best["type"].unique())
        summary = s36.summarise(best, cells, types)
        import json
        p = json.loads((config.DATA_PROCESSED / f"{prefix}.json").read_text(encoding="utf-8"))
        L, blocks, ptypes = len(p["layout"]["types"]), p["layout"]["blocks"], p["layout"]["types"]
        i = blocks.index("time:step_free_no") * L
        for code in CODES:
            row = p["iris"].get(code)
            for t in types:
                if t in ptypes and row is not None:
                    pub.setdefault(code, {})[t] = (row[i + ptypes.index(t)], summary.get(code, {}).get(t))
    names = gpd.read_file(config.IRIS_REFERENCE_PATH).set_index("code_iris")
    fmt = lambda v: ">90" if v is None else str(int(v))
    for code in CODES:
        lines.append(f"\n{names.at[code, 'nom_com']} — {names.at[code, 'nom_iris']} ({code})")
        changed = [(t, a, b) for t, (a, b) in sorted(pub.get(code, {}).items()) if a != b]
        lines.append("  " + "; ".join(f"{t} {fmt(a)} -> {fmt(b)}" for t, a, b in changed) if changed else "  identical")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
