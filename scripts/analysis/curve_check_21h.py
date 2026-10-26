"""Recompute Tuesday 21:00 (wheelchair, unknown = not accessible) with the
curve code for 300 cells whose published 21:00 time lies outside the
20:00-22:00 curve values; compare with the published cell times (26 October 2026: 300 of 300 equal).
Run in the project Docker image (r5py), as for script 34:
python scripts/analysis/curve_check_21h.py
"""
import datetime as dt, glob, importlib, os, sys
os.environ["ROUTES_VERSION"] = "2"; os.environ["ROUTES_SET"] = "curve"
sys.path.insert(0, "/app/scripts")
s34 = importlib.import_module("34_route_travel_times")
import geopandas as gpd, pandas as pd, r5py
def cells(path, name):
    t = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{path}/{name}_*.parquet"))])
    return t[t.type == "emergency"].set_index("cell_id").minutes
A = "/app/data/interim/access"
c21 = cells(f"{A}/routes_ttm_v2", "step_free_no_tue21")
c20 = cells(f"{A}/routes_ttm_curve_v2", "step_free_no_tue20"); c22 = cells(f"{A}/routes_ttm_curve_v2", "step_free_no_tue22")
df = pd.concat([c20.rename("a"), c21.rename("x"), c22.rename("b")], axis=1).dropna()
out = df[(df.x < df[["a", "b"]].min(axis=1)) | (df.x > df[["a", "b"]].max(axis=1))].sample(300, random_state=20261026)
orig = s34.origins(); orig = orig[orig["id"].astype(str).isin(out.index.astype(str))]
dest = gpd.read_file(s34.ACCESS_DIR / s34.DEST_FILE); dest["wheelchair"] = dest["wheelchair"].fillna("").astype(str)
task = s34.Task("step_free_no_tue21", "step_free_no", True, dt.datetime(2026, 10, 13, 21, 0))
net, speed, _ = s34.PROFILES["step_free_no"]; osm, gtfs = s34.NETWORKS[net]
network = r5py.TransportNetwork(str(osm), [str(gtfs)])
ttm = pd.DataFrame(r5py.TravelTimeMatrix(network, origins=orig, destinations=s34.destinations(task, dest), departure=task.departure,
      departure_time_window=s34.WINDOW, transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK], speed_walking=speed,
      max_time=dt.timedelta(minutes=90), snap_to_network=s34.SNAP)).dropna(subset=["travel_time"])
new = ttm.groupby("from_id").travel_time.min()
cmp = out.join(new.rename("recomputed"), how="inner")
print(f"{len(cmp)} cells; recomputed 21:00 equal to published 21:00: {(cmp.recomputed == cmp.x).sum()}")
print(cmp.head(8).to_string())
