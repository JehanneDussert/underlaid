"""Walking routes for act 2 of the launch video ("la course des deux lignes"):
from the focus neighbourhood to the nearest heavy-network stop (full
network, 4.5 km/h) and to the nearest accessible stop (second-run
wheelchair network, 0.8 m/s). Origin: the inhabited cell of the
neighbourhood whose walking times equal the published neighbourhood values
(population-weighted medians), or the closest one; the counters of the
video show the published values. Same points and networks as script 34,
version 2. One network per process (memory): PROFILE=free|wheelchair.
Writes data/interim/analysis/video_route_<profile>.geojson.
"""
import datetime as dt
import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("ROUTES_VERSION", "2")
sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "10G")]
import config  # noqa: E402

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

FOCUS = os.environ["FOCUS"]
PROFILE = os.environ["PROFILE"]


def main():
    import r5py

    s34 = importlib.import_module("34_route_travel_times")
    s36 = importlib.import_module("36_route_aggregate")
    rec = None
    for f in (ROOT / "frontend" / "public" / "data" / "quartiers").glob("[0-9]*.json"):
        for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
            if r["code"] == FOCUS:
                rec = r
    target = rec["station"]["free" if PROFILE == "free" else "wheelchair"]
    stations = pd.read_csv(config.DATA_INTERIM / "analysis" / f"pair_stations_{PROFILE}.csv", dtype={"code_iris": str, "cell_id": str})
    stations = stations[stations.code_iris == FOCUS].copy()
    stations["gap"] = (stations["travel_time"] - target).abs()
    row = stations.sort_values(["gap", "pop"], ascending=[True, False]).iloc[0]
    grid = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["cell_id", "geometry"]]
    orig = s34.snapped(grid[grid.cell_id == row.cell_id].to_crs(config.CRS_LATLON).rename(columns={"cell_id": "id"}).reset_index(drop=True), "origin")
    dest = gpd.read_file(config.DATA_PROCESSED / "access" / "route_destinations_idf.geojson")
    d = s34.snapped(dest[dest.dest_id == row.to_id][["dest_id", "geometry"]].rename(columns={"dest_id": "id"}).reset_index(drop=True), "key")
    net, speed = ("standard", 4.5) if PROFILE == "free" else ("acc_unknown_no", 0.8 * 3.6)
    osm, gtfs = s34.NETWORKS[net]
    network = r5py.TransportNetwork(str(osm), [str(gtfs)])
    it = gpd.GeoDataFrame(r5py.DetailedItineraries(network, origins=orig, destinations=d, departure=dt.datetime(2026, 10, 13, 10, 0),
                                                   transport_modes=[r5py.TransportMode.WALK], speed_walking=speed, snap_to_network=False),
                          geometry="geometry", crs=config.CRS_LATLON)
    line = it.geometry.iloc[0]
    minutes = it["travel_time"].iloc[0].total_seconds() / 60
    out = config.DATA_INTERIM / "analysis" / f"video_route_{PROFILE}.geojson"
    out.write_text(json.dumps({"type": "Feature", "properties": {
        "focus": FOCUS, "profile": PROFILE, "stop": str(row["stop"]), "stop_id": str(row.to_id), "cell_id": str(row.cell_id),
        "route_minutes": round(float(minutes), 1), "published_minutes": int(target), "cell_minutes": float(row.travel_time),
    }, "geometry": line.__geo_interface__}), encoding="utf-8")
    print(f"{PROFILE}: {row['stop']}, route {minutes:.1f} min (published {target}, cell {row.travel_time:.0f})")


if __name__ == "__main__":
    main()
