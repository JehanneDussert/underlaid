"""Neighbourhood-level travel times to key destinations (routes page).

Pre-registered on 2026-10-02 (CLAUDE.md, "Hypothèse de travail", routes
pre-registration and addendum). Reads the per-cell nearest-destination
times of script 34 and summarises them per IRIS:

- value of a neighbourhood = population-weighted median of its inhabited
  200 m cells (Filosofi 2021 population);
- a cell that does not reach a destination type within 90 min counts as
  +inf (never as 0, never dropped); if more than half of the population
  does not reach it, the neighbourhood is "more than 90 min" (null in the
  output, flagged in `over90`);
- imposed detour = step-free time minus standard time, computed per cell
  then summarised the same way (cell reached without constraint but not
  step-free: +inf), for each of the two step-free variants;
- stations: walking only, one value per profile (no time slot).

Outputs (data/processed/): routes_iris_<slot>.json, one per time slot,
and routes_stations_iris.json — compact arrays per IRIS (layout given in
each file), small enough to load on demand on the page.
Prints the completeness of the run (missing chunks) and refuses to write
partial outputs unless ROUTES_ALLOW_PARTIAL=1 (used for testing only).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

ACCESS_DIR = config.DATA_PROCESSED / "access"
MAX_MINUTES = 90
PROFILES = ["standard", "slow", "step_free_no", "step_free_yes"]
# ROUTES_SET=neighbourhood: the second run (everyday places of the
# "Votre quartier" page, script 37; Tuesday 10:00 only, no stations), as in
# script 34. Outputs routes_neighbourhood_tue10.json.
ROUTES_SET = os.environ.get("ROUTES_SET", "key")
if ROUTES_SET == "neighbourhood":
    TTM_DIR = config.DATA_INTERIM / "access" / "routes_ttm_neighbourhood"
    SLOTS = ["tue10"]
    TYPES = ["creche", "food_store", "nursery_school", "police", "social_centre", "library", "park"]
    N_CHUNKS = 92  # 13,752 cells / 150
    OUT_PREFIX = "routes_neighbourhood"
elif ROUTES_SET == "paris":
    # Public toilets and drinking fountains, Paris only (script 41): origins
    # are the Paris cells, so only Paris neighbourhoods get a value.
    TTM_DIR = config.DATA_INTERIM / "access" / "routes_ttm_paris"
    SLOTS = ["tue10"]
    TYPES = ["toilets", "toilets_pmr", "toilets_24h", "drinking_water"]
    N_CHUNKS = 7  # 2,034 Paris cells / 300
    OUT_PREFIX = "routes_paris"
else:
    TTM_DIR = config.DATA_INTERIM / "access" / "routes_ttm"
    SLOTS = ["tue10", "tue21", "tue01", "sun10"]
    TYPES = ["emergency", "gp", "pharmacy", "town_hall", "france_services", "caf", "cpam", "employment", "post_office"]
    N_CHUNKS = 46  # 13,752 cells / 300
    OUT_PREFIX = "routes_iris"

# ROUTES_VERSION=2 (second calculation, pre-registered on 2026-10-04): reads
# the *_v2 folders of script 34 and writes *_v2 outputs next to the
# published ones (nothing published is overwritten); the neighbourhood set
# gains the schools; the sensitivity runs (wheelchair at 0.5 and 1.0 m/s,
# slope threshold 6 %; Tuesday 10:00 and stations) go to
# <prefix>_sensitivity_v2.json.
VERSION = os.environ.get("ROUTES_VERSION", "1")
SENSITIVITY = ["sens_speed05", "sens_speed10", "sens_slope6"]
STATIONS_OUT = "routes_stations_iris.json"
if VERSION == "2":
    TTM_DIR = TTM_DIR.with_name(TTM_DIR.name + "_v2")
    OUT_PREFIX += "_v2"
    STATIONS_OUT = "routes_stations_iris_v2.json"
    if ROUTES_SET == "neighbourhood":
        TYPES = TYPES + ["elementary_public", "elementary_private", "college_public", "college_private", "lycee_public", "lycee_private"]


def cells_by_iris() -> pd.DataFrame:
    """Inhabited cells per IRIS. Same rule as script 32: an IRIS that
    contains no cell centre (small IRIS) takes the cell whose 200 m square
    contains its representative point (that cell is an origin of script 34
    already, through the IRIS that contains its centre)."""
    cells = gpd.read_file(ACCESS_DIR / "demand_grid_idf.geojson")[["cell_id", "pop", "geometry"]]
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(cells.crs)
    inside = gpd.sjoin(cells, iris, predicate="within", how="inner")
    inside = inside[inside["pop"] > 0].drop_duplicates("cell_id")
    main = inside[["cell_id", "code_iris", "pop"]]
    missing = iris[~iris.code_iris.isin(main.code_iris)]
    squares = main.merge(cells[["cell_id", "geometry"]], on="cell_id")
    squares = gpd.GeoDataFrame(squares, geometry="geometry", crs=cells.crs)
    squares["geometry"] = squares.to_crs("EPSG:3035").buffer(100, cap_style=3).to_crs(cells.crs)
    rep = gpd.GeoDataFrame(missing[["code_iris"]].copy(), geometry=missing.representative_point(), crs=iris.crs)
    extra = gpd.sjoin(rep, squares[["cell_id", "pop", "geometry"]], predicate="within")[["cell_id", "code_iris", "pop"]]
    return pd.concat([main, extra], ignore_index=True)


def load_task(name: str) -> pd.DataFrame | None:
    files = sorted(TTM_DIR.glob(f"{name}_*.parquet"))
    if len(files) < N_CHUNKS and os.environ.get("ROUTES_ALLOW_PARTIAL") != "1":
        return None
    if not files:
        return None
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Population-weighted median; values may contain +inf."""
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = np.cumsum(w)
    return float(v[np.searchsorted(cum, cum[-1] / 2)])


def summarise(times: pd.DataFrame, cells: pd.DataFrame, types: list[str]) -> dict:
    """times: cell_id, type, minutes (reached only). Returns {iris: {type: minutes|None}}."""
    out = {}
    wide = times.pivot_table(index="cell_id", columns="type", values="minutes", aggfunc="min")
    grid = cells.set_index("cell_id").join(wide, how="left")
    for code, g in grid.groupby("code_iris"):
        row = {}
        for t in types:
            vals = g[t].to_numpy(dtype=float) if t in g else np.full(len(g), np.inf)
            vals = np.where(np.isnan(vals), np.inf, vals)
            m = weighted_median(vals, g["pop"].to_numpy(dtype=float))
            row[t] = None if not np.isfinite(m) else int(round(m))
        out[code] = row
    return out


def detour(acc: pd.DataFrame, std: pd.DataFrame, cells: pd.DataFrame, types: list[str]) -> dict:
    a = acc.pivot_table(index="cell_id", columns="type", values="minutes", aggfunc="min")
    s = std.pivot_table(index="cell_id", columns="type", values="minutes", aggfunc="min")
    grid = cells.set_index("cell_id")
    out = {}
    for code, g in grid.groupby("code_iris"):
        row = {}
        for t in types:
            sv = s[t].reindex(g.index).to_numpy(dtype=float) if t in s else np.full(len(g), np.nan)
            av = a[t].reindex(g.index).to_numpy(dtype=float) if t in a else np.full(len(g), np.nan)
            reached = ~np.isnan(sv)  # detour defined where the standard trip reaches it
            if not reached.any():
                row[t] = None
                continue
            d = np.where(np.isnan(av[reached]), np.inf, av[reached] - sv[reached])
            m = weighted_median(d, g["pop"].to_numpy(dtype=float)[reached])
            row[t] = None if not np.isfinite(m) else int(round(m))
        out[code] = row
    return out


def main():
    cells = cells_by_iris()
    missing = []
    for slot in SLOTS:
        data = {p: load_task(f"{p}_{slot}") for p in PROFILES}
        absent = [p for p, d in data.items() if d is None]
        if absent:
            missing += [f"{p}_{slot}" for p in absent]
            continue
        # Compact layout: per IRIS, one flat list of 6 x 9 values (minutes,
        # null = more than 90 min / not reached): times for the 4 profiles,
        # then the imposed detour for the 2 step-free variants, each block
        # in TYPES order. Keeps a slot file around 0.4 MB.
        blocks = [summarise(data[p], cells, TYPES) for p in PROFILES]
        blocks += [detour(data[v], data["standard"], cells, TYPES) for v in ("step_free_no", "step_free_yes")]
        result = {code: [b[code][t] for b in blocks for t in TYPES] for code in sorted(cells.code_iris.unique())}
        layout = {"blocks": [f"time:{p}" for p in PROFILES] + ["detour:step_free_no", "detour:step_free_yes"], "types": TYPES}
        out = config.DATA_PROCESSED / f"{OUT_PREFIX}_{slot}.json"
        out.write_text(json.dumps({"slot": slot, "max_minutes": MAX_MINUTES, "layout": layout, "iris": result}, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {out.name} ({out.stat().st_size / 1e6:.2f} MB, {len(result)} IRIS)")

    if VERSION == "2":
        sens = {p: load_task(f"{p}_tue10") for p in ["step_free_no"] + SENSITIVITY}
        absent = [p for p, d in sens.items() if d is None]
        if absent:
            missing += [f"{p}_tue10" for p in absent]
        else:
            blocks = [summarise(sens[p], cells, TYPES) for p in sens]
            result = {code: [b[code][t] for b in blocks for t in TYPES] for code in sorted(cells.code_iris.unique())}
            out = config.DATA_PROCESSED / f"{OUT_PREFIX.replace('_v2', '')}_sensitivity_v2.json"
            out.write_text(json.dumps({"slot": "tue10", "max_minutes": MAX_MINUTES, "layout": {"blocks": [f"time:{p}" for p in sens], "types": TYPES},
                                       "iris": result}, separators=(",", ":")), encoding="utf-8")
            print(f"wrote {out.name}")
    if ROUTES_SET in ("neighbourhood", "paris"):
        if missing:
            print(f"incomplete tasks (not written): {', '.join(missing)}")
        return
    stations = {p: load_task(f"{p}_stations_walk") for p in PROFILES}
    absent = [p for p, d in stations.items() if d is None]
    if absent:
        missing += [f"{p}_stations_walk" for p in absent]
    else:
        per_profile = [summarise(stations[p], cells, ["station"]) for p in PROFILES]
        result = {code: [b[code]["station"] for b in per_profile] for code in sorted(cells.code_iris.unique())}
        out = config.DATA_PROCESSED / STATIONS_OUT
        out.write_text(json.dumps({"max_minutes": MAX_MINUTES, "profiles": PROFILES, "iris": result}, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {out.name}")
    if missing:
        print(f"incomplete tasks (not written): {', '.join(missing)}")


if __name__ == "__main__":
    main()
