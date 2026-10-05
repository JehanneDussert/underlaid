"""Option (a), 5 October 2026: are the remaining "step-free faster" pairs
(second pilot, 198 pairs, mostly 1 min) a matter of rounding or of the
median over the departure window?

For each remaining pair, travel times departure by departure (each minute
from 10:00 to 10:59, a 1-minute window each), on the standard and on the
accessible networks, same common points, no re-snapping (as in the second
pilot). If, departure by departure, step-free is never faster than
standard, the inversion comes from taking the median over the hour (two
different distributions); if step-free is faster for some departures, the
networks themselves allow it. Changes nothing; writes
data/interim/analysis/departure_by_departure.txt.
"""
import datetime as dt
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

AI = config.DATA_INTERIM / "access"
AP = config.DATA_PROCESSED / "access"
OUT = config.DATA_INTERIM / "analysis" / "departure_by_departure.txt"
NETS = {
    "std": (config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf", config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"),
    "sf": (AI / "idf_no_stairs.osm.pbf", AI / "gtfs_accessible_unknown_no.zip"),
}


def load(d, t):
    return pd.concat([pd.read_parquet(f) for f in sorted((AI / d).glob(f"{t}_[0-9][0-9].parquet"))], ignore_index=True)


def main():
    import r5py

    m = load("routes_ttm_neighbourhood_pilot2", "standard_tue10").merge(
        load("routes_ttm_neighbourhood_pilot2", "step_free_no_tue10"), on=["cell_id", "type"], suffixes=("_s", "_f"))
    inv = m[m.minutes_f < m.minutes_s].copy()
    inv["cell_id"] = inv.cell_id.astype(str)
    sp = pd.read_csv(AP / "snapped_points.csv", dtype={"id": str})
    o = sp[sp["set"] == "origin"].set_index("id")
    cells = inv.cell_id.unique()
    og = gpd.GeoDataFrame({"id": cells}, geometry=gpd.points_from_xy(o.loc[cells, "lon"], o.loc[cells, "lat"]), crs=config.CRS_LATLON)
    dest = gpd.read_file(AP / "neighbourhood_destinations_idf.geojson")
    dest = dest[dest["type"].isin(inv["type"].unique())]
    d = sp[sp["set"] == "neighbourhood"].set_index("id")
    ids = dest["dest_id"].astype(str).to_numpy()
    dg = gpd.GeoDataFrame({"id": ids}, geometry=gpd.points_from_xy(d.loc[ids, "lon"], d.loc[ids, "lat"]), crs=config.CRS_LATLON)
    dtype = dest.assign(dest_id=dest.dest_id.astype(str)).set_index("dest_id")["type"]

    per = {}
    for key, (osm, gtfs) in NETS.items():
        net = r5py.TransportNetwork(str(osm), [str(gtfs)])
        rows = []
        for minute in range(60):
            dep = dt.datetime(2026, 10, 13, 10, minute)
            t = pd.DataFrame(r5py.TravelTimeMatrix(net, origins=og, destinations=dg, departure=dep,
                                                   departure_time_window=dt.timedelta(minutes=1),
                                                   transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
                                                   speed_walking=4.5, max_time=dt.timedelta(minutes=90), snap_to_network=False))
            t = t.dropna(subset=["travel_time"])
            t["type"] = t["to_id"].map(dtype)
            b = t.groupby(["from_id", "type"], as_index=False)["travel_time"].min()
            b["minute"] = minute
            rows.append(b)
        per[key] = pd.concat(rows)
        del net
    j = per["std"].merge(per["sf"], on=["from_id", "type", "minute"], suffixes=("_s", "_f"), how="outer")
    j = j.merge(inv[["cell_id", "type", "minutes_s", "minutes_f"]].rename(columns={"cell_id": "from_id"}), on=["from_id", "type"])
    j["faster"] = j.travel_time_f < j.travel_time_s
    pair = j.groupby(["from_id", "type"]).agg(dep_faster=("faster", "sum"), n=("minute", "size"),
                                                med_s=("travel_time_s", "median"), med_f=("travel_time_f", "median"),
                                                pub_s=("minutes_s", "first"), pub_f=("minutes_f", "first"))
    never = (pair.dep_faster == 0).sum()
    lines = [
        "Remaining pairs, departure by departure (10:00-10:59, one per minute)", "=" * 70,
        f"pairs: {len(pair)}",
        f"step-free never faster at any departure: {never} ({100 * never / len(pair):.0f}%) -> inversion from the median over the hour",
        f"step-free faster at least once: {len(pair) - never}; of which at more than half of the departures: {(pair.dep_faster > 30).sum()}",
        f"medians recomputed from the 60 departures reproduce the published values: standard {100 * (pair.med_s == pair.pub_s).mean():.0f}%, "
        f"step-free {100 * (pair.med_f == pair.pub_f).mean():.0f}%",
        f"by published gap: " + ", ".join(f"{g} min: {int(v)} pairs, never faster {int(w)}" for g, (v, w) in
                                           pair.assign(g=pair.pub_s - pair.pub_f).groupby("g").agg(v=("n", "size"), w=("dep_faster", lambda s: (s == 0).sum())).iterrows()),
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
