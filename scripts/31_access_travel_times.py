"""Travel-time matrices for the access E2SFCA (indicators in script 32).

From every inhabited 200 m cell of Île-de-France (script 29) to every GP
site (script 27) and pharmacy (script 28), with R5 (via r5py) on the
networks built by script 30.

Tasks (one matrix each, see TASKS):
- GPs, walking or public transport (best of the two), max 25 min (the
  DREES decay stops at 20 min; 25 allows the +5 min sensitivity run):
  standard network, and the two accessible variants ("unknown = not
  accessible" / "unknown = accessible"), each at the main walking speed
  and at the reduced one, morning departures; then the three networks at
  the second departure window.
- Pharmacies, walking only, max 20 min (15 min zone + 5 min sensitivity):
  standard walking network, step-free network, and step-free at the
  reduced speed.

Parameters:
- REFERENCE_DAY: Tuesday 13 October 2026, a school day outside holidays
  (Toussaint holidays, zone C, start on the 17th) and inside the GTFS
  calendar (2026-09-28 to 2026-10-30). Rule for later runs: the first
  Tuesday at least 7 days after the GTFS download, outside school holidays
  of zone C and public holidays.
- Departure windows: 10:00-11:00 (main, late morning) and 17:30-18:30
  (sensitivity). R5 returns the median travel time over departures every
  minute of the window.
- Walking speed: 4.5 km/h main (1.25 m/s, just under the comfortable
  speeds of adults, 1.3-1.4 m/s, Bohannon & Andrews 2011, Physiotherapy
  97(3):182-189), 2.8 km/h reduced (0.79 m/s, manual wheelchair users,
  Tolerico et al. 2007, J Rehabil Res Dev 44(4):561-572).

Direction: R5 routes from each site to every cell, and the time is used
as the cell-to-site time. Routing from the 8,500 sites instead of the
72,766 cells is about 9 times faster (R5 runs single-threaded per origin
here). Checked before adoption (scripts/analysis/r5_direction_symmetry.py,
1,345 cell-site pairs, both directions, same network and window): median
difference 0 min, mean absolute 0.6 min, 98% within 2 min, 96% in the same
DREES decay band. Rule set before the check: adopt if the median
difference is at most 1 min.

Only cells within REACH_LIMIT_M of a chunk's sites are routed to: the
longest trip found within 25 min on a first sample was 12.4 km as the crow
flies (99% under 5.3 km), and the limit is twice that. Sites are grouped
into compact chunks (10 km tiles) so this filter stays tight.

Long-running (hours): sites are processed in chunks, each chunk saved as
soon as it's done, so an interrupted run resumes where it stopped. Several
processes can share the work (env WORKER / WORKERS: worker w takes the
chunks whose global index is w modulo WORKERS). Progress, counted over all
workers, is written to data/interim/access/progress.txt.

Runs in the access Docker image (Dockerfile.access).
"""
import sys

# r5py reads its Java options from the command line; give the JVM most of
# the container's memory before importing it.
import os

sys.argv += ["--max-memory", os.environ.get("R5_MAX_MEMORY", "26G")]

import datetime as dt
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config

ACCESS_DIR = config.DATA_PROCESSED / "access"
WORK_DIR = config.DATA_INTERIM / "access"
TTM_DIR = WORK_DIR / "ttm"
PROGRESS = WORK_DIR / "progress.txt"
CHUNK = 400
REACH_LIMIT_M = 25_000
TILE_M = 10_000
WORKER = int(os.environ.get("WORKER", "0"))
WORKERS = int(os.environ.get("WORKERS", "1"))

REFERENCE_DAY = dt.date(2026, 10, 13)
MORNING = dt.datetime.combine(REFERENCE_DAY, dt.time(10, 0))
EVENING = dt.datetime.combine(REFERENCE_DAY, dt.time(17, 30))
WINDOW = dt.timedelta(minutes=60)
SPEED_MAIN = 4.5
SPEED_REDUCED = 2.8

NETWORKS = {
    "standard": (config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf", config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"),
    "acc_unknown_no": (WORK_DIR / "idf_no_stairs.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_no.zip"),
    "acc_unknown_yes": (WORK_DIR / "idf_no_stairs.osm.pbf", WORK_DIR / "gtfs_accessible_unknown_yes.zip"),
}


@dataclass
class Task:
    name: str
    network: str
    destinations: str  # "gp" or "pharmacy"
    transit: bool
    departure: dt.datetime
    speed: float
    max_minutes: int


TASKS = [
    Task("gp_standard_am", "standard", "gp", True, MORNING, SPEED_MAIN, 25),
    Task("gp_acc_unknown_no_am", "acc_unknown_no", "gp", True, MORNING, SPEED_MAIN, 25),
    Task("gp_acc_unknown_yes_am", "acc_unknown_yes", "gp", True, MORNING, SPEED_MAIN, 25),
    Task("pharmacy_standard_walk", "standard", "pharmacy", False, MORNING, SPEED_MAIN, 20),
    Task("pharmacy_step_free_walk", "acc_unknown_no", "pharmacy", False, MORNING, SPEED_MAIN, 20),
    Task("gp_acc_unknown_no_am_slow", "acc_unknown_no", "gp", True, MORNING, SPEED_REDUCED, 25),
    Task("gp_acc_unknown_yes_am_slow", "acc_unknown_yes", "gp", True, MORNING, SPEED_REDUCED, 25),
    Task("pharmacy_step_free_walk_slow", "acc_unknown_no", "pharmacy", False, MORNING, SPEED_REDUCED, 20),
    Task("gp_standard_pm", "standard", "gp", True, EVENING, SPEED_MAIN, 25),
    Task("gp_acc_unknown_no_pm", "acc_unknown_no", "gp", True, EVENING, SPEED_MAIN, 25),
    Task("gp_acc_unknown_yes_pm", "acc_unknown_yes", "gp", True, EVENING, SPEED_MAIN, 25),
]


def load_points(path: Path, id_col: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)[[id_col, "geometry"]].rename(columns={id_col: "id"})
    return gdf.to_crs(config.CRS_LATLON)


def write_progress(started: float, done_at_start: int, total: int, current: str) -> None:
    """Share done over all workers; time left from the pace since this worker started."""
    done = len(list(TTM_DIR.glob("*.parquet")))
    elapsed = time.time() - started
    eta = ""
    if done > done_at_start:
        remaining = elapsed / (done - done_at_start) * (total - done)
        eta = f" — about {remaining / 60:.0f} min left"
    PROGRESS.write_text(
        f"Access travel times: {100 * done / total:.0f}% ({done}/{total} chunks, {WORKERS} processes){eta}\n"
        f"Worker {WORKER} on: {current}\n"
        f"Updated {dt.datetime.now():%H:%M:%S}\n",
        encoding="utf-8",
    )


def main():
    import gc

    import jpype
    import r5py

    cells = load_points(ACCESS_DIR / "demand_grid_idf.geojson", "cell_id")
    sites = {
        "gp": load_points(ACCESS_DIR / "gp_sites_idf.geojson", "site_id"),
        "pharmacy": load_points(ACCESS_DIR / "pharmacy_sites_idf.geojson", "site_id"),
    }
    cells_xy = cells.to_crs(config.CRS_PROJECTED).geometry
    for key, s in sites.items():
        xy = s.to_crs(config.CRS_PROJECTED).geometry
        tile = (xy.x // TILE_M).astype(int) * 1000 + (xy.y // TILE_M).astype(int)
        sites[key] = s.assign(_tile=tile.values, _x=xy.x.values, _y=xy.y.values).sort_values(["_tile", "_x"])
    jobs = []  # (task, chunk index, site chunk), grouped by network
    for task in sorted(TASKS, key=lambda t: list(NETWORKS).index(t.network)):
        s = sites[task.destinations]
        for k, start in enumerate(range(0, len(s), CHUNK)):
            jobs.append((task, k, s.iloc[start:start + CHUNK]))
    total = len(jobs)
    TTM_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    done_at_start = len(list(TTM_DIR.glob("*.parquet")))
    # One network in memory at a time: a worker's JVM can't hold two
    # Île-de-France networks (OutOfMemoryError at 9 GB), and jobs are
    # ordered by network so each is loaded once per worker.
    network_name, network = None, None

    for index, (task, k, chunk) in enumerate(jobs):
        out = TTM_DIR / f"{task.name}_{k:02d}.parquet"
        if index % WORKERS != WORKER or out.exists():
            continue
        label = f"{task.name}, chunk {k + 1}"
        if task.network != network_name:
            write_progress(started, done_at_start, total, f"loading the '{task.network}' network")
            network = None
            gc.collect()
            jpype.java.lang.System.gc()
            osm, gtfs = NETWORKS[task.network]
            network = r5py.TransportNetwork(str(osm), [str(gtfs)])
            network_name = task.network
        write_progress(started, done_at_start, total, label)
        modes = [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK] if task.transit else [r5py.TransportMode.WALK]
        near = cells_xy.x.between(chunk._x.min() - REACH_LIMIT_M, chunk._x.max() + REACH_LIMIT_M) &             cells_xy.y.between(chunk._y.min() - REACH_LIMIT_M, chunk._y.max() + REACH_LIMIT_M)
        ttm = r5py.TravelTimeMatrix(
            network,
            origins=chunk[["id", "geometry"]],
            destinations=cells[near.values],
            departure=task.departure,
            departure_time_window=WINDOW,
            transport_modes=modes,
            speed_walking=task.speed,
            max_time=dt.timedelta(minutes=task.max_minutes),
            snap_to_network=True,
        )
        ttm = pd.DataFrame(ttm).dropna(subset=["travel_time"])
        ttm = ttm[ttm.travel_time <= task.max_minutes]
        # Stored cell -> site, as used by the E2SFCA (script 32).
        ttm = ttm.rename(columns={"from_id": "to_id", "to_id": "from_id"})[["from_id", "to_id", "travel_time"]]
        ttm.astype({"travel_time": "int16"}).to_parquet(out, index=False)
        write_progress(started, done_at_start, total, label + " done")
        print(f"{label}: {len(ttm)} pairs", flush=True)
    if len(list(TTM_DIR.glob("*.parquet"))) == total:
        PROGRESS.write_text(f"Access travel times: 100% — finished {dt.datetime.now():%Y-%m-%d %H:%M}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
