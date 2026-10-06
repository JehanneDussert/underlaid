"""Check of a cached R5 network (6 October 2026): three workers built the
network without stairs and without steep segments (unknown = not
accessible) at the same time; two of them failed on a corrupted cache file,
the third built the network and computed with it. Is that network right?

The network is rebuilt from scratch in a separate, empty cache, then a few
chunks already computed with the shared network are recomputed with the
fresh one exactly as script 34 does (same origins, destinations, attachment
points, departure, window, speed, time limit) and compared value by value.
Identical -> the shared network is sound. Otherwise every chunk computed
with it must be redone. Changes nothing; prints and writes
data/interim/analysis/validate_network_cache.txt.

Run with an empty cache volume mounted at /root/.cache/r5py, and
ROUTES_SET=routes ROUTES_VERSION=2.
"""
import datetime as dt
import importlib.util
import os
import sys
from pathlib import Path

sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "9G")]
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s34", ROOT / "scripts" / "34_route_travel_times.py")
s34 = importlib.util.module_from_spec(spec)
sys.argv_saved = list(sys.argv)
spec.loader.exec_module(s34)

import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

CHECKS = [("step_free_no_tue10", 2), ("step_free_no_tue01", 45), ("step_free_no_sun10", 2)]


def main():
    import r5py

    osm, gtfs = s34.NETWORKS["acc_unknown_no"]
    net = r5py.TransportNetwork(str(osm), [str(gtfs)])
    orig = s34.origins()
    dest = gpd.read_file(s34.ACCESS_DIR / s34.DEST_FILE)
    dest["wheelchair"] = dest["wheelchair"].fillna("").astype(str) if "wheelchair" in dest else ""
    dest_type = dest.set_index("dest_id")["type"]
    tasks = {t.name: t for t in s34.TASKS}
    lines = ["Fresh rebuild of the step-free network (slope 8 %, unknown = no) vs chunks computed with the shared cache", "=" * 90]
    all_same = True
    for name, k in CHECKS:
        task = tasks[name]
        chunk = orig.iloc[k * s34.CHUNK:(k + 1) * s34.CHUNK]
        _, speed, _ = s34.PROFILES[task.profile]
        modes = [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK] if task.transit else [r5py.TransportMode.WALK]
        ttm = r5py.TravelTimeMatrix(net, origins=chunk, destinations=s34.destinations(task, dest), departure=task.departure,
                                    departure_time_window=s34.WINDOW if task.transit else dt.timedelta(minutes=1),
                                    transport_modes=modes, speed_walking=speed, max_time=dt.timedelta(minutes=s34.MAX_MINUTES),
                                    snap_to_network=s34.SNAP)
        ttm = pd.DataFrame(ttm).dropna(subset=["travel_time"])
        ttm = ttm[ttm.travel_time <= s34.MAX_MINUTES]
        ttm["type"] = ttm["to_id"].map(dest_type)
        fresh = ttm.groupby(["from_id", "type"], as_index=False)["travel_time"].min().rename(columns={"from_id": "cell_id", "travel_time": "minutes"})
        stored = pd.read_parquet(s34.OUT_DIR / f"{name}_{k:02d}.parquet")
        m = stored.merge(fresh, on=["cell_id", "type"], how="outer", suffixes=("_stored", "_fresh"), indicator=True)
        diff = m[(m["_merge"] != "both") | (m.minutes_stored != m.minutes_fresh)]
        same = diff.empty
        all_same &= same
        lines.append(f"{name} chunk {k}: {len(stored)} stored rows, {len(fresh)} fresh rows, {len(diff)} differences -> {'identical' if same else 'DIFFERENT'}")
    lines.append("")
    lines.append("RESULT: shared network sound" if all_same else "RESULT: shared network NOT sound, redo every chunk computed with it")
    out = ROOT / "data" / "interim" / "analysis" / "validate_network_cache.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
