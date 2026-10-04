"""Remaining inversions after the common attachment points (pilot run,
4 October 2026): street network or public transport?

For the pilot cells where step-free is still faster, recompute walking only
(no transit) from the common attachment points (script 42) to the same
destinations, on the standard and on the no-stairs street networks. If
walking alone shows no inversion, the remaining ones come from the transit
part (filtered GTFS). Changes nothing; writes
data/interim/analysis/pilot_residual.txt.
"""
import datetime as dt
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

AI = config.DATA_INTERIM / "access"
AP = config.DATA_PROCESSED / "access"
OUT = config.DATA_INTERIM / "analysis" / "pilot_residual.txt"


def load(d, t):
    return pd.concat([pd.read_parquet(f) for f in sorted((AI / d).glob(f"{t}_[0-9][0-9].parquet"))], ignore_index=True)


def main():
    import r5py

    m = load("routes_ttm_neighbourhood_pilot", "standard_tue10").merge(
        load("routes_ttm_neighbourhood_pilot", "step_free_no_tue10"), on=["cell_id", "type"], suffixes=("_s", "_f"))
    inv = m[m.minutes_f < m.minutes_s]
    sp = pd.read_csv(AP / "snapped_points.csv", dtype={"id": str})
    o = sp[sp["set"] == "origin"].set_index("id")
    cells = inv.cell_id.astype(str).unique()
    og = gpd.GeoDataFrame({"id": cells}, geometry=gpd.points_from_xy(o.loc[cells, "lon"], o.loc[cells, "lat"]), crs=config.CRS_LATLON)
    dest = gpd.read_file(AP / "neighbourhood_destinations_idf.geojson")
    dest = dest[dest["type"].isin(inv["type"].unique())]
    d = sp[sp["set"] == "neighbourhood"].set_index("id")
    ids = dest["dest_id"].astype(str)
    dg = gpd.GeoDataFrame({"id": ids.to_numpy(), "type": dest["type"].to_numpy()},
                          geometry=gpd.points_from_xy(d.loc[ids, "lon"], d.loc[ids, "lat"]), crs=config.CRS_LATLON)

    res = {}
    for key, osm in [("s", config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), ("f", AI / "idf_no_stairs.osm.pbf")]:
        net = r5py.TransportNetwork(str(osm), [])
        t = pd.DataFrame(r5py.TravelTimeMatrix(net, origins=og, destinations=dg[["id", "geometry"]], transport_modes=[r5py.TransportMode.WALK],
                                               speed_walking=4.5, max_time=dt.timedelta(minutes=90), snap_to_network=True,
                                               departure=dt.datetime(2026, 10, 13, 10, 0))).dropna(subset=["travel_time"])
        t["type"] = t["to_id"].map(dg.set_index("id")["type"])
        res[key] = t.groupby(["from_id", "type"])["travel_time"].min()
        del net
    w = pd.DataFrame(res).dropna()
    w["inv"] = w.f < w.s
    j = inv.assign(cell_id=inv.cell_id.astype(str)).merge(w.reset_index().rename(columns={"from_id": "cell_id"}), on=["cell_id", "type"], how="left")
    lines = [
        "Pilot: remaining step-free < standard pairs, recomputed walking only from the common points", "=" * 80,
        f"remaining pairs (transit run): {len(inv):,} in {len(cells)} cells",
        f"walking only, same pairs: step-free faster in {int(j.inv.sum())} of {int(j.inv.notna().sum())} "
        f"({100 * j.inv.mean():.1f}%)",
        f"walking only reproduces the published standard time (±1 min): {100 * ((j.s - j.minutes_s).abs() <= 1).mean():.0f}% of pairs",
        f"transit run shorter than walking alone (standard): {100 * (j.minutes_s < j.s - 1).mean():.0f}% of pairs",
        f"transit run shorter than walking alone (step-free): {100 * (j.minutes_f < j.f - 1).mean():.0f}% of pairs",
        "",
        "by type: " + ", ".join(f"{k} {v:.0%}" for k, v in j.groupby('type').inv.mean().items()),
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
