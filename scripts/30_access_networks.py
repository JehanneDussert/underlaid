"""Street and transit networks for the access computation (script 31).

Builds three network variants from the same sources:
- standard: the Geofabrik OpenStreetMap extract for Île-de-France and the
  full Île-de-France Mobilités GTFS;
- accessible, "unknown = not accessible": stairs removed from the walking
  network (see below); transit restricted to stops and trips marked
  accessible in the GTFS (wheelchair_boarding = 1 at the stop, inherited
  from the parent station when the stop says 0, and wheelchair_accessible
  = 1 for the trip). Stops and trips marked unknown (0 or blank) are
  treated as not accessible;
- accessible, "unknown = accessible": same, but unknown stops and trips
  are kept. A conclusion on the working hypothesis only stands if it
  holds in both (decision of 2026-10-01, CLAUDE.md).

Stairs: OSM highway=steps ways are removed. OSM steps are mapped unevenly
(share of IGN BD TOPO staircase length also found in OSM: 75: 93%, 92:
75%, 93: 65%, 94: 76%; scripts/analysis/osm_steps_completeness.py), so
OSM pedestrian ways that run along a BD TOPO staircase missing from OSM
are removed too: a BD TOPO "Escalier" segment not within 15 m of OSM steps,
covered at >= 50% of its length by the 10 m buffer of an OSM pedestrian
way no longer than MAX_DROPPED_WAY_M, removes that way. Longer ways are
kept (dropping them would cut off long paths for one short staircase) and
counted.

GTFS: Île-de-France Mobilités, "Horaires prévus sur les lignes de
transport en commun d'Île-de-France (GTFS Datahub)", Licence Mobilités.
It covers the next 30 days only, so the reference day is chosen per run
(see REFERENCE_DAY in script 31) and the downloaded file is kept in
data/raw for reproducibility. The filtered feeds are working files
(data/interim), never published.

Runs in the access Docker image (Dockerfile.access): needs osmium.
"""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
import pyogrio
import requests

import config
from utils.download import download_file

RAW_GTFS = config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"
RAW_PBF = config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"
OUT_DIR = config.DATA_INTERIM / "access"
WFS_URL = "https://data.geopf.fr/wfs/ows"
PEDESTRIAN_WAYS = ("footway", "path", "pedestrian", "corridor", "cycleway", "track", "bridleway")
STEPS_MATCH_M = 15
WAY_BUFFER_M = 10
MIN_STAIR_COVERAGE = 0.5
MAX_DROPPED_WAY_M = 200


# --- GTFS -----------------------------------------------------------------

def stop_accessibility(stops: pd.DataFrame) -> pd.Series:
    """1 yes, 2 no, 0 unknown, per stop_id, children inheriting from their
    parent station when they say 0/blank (GTFS reference)."""
    wb = stops.set_index("stop_id")["wheelchair_boarding"].fillna("0").replace("", "0")
    parent = stops.set_index("stop_id")["parent_station"].fillna("")
    inherited = parent.map(wb).fillna("0")
    return wb.where(wb != "0", inherited)


def filter_gtfs(src: Path, dest: Path, keep_unknown: bool) -> dict:
    keep_values = {"1", "0"} if keep_unknown else {"1"}
    with zipfile.ZipFile(src) as z:
        stops = pd.read_csv(z.open("stops.txt"), dtype=str)
        trips = pd.read_csv(z.open("trips.txt"), dtype=str)
        stop_ok = stop_accessibility(stops)
        trips["wheelchair_accessible"] = trips["wheelchair_accessible"].fillna("0").replace("", "0")
        kept_trips = set(trips.loc[trips.wheelchair_accessible.isin(keep_values), "trip_id"])
        kept_stops = set(stop_ok[stop_ok.isin(keep_values)].index)
        st = pd.read_csv(z.open("stop_times.txt"), dtype=str)
        n_before = len(st)
        st = st[st.trip_id.isin(kept_trips) & st.stop_id.isin(kept_stops)]
        # A trip needs at least two stops left to carry anyone.
        sizes = st.groupby("trip_id").size()
        st = st[st.trip_id.isin(sizes[sizes >= 2].index)]
        trips_out = trips[trips.trip_id.isin(st.trip_id.unique())]
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as out:
            for name in z.namelist():
                if name == "stop_times.txt":
                    out.writestr(name, st.to_csv(index=False))
                elif name == "trips.txt":
                    out.writestr(name, trips_out.to_csv(index=False))
                elif name in ("pathways.txt", "object_codes_extension.txt", "ticketing_deep_links.txt", "booking_rules.txt"):
                    continue  # not used by R5; pathways reference stops that may be gone
                else:
                    out.writestr(name, z.read(name))
    return {"feed": dest.name, "stop_times_kept_%": round(100 * len(st) / n_before, 1),
            "trips_kept": len(trips_out), "trips_total": len(trips)}


# --- Stairs -----------------------------------------------------------------

def fetch_bdtopo_stairs(bbox) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = bbox
    frames, start = [], 0
    while True:
        r = requests.get(WFS_URL, timeout=120, params={
            "service": "WFS", "version": "2.0.0", "request": "GetFeature",
            "typeNames": "BDTOPO_V3:troncon_de_route", "outputFormat": "application/json",
            "srsName": "EPSG:4326", "count": 5000, "startIndex": start,
            "CQL_FILTER": f"nature='Escalier' AND BBOX(geometrie,{minx},{miny},{maxx},{maxy},'EPSG:4326')",
        })
        r.raise_for_status()
        feats = r.json()["features"]
        if not feats:
            break
        frames.append(gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326"))
        if len(feats) < 5000:
            break
        start += 5000
    return pd.concat(frames, ignore_index=True)


def stair_way_ids() -> tuple[set[int], dict]:
    """OSM way ids to drop from the accessible walking network."""
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_LATLON)
    minx, miny, maxx, maxy = iris.total_bounds
    bbox = (minx - 0.25, miny - 0.2, maxx + 0.25, maxy + 0.2)  # MGP plus the walking reach of the buffer zone
    where = "highway IN (" + ",".join(f"'{h}'" for h in ("steps", *PEDESTRIAN_WAYS)) + ")"
    ways = pyogrio.read_dataframe(RAW_PBF, layer="lines", where=where, bbox=bbox).to_crs(config.CRS_PROJECTED)
    ways["osm_id"] = ways["osm_id"].astype("int64")
    steps = ways[ways.highway == "steps"]
    paths = ways[ways.highway != "steps"].copy()
    stairs = fetch_bdtopo_stairs(bbox).to_crs(config.CRS_PROJECTED)
    stairs = stairs[~stairs.intersects(steps.buffer(STEPS_MATCH_M).union_all())].reset_index(drop=True)
    stairs["sid"] = stairs.index
    stairs["slen"] = stairs.length
    paths["plen"] = paths.length
    buf = paths[["osm_id", "plen", "geometry"]].copy()
    buf["geometry"] = buf.buffer(WAY_BUFFER_M)
    pairs = gpd.overlay(stairs[["sid", "slen", "geometry"]], buf, how="intersection", keep_geom_type=True)
    pairs["cov"] = pairs.length / pairs.slen
    hit = pairs[pairs["cov"] >= MIN_STAIR_COVERAGE]
    dropped = hit[hit.plen <= MAX_DROPPED_WAY_M]
    stats = {
        "osm_steps_ways": len(steps),
        "bdtopo_stairs_missing_in_osm": len(stairs),
        "bdtopo_stairs_matched_to_a_path": hit.sid.nunique(),
        "paths_dropped": dropped.osm_id.nunique(),
        "paths_kept_too_long": hit.loc[hit.plen > MAX_DROPPED_WAY_M, "osm_id"].nunique(),
    }
    return set(steps.osm_id) | set(dropped.osm_id), stats


def write_pbf_without(way_ids: set[int], dest: Path) -> None:
    import osmium

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with osmium.SimpleWriter(str(dest)) as writer:
        for obj in osmium.FileProcessor(str(RAW_PBF)):
            if obj.is_way() and obj.id in way_ids:
                continue
            writer.add(obj)


def main():
    download_file(config.IDFM_GTFS_URL, RAW_GTFS)
    download_file(config.OSM_IDF_PBF_URL, RAW_PBF)
    for keep_unknown, name in ((False, "gtfs_accessible_unknown_no.zip"), (True, "gtfs_accessible_unknown_yes.zip")):
        print(filter_gtfs(RAW_GTFS, OUT_DIR / name, keep_unknown))
    ids, stats = stair_way_ids()
    print("Stairs:", stats)
    write_pbf_without(ids, OUT_DIR / "idf_no_stairs.osm.pbf")
    print(f"Wrote {OUT_DIR / 'idf_no_stairs.osm.pbf'} ({len(ids)} ways removed)")


if __name__ == "__main__":
    main()
