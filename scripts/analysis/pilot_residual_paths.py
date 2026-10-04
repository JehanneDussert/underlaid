"""Remaining inversions, walking only: detailed paths of the worst pairs on
both street networks (4 October 2026). For each pair, the walking
itinerary from the common origin point to the nearest destination of the
type, on the standard and on the no-stairs network: duration, distance,
and the OSM ways used at both ends. Changes nothing; writes
data/interim/analysis/pilot_residual_paths.txt.
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
OUT = config.DATA_INTERIM / "analysis" / "pilot_residual_paths.txt"
N = 4


def main():
    import r5py

    sp = pd.read_csv(AP / "snapped_points.csv", dtype={"id": str})
    o = sp[sp["set"] == "origin"].set_index("id")
    d = sp[sp["set"] == "neighbourhood"].set_index("id")
    dest = gpd.read_file(AP / "neighbourhood_destinations_idf.geojson")
    dest["dest_id"] = dest["dest_id"].astype(str)

    def ttm(net, origins, dests):
        t = pd.DataFrame(r5py.TravelTimeMatrix(net, origins=origins, destinations=dests, transport_modes=[r5py.TransportMode.WALK],
                                               speed_walking=4.5, max_time=dt.timedelta(minutes=60), snap_to_network=True,
                                               departure=dt.datetime(2026, 10, 13, 10, 0)))
        return t.dropna(subset=["travel_time"])

    # Candidate pairs: walking-only inversions on nursery schools / food stores (short walks).
    m = pd.concat([pd.read_parquet(f) for f in (AI / "routes_ttm_neighbourhood_pilot").glob("standard_tue10_*.parquet")]).merge(
        pd.concat([pd.read_parquet(f) for f in (AI / "routes_ttm_neighbourhood_pilot").glob("step_free_no_tue10_*.parquet")]),
        on=["cell_id", "type"], suffixes=("_s", "_f"))
    m = m[(m.minutes_f < m.minutes_s) & m.type.isin(["nursery_school", "food_store", "park", "creche", "elementary_public"])]
    m = m.assign(gap=m.minutes_s - m.minutes_f).sort_values("gap", ascending=False).head(N)

    nets = {"std": r5py.TransportNetwork(str(config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), []),
            "sf": r5py.TransportNetwork(str(AI / "idf_no_stairs.osm.pbf"), [])}
    lines = ["Worst remaining pairs, walking only, detailed paths", "=" * 70]
    for _, p in m.iterrows():
        cid = str(p.cell_id)
        og = gpd.GeoDataFrame({"id": [cid]}, geometry=gpd.points_from_xy([o.loc[cid, "lon"]], [o.loc[cid, "lat"]]), crs=config.CRS_LATLON)
        cand = dest[dest["type"] == p.type]
        ids = cand["dest_id"].to_numpy()
        dg = gpd.GeoDataFrame({"id": ids}, geometry=gpd.points_from_xy(d.loc[ids, "lon"], d.loc[ids, "lat"]), crs=config.CRS_LATLON)
        lines.append(f"\ncell {cid} -> {p.type}: transit run std {p.minutes_s} / step-free {p.minutes_f}")
        best = {}
        for k, net in nets.items():
            t = ttm(net, og, dg)
            r = t.sort_values("travel_time").iloc[0]
            best[k] = r
            lines.append(f"  {k}: walking {r.travel_time:.0f} min to destination {r.to_id}")
        for k, net in nets.items():
            to = best[k].to_id
            di = r5py.DetailedItineraries(net, origins=og, destinations=dg[dg.id == to], transport_modes=[r5py.TransportMode.WALK],
                                          speed_walking=4.5, departure=dt.datetime(2026, 10, 13, 10, 0), snap_to_network=True)
            g = gpd.GeoDataFrame(pd.DataFrame(di), geometry="geometry", crs=config.CRS_LATLON)
            if len(g):
                length = g.to_crs(config.CRS_PROJECTED).length.sum()
                lines.append(f"  {k} path to {to}: {g.travel_time.sum()} , {length:.0f} m, "
                             f"start {list(g.geometry.iloc[0].coords)[0]}, end {list(g.geometry.iloc[-1].coords)[-1]}")
        lines.append(f"  origin point {o.loc[cid, 'lon']:.6f},{o.loc[cid, 'lat']:.6f} (tier {o.loc[cid, 'tier']}, moved {o.loc[cid, 'moved_m']:.0f} m)")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
