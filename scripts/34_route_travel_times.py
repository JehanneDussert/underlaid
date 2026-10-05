"""Travel times to the nearest key destinations, for the routes page.

Pre-registered on 2026-10-02 before any of these times was computed
(CLAUDE.md, "Hypothèse de travail", routes pre-registration and its
addendum). From every inhabited 200 m cell of the MGP (Filosofi 2021
grid, script 29) to the nearest destination of each type (script 33),
with R5 (r5py) on the networks of script 30. Only the minimum time per
cell and destination type is kept.

Profiles (4 per time slot):
- standard: full OSM network + full IDFM GTFS, walking 4.5 km/h;
- slow: same networks, walking 3.4 km/h (0.943 m/s, women aged 80-99,
  Bohannon & Andrews 2011, Physiotherapy 97(3):182-189);
- step_free_no / step_free_yes ("sans marches": wheelchair, pushchair):
  OSM without stairs (script 30) + GTFS restricted to accessible stops and
  trips, unknown counted as not accessible / accessible; walking 4.5 km/h.
Time slots: departures over 60 min, R5 median travel time — Tuesday
13 October 2026 at 10:00 (main), 21:00 and 01:00; Sunday 11 October 2026
at 10:00. Maximum 90 min; beyond, the cell is "not reached" (no row).

Stations (heavy-network stop points) are reached on foot only, so they get
one walking task per profile (no time slot); step-free profiles go to
accessible stops only (wheelchair = 1; also 0 in the "unknown = yes"
variant).

Output: data/interim/access/routes_ttm/<task>_<chunk>.parquet with
cell_id, type, minutes. Long-running (about 21 h with 3 processes);
resumable and shareable between processes like script 31 (env WORKER /
WORKERS); progress in data/interim/access/routes_progress.txt.

ROUTES_VERSION=2 (decided 2026-10-04, see CLAUDE.md): origins and
destinations are first moved onto the common attachment points of script
42, the same for the four profiles (fixes durations shorter step-free than
without constraint); outputs go to *_v2 directories, the first run is kept
for comparison. ROUTES_PILOT=<file of cell ids>: only those origins, output
in *_pilot (checks before the full run).

Runs in the access Docker image (Dockerfile.access).
"""
import os
import sys

sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "26G")]

import datetime as dt
import gc
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config

ACCESS_DIR = config.DATA_PROCESSED / "access"
WORK_DIR = config.DATA_INTERIM / "access"
# ROUTES_SET=neighbourhood: second run for the "Your neighbourhood" page
# (script 37 destinations, Tuesday 10:00 only, no station task), validated
# on 2026-10-03; smaller origin chunks because there are about twice as
# many destinations.
# ROUTES_SET=paris: public toilets and drinking fountains, Paris only
# (script 41; decision of 2026-10-03), Paris cells as origins, Tuesday
# 10:00, four profiles.
ROUTES_SET = os.environ.get("ROUTES_SET", "routes")
NEIGHBOURHOOD = ROUTES_SET == "neighbourhood"
PARIS = ROUTES_SET == "paris"
VERSION = os.environ.get("ROUTES_VERSION", "1")
PILOT = os.environ.get("ROUTES_PILOT")
# Version 2: the points already lie on a common street, so r5py must not move
# them again (snap_to_network moves a point onto the network before routing
# without counting that distance, and differently in each network; diagnosed
# on 4 October 2026). R5 then links each point itself and counts the link.
SNAP = VERSION != "2"
SUFFIX = ("_pilot2" if VERSION == "2" else "_pilot") if PILOT else ("_v2" if VERSION == "2" else "")
OUT_DIR = WORK_DIR / ({"neighbourhood": "routes_ttm_neighbourhood", "paris": "routes_ttm_paris"}.get(ROUTES_SET, "routes_ttm") + SUFFIX)
PROGRESS = WORK_DIR / {"neighbourhood": "routes_neighbourhood_progress.txt", "paris": "routes_paris_progress.txt"}.get(ROUTES_SET, "routes_progress.txt").replace(".txt", f"{SUFFIX}.txt")
SNAPPED = ACCESS_DIR / "snapped_points.csv"
DEST_FILE = {"neighbourhood": "neighbourhood_destinations_idf.geojson", "paris": "paris_amenities_idf.geojson"}.get(ROUTES_SET, "route_destinations_idf.geojson")
CHUNK = 150 if NEIGHBOURHOOD else 300
MAX_MINUTES = 90
WINDOW = dt.timedelta(minutes=60)
WORKER = int(os.environ.get("WORKER", "0"))
WORKERS = int(os.environ.get("WORKERS", "1"))

SLOTS = {
    "tue10": dt.datetime(2026, 10, 13, 10, 0),
    "tue21": dt.datetime(2026, 10, 13, 21, 0),
    "tue01": dt.datetime(2026, 10, 13, 1, 0),
    "sun10": dt.datetime(2026, 10, 11, 10, 0),
}
NETWORKS = {
    "standard": (config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf", config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"),
    "acc_unknown_no": (WORK_DIR / "idf_no_stairs.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_no.zip"),
    "acc_unknown_yes": (WORK_DIR / "idf_no_stairs.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_yes.zip"),
}
if VERSION == "2":
    # Pre-registered on 2026-10-04 (docs/preregistrations): the wheelchair
    # profile uses the network without stairs and without segments steeper
    # than 8 % (script 44); sensitivity on a 6 % network.
    NETWORKS.update({
        "acc_unknown_no": (WORK_DIR / "idf_no_stairs_slope8.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_no.zip"),
        "acc_unknown_yes": (WORK_DIR / "idf_no_stairs_slope8.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_yes.zip"),
        "acc_unknown_no_slope6": (WORK_DIR / "idf_no_stairs_slope6.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_no.zip"),
    })
# profile -> (network, walking speed km/h, station accessibility values kept)
PROFILES = {
    "standard": ("standard", 4.5, None),
    "slow": ("standard", 3.4, None),
    "step_free_no": ("acc_unknown_no", 4.5, {"1"}),
    "step_free_yes": ("acc_unknown_yes", 4.5, {"1", "0"}),
}
WHEELCHAIR_KMH = 0.8 * 3.6  # 0.8 m/s, pre-registered on 2026-10-04
if VERSION == "2":
    PROFILES.update({
        "step_free_no": ("acc_unknown_no", WHEELCHAIR_KMH, {"1"}),
        "step_free_yes": ("acc_unknown_yes", WHEELCHAIR_KMH, {"1", "0"}),
        # Sensitivity (Tuesday 10:00 only, unknown = not accessible).
        "sens_speed05": ("acc_unknown_no", 0.5 * 3.6, {"1"}),
        "sens_speed10": ("acc_unknown_no", 1.0 * 3.6, {"1"}),
        "sens_slope6": ("acc_unknown_no_slope6", WHEELCHAIR_KMH, {"1"}),
    })
SENSITIVITY = {"sens_speed05", "sens_speed10", "sens_slope6"}


@dataclass
class Task:
    name: str
    profile: str
    transit: bool
    departure: dt.datetime


if NEIGHBOURHOOD or PARIS:
    TASKS = [Task(f"{p}_tue10", p, True, SLOTS["tue10"]) for p in PROFILES]
else:
    TASKS = [Task(f"{p}_{s}", p, True, d) for p in PROFILES for s, d in SLOTS.items() if p not in SENSITIVITY or s == "tue10"]
    TASKS += [Task(f"{p}_stations_walk", p, False, SLOTS["tue10"]) for p in PROFILES]
# ROUTES_PROFILES=standard,slow: only these profiles (lets the profiles that
# do not depend on a network still being prepared start first).
if os.environ.get("ROUTES_PROFILES"):
    _keep = set(os.environ["ROUTES_PROFILES"].split(","))
    TASKS = [t for t in TASKS if t.profile in _keep]


def origins() -> gpd.GeoDataFrame:
    """Inhabited grid cells whose centre lies in an MGP IRIS."""
    cells = gpd.read_file(ACCESS_DIR / "demand_grid_idf.geojson")[["cell_id", "pop", "geometry"]]
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(cells.crs)
    inside = gpd.sjoin(cells, iris, predicate="within", how="inner")
    inside = inside[inside["pop"] > 0].drop_duplicates("cell_id")
    if PARIS:
        inside = inside[inside["code_iris"].astype(str).str.startswith("75")]
    out = inside[["cell_id", "geometry"]].rename(columns={"cell_id": "id"}).to_crs(config.CRS_LATLON).reset_index(drop=True)
    if PILOT:
        keep = set(Path(PILOT).read_text().split())
        out = out[out["id"].astype(str).isin(keep)].reset_index(drop=True)
    return snapped(out, "origin")


def snapped(points: gpd.GeoDataFrame, point_set: str) -> gpd.GeoDataFrame:
    """Version 2: replace each point by its common attachment point (script 42)."""
    if VERSION != "2":
        return points
    s = pd.read_csv(SNAPPED, dtype={"id": str})
    s = s[s["set"] == point_set].set_index("id")
    ids = points["id"].astype(str)
    missing = ~ids.isin(s.index)
    if missing.any():
        raise SystemExit(f"{missing.sum()} {point_set} points without an attachment point: run script 42 again")
    out = points.copy()
    out["geometry"] = gpd.points_from_xy(s.loc[ids, "lon"].to_numpy(), s.loc[ids, "lat"].to_numpy())
    return out.set_crs(config.CRS_LATLON, allow_override=True)


def destinations(task: Task, dest: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if task.transit:
        d = dest[dest["type"] != "station"]
    else:
        keep = PROFILES[task.profile][2]
        d = dest[dest["type"] == "station"]
        if keep is not None:
            d = d[d["wheelchair"].isin(keep)]
    return snapped(d[["dest_id", "geometry"]].rename(columns={"dest_id": "id"}), {"neighbourhood": "neighbourhood", "paris": "paris"}.get(ROUTES_SET, "key"))


def write_progress(started, done_at_start, total, current):
    done = len(list(OUT_DIR.glob("*.parquet")))
    elapsed = time.time() - started
    eta = ""
    if done > done_at_start:
        eta = f" — about {elapsed / (done - done_at_start) * (total - done) / 60:.0f} min left"
    PROGRESS.write_text(
        f"Routes travel times: {100 * done / total:.0f}% ({done}/{total} chunks, {WORKERS} processes){eta}\n"
        f"Worker {WORKER} on: {current}\nUpdated {dt.datetime.now():%H:%M:%S}\n",
        encoding="utf-8",
    )


def main():
    import jpype
    import r5py

    orig = origins()
    dest = gpd.read_file(ACCESS_DIR / DEST_FILE)
    dest["wheelchair"] = dest["wheelchair"].fillna("").astype(str) if "wheelchair" in dest else ""
    dest_type = dest.set_index("dest_id")["type"]
    print(f"{len(orig)} origin cells, {len(dest)} destinations", flush=True)

    jobs = []
    for task in sorted(TASKS, key=lambda t: list(NETWORKS).index(PROFILES[t.profile][0])):
        for k, start in enumerate(range(0, len(orig), CHUNK)):
            jobs.append((task, k, orig.iloc[start:start + CHUNK]))
    total = len(jobs)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    done_at_start = len(list(OUT_DIR.glob("*.parquet")))
    network_name, network = None, None

    for index, (task, k, chunk) in enumerate(jobs):
        out = OUT_DIR / f"{task.name}_{k:02d}.parquet"
        if index % WORKERS != WORKER or out.exists():
            continue
        net, speed, _ = PROFILES[task.profile]
        label = f"{task.name}, chunk {k + 1}"
        if net != network_name:
            write_progress(started, done_at_start, total, f"loading the '{net}' network")
            network = None
            gc.collect()
            jpype.java.lang.System.gc()
            osm, gtfs = NETWORKS[net]
            network = r5py.TransportNetwork(str(osm), [str(gtfs)])
            network_name = net
        write_progress(started, done_at_start, total, label)
        modes = [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK] if task.transit else [r5py.TransportMode.WALK]
        ttm = r5py.TravelTimeMatrix(
            network,
            origins=chunk,
            destinations=destinations(task, dest),
            departure=task.departure,
            departure_time_window=WINDOW if task.transit else dt.timedelta(minutes=1),
            transport_modes=modes,
            speed_walking=speed,
            max_time=dt.timedelta(minutes=MAX_MINUTES),
            snap_to_network=SNAP,
        )
        ttm = pd.DataFrame(ttm).dropna(subset=["travel_time"])
        ttm = ttm[ttm.travel_time <= MAX_MINUTES]
        ttm["type"] = ttm["to_id"].map(dest_type)
        best = ttm.groupby(["from_id", "type"], as_index=False)["travel_time"].min()
        best = best.rename(columns={"from_id": "cell_id", "travel_time": "minutes"})
        best.astype({"minutes": "int16"}).to_parquet(out, index=False)
        write_progress(started, done_at_start, total, label + " done")
        print(f"{label}: {len(best)} cell-type rows", flush=True)
    if len(list(OUT_DIR.glob("*.parquet"))) == total:
        PROGRESS.write_text(f"Routes travel times: 100% — finished {dt.datetime.now():%Y-%m-%d %H:%M}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
