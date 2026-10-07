"""Launch video, candidate pairs: nearest heavy-network stop on foot (full
network, 4.5 km/h) and nearest accessible stop in a wheelchair (second-run
wheelchair network, 0.8 m/s), per inhabited cell of each neighbourhood,
with the stop names and their wheelchair_boarding value in the GTFS (after
inheritance from the parent station, as in script 30). Same points and
networks as the second calculation (script 34, version 2).
Usage: CODES=code1,code2,... [PROFILE=free|wheelchair]; writes
data/interim/analysis/pair_stations[_<profile>].csv.
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


def main():
    import r5py

    s34 = importlib.import_module("34_route_travel_times")
    s36 = importlib.import_module("36_route_aggregate")
    codes = os.environ["CODES"].split(",")
    cells = s36.cells_by_iris()
    cells = cells[cells.code_iris.isin(codes)]
    grid = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["cell_id", "geometry"]]
    orig = s34.snapped(grid[grid.cell_id.isin(cells.cell_id)].to_crs(config.CRS_LATLON).rename(columns={"cell_id": "id"}).reset_index(drop=True), "origin")
    dest = gpd.read_file(config.DATA_PROCESSED / "access" / "route_destinations_idf.geojson")
    st = dest[dest["type"] == "station"]
    rows = []
    only = os.environ.get("PROFILE")  # one network per process (memory)
    for label, net, speed, keep in [("free", "standard", 4.5, None), ("wheelchair", "acc_unknown_no", 0.8 * 3.6, {"1"})]:
        if only and label != only:
            continue
        d = st if keep is None else st[st["wheelchair"].isin(keep)]
        dd = s34.snapped(d[["dest_id", "geometry"]].rename(columns={"dest_id": "id"}), "key")
        osm, gtfs = s34.NETWORKS[net]
        network = r5py.TransportNetwork(str(osm), [str(gtfs)])
        t = pd.DataFrame(r5py.TravelTimeMatrix(network, origins=orig, destinations=dd, departure=dt.datetime(2026, 10, 13, 10, 0),
                                               departure_time_window=dt.timedelta(minutes=1), transport_modes=[r5py.TransportMode.WALK],
                                               speed_walking=speed, max_time=dt.timedelta(minutes=90), snap_to_network=False)).dropna()
        best = t.sort_values("travel_time").groupby("from_id").head(1)
        best = best.assign(profile=label, stop=best["to_id"].map(d.set_index("dest_id")["name"]),
                           wheelchair_boarding=best["to_id"].map(d.set_index("dest_id")["wheelchair"]))
        rows.append(best.rename(columns={"from_id": "cell_id"}).merge(cells, on="cell_id"))
    out = pd.concat(rows, ignore_index=True)
    path = config.DATA_INTERIM / "analysis" / f"pair_stations{'_' + only if only else ''}.csv"
    out.to_csv(path, index=False)
    print(out.groupby(["code_iris", "profile", "stop", "wheelchair_boarding"])["pop"].sum().round().to_string())


if __name__ == "__main__":
    main()
