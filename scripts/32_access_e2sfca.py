"""E2SFCA access indicators per IRIS, from the matrices of script 31.

Enhanced two-step floating catchment area (Luo & Qi 2009, Health & Place
15(4):1100-1107), with the distance decay of the DREES APL:

1. each site j gets a ratio R_j = S_j / sum_i(D_i * W(t_ij)): its capacity
   S_j over the demand of every cell i that can reach it, weighted by
   travel time t_ij;
2. each cell i gets A_i = sum_j(R_j * W(t_ij)): the capacity it can reach,
   net of everyone else who can reach the same sites.

A_i is expressed per 10,000 residents (age-weighted residents for GPs).

Accessible scenario (decision of 2026-10-02, option b): step 1 always uses
the standard network (the competition for a site is what it is: most of
its patients travel without restriction); only step 2 uses the accessible
travel times. So gp_acc_* <= gp_std for every cell, and the
inclusive-mobility gap gp_gap_* = gp_acc_* / gp_std (between 0 and 1) is
the share of reachable GP capacity a resident keeps when travelling
step-free on accessible public transport only.

Decay W(t), t in whole minutes (R5):
- GPs, DREES APL: t < 10: 1; 10 <= t < 15: 2/3; 15 <= t < 20: 1/3; else 0.
  Sensitivity: every bound 5 min lower, then 5 min higher.
- Pharmacies: walking, t < 15: 1, else 0 (everyday local service).
  Sensitivity: 10 and 20 min.

Per IRIS: mean of its cells weighted by residents, cells assigned to the
IRIS that contains their centre. An IRIS that contains no cell centre
(small IRIS) takes the cell whose square contains its representative
point; none at all -> NaN (no residents on the grid).

Indicators written (data/processed/access_e2sfca_iris.csv, MGP IRIS):
- gp_std: GPs, standard network, morning (main);
- gp_acc_no / gp_acc_yes: GPs, accessible travel (unknown stops/trips
  counted as not accessible / accessible), standard competition;
- gp_gap_no / gp_gap_yes: gp_acc_* / gp_std;
- pharmacy_std: pharmacies within 15 min walk;
- the same with suffixes _small / _large (decay bounds -5 / +5 min),
  _slow (reduced walking speed, accessible only), _pm (evening);
- *_q4_flip flags: IRIS whose worst-quartile status changes between the
  -5 and +5 min runs (sensitivity);
- n_cells, pop_grid, pop_imputed_share.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

ACCESS_DIR = config.DATA_PROCESSED / "access"
TTM_DIR = config.DATA_INTERIM / "access" / "ttm"
# Published (tracked in git, read by script 11), unlike the working files in ACCESS_DIR.
OUT_PATH = config.DATA_PROCESSED / "access_e2sfca_iris.csv"
# E2SFCA_NO_CAP=1 (control asked on 2026-10-05): no "accessible no faster
# than standard" rule; output written next to the published file, which is
# left untouched. The number of pairs the rule changes is always printed.
import os  # noqa: E402

NO_CAP = os.environ.get("E2SFCA_NO_CAP") == "1"
if NO_CAP:
    OUT_PATH = config.DATA_INTERIM / "analysis" / "access_e2sfca_iris_nocap.csv"
CAPPED = []
PER = 10_000

GP_DECAY = [(10, 1.0), (15, 2 / 3), (20, 1 / 3)]
PHARMACY_DECAY = [(15, 1.0)]


def shifted(decay, minutes):
    return [(bound + minutes, w) for bound, w in decay]


def weights(t: pd.Series, decay) -> np.ndarray:
    w = np.zeros(len(t))
    for bound, value in reversed(decay):
        w[t.values < bound] = value
    return w


def load_ttm(task: str) -> pd.DataFrame:
    files = sorted(TTM_DIR.glob(f"{task}_[0-9][0-9].parquet"))
    if not files:
        raise FileNotFoundError(f"No travel-time matrix for task {task} in {TTM_DIR}")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def no_faster_than(acc: pd.DataFrame, std: pd.DataFrame) -> pd.DataFrame:
    """An accessible trip can't beat the unrestricted one: R5 returns a
    shorter accessible time for ~1% of pairs (almost all by 1 min), from
    the two networks snapping points slightly differently. Keep the max."""
    m = acc.merge(std, on=["from_id", "to_id"], how="left", suffixes=("", "_std"))
    faster = m.travel_time < m.travel_time_std
    CAPPED.append((len(m), int(faster.sum()), (m.travel_time_std - m.travel_time)[faster].value_counts().sort_index().to_dict()))
    if NO_CAP:
        return m[["from_id", "to_id", "travel_time"]]
    m["travel_time"] = np.fmax(m.travel_time, m.travel_time_std)
    return m[["from_id", "to_id", "travel_time"]]


def site_ratios(ttm: pd.DataFrame, demand: pd.Series, supply: pd.Series, decay) -> pd.Series:
    """Step 1: R_j = S_j / sum_i(D_i W(t_ij))."""
    m = ttm.assign(w=weights(ttm.travel_time, decay))
    m = m[m.w > 0]
    reach = (m.from_id.map(demand).fillna(0) * m.w).groupby(m.to_id).sum()
    return supply.reindex(reach.index) / reach.replace(0, np.nan)


def cell_access(ttm: pd.DataFrame, ratios: pd.Series, decay, cells: pd.Index) -> pd.Series:
    """Step 2: A_i = sum_j(R_j W(t_ij)), per 10,000."""
    m = ttm.assign(w=weights(ttm.travel_time, decay))
    m = m[m.w > 0]
    a = m.to_id.map(ratios).fillna(0) * m.w
    return (a.groupby(m.from_id).sum() * PER).reindex(cells).fillna(0.0)


def cells_to_iris(cells: gpd.GeoDataFrame, iris: gpd.GeoDataFrame):
    """cell_id -> code_iris, plus the fallback cell for IRIS with no centre."""
    joined = gpd.sjoin(cells[["cell_id", "geometry"]], iris[["code_iris", "geometry"]], predicate="within")
    mapping = joined.set_index("cell_id").code_iris
    missing = iris[~iris.code_iris.isin(mapping.values)]
    squares = cells[["cell_id", "geometry"]].copy()
    squares["geometry"] = squares.to_crs("EPSG:3035").buffer(100, cap_style=3).to_crs(cells.crs)
    rep = gpd.GeoDataFrame(missing[["code_iris"]].copy(), geometry=missing.representative_point(), crs=iris.crs)
    extra = gpd.sjoin(rep, squares, predicate="within")[["code_iris", "cell_id"]]
    return mapping, extra


def aggregate(values: pd.DataFrame, cells: pd.DataFrame, mapping: pd.Series, extra: pd.DataFrame) -> pd.DataFrame:
    df = values.join(cells.set_index("cell_id")[["pop", "imputed"]])
    main = df.loc[df.index.intersection(mapping.index)].assign(code_iris=mapping)
    cols = list(values.columns)
    w = main["pop"]
    # Weighted mean over the cells that have a value (unroutable cells are NaN).
    wv = main[cols].notna().mul(w, axis=0)
    agg = main[cols].mul(w, axis=0).groupby(main.code_iris).sum(min_count=1).div(
        wv.groupby(main.code_iris).sum().replace(0, np.nan))
    agg["n_cells"] = main.groupby("code_iris").size()
    agg["pop_grid"] = w.groupby(main.code_iris).sum()
    agg["pop_imputed_share"] = (main["pop"] * main["imputed"]).groupby(main.code_iris).sum() / agg["pop_grid"]
    fb = extra.join(df, on="cell_id").set_index("code_iris")
    fb["n_cells"], fb["pop_grid"], fb["pop_imputed_share"] = 0, 0.0, fb["imputed"].astype(float)
    return pd.concat([agg, fb[cols + ["n_cells", "pop_grid", "pop_imputed_share"]]])


def main():
    cells = gpd.read_file(ACCESS_DIR / "demand_grid_idf.geojson")
    cells["imputed"] = (cells.i_est_200.astype(int) == 1).astype(float)
    gp = gpd.read_file(ACCESS_DIR / "gp_sites_idf.geojson").set_index("site_id").capacity
    ph = gpd.read_file(ACCESS_DIR / "pharmacy_sites_idf.geojson").set_index("site_id").capacity
    ids = pd.Index(cells.cell_id)
    d_gp = cells.set_index("cell_id").pop_gp
    d_ph = cells.set_index("cell_id")["pop"]

    runs = {}
    decays = {"": GP_DECAY, "_small": shifted(GP_DECAY, -5), "_large": shifted(GP_DECAY, +5)}
    for period, std_task in (("", "gp_standard_am"), ("_pm", "gp_standard_pm")):
        std = load_ttm(std_task)
        for sfx, decay in (decays.items() if period == "" else [("", GP_DECAY)]):
            ratios = site_ratios(std, d_gp, gp, decay)
            runs[f"gp_std{sfx}{period}"] = cell_access(std, ratios, decay, ids)
            for v in ("no", "yes"):
                acc = no_faster_than(load_ttm(f"gp_acc_unknown_{v}_{'am' if period == '' else 'pm'}"), std)
                runs[f"gp_acc_{v}{sfx}{period}"] = cell_access(acc, ratios, decay, ids)
            if period == "" and sfx == "":
                for v in ("no", "yes"):  # reduced walking speed, accessible travel only
                    slow = no_faster_than(load_ttm(f"gp_acc_unknown_{v}_am_slow"), std)
                    runs[f"gp_acc_{v}_slow"] = cell_access(slow, ratios, decay, ids)
    ph_ttm = load_ttm("pharmacy_standard_walk")
    for sfx, decay in {"": PHARMACY_DECAY, "_small": shifted(PHARMACY_DECAY, -5), "_large": shifted(PHARMACY_DECAY, +5)}.items():
        runs[f"pharmacy_std{sfx}"] = cell_access(ph_ttm, site_ratios(ph_ttm, d_ph, ph, decay), decay, ids)
    values = pd.DataFrame(runs)
    # A cell that reaches no GP site and no pharmacy at all is a routing
    # failure, not an absence of services (in the MGP: 23 cells, 4,146
    # residents, e.g. Courbevoie "Dominos" on the La Défense deck, whose
    # point snaps to a street piece cut off from the network). NaN, not 0.
    # Rural cells outside the MGP that reach nothing within the time limit
    # get NaN too, which changes nothing for the MGP: they add no demand to
    # any site either way.
    reached = set(load_ttm("gp_standard_am").from_id) | set(ph_ttm.from_id)
    unroutable = ~values.index.isin(reached)
    values.loc[unroutable] = np.nan
    print(f"Unroutable cells (no GP and no pharmacy reached): {unroutable.sum()}")
    n, k = CAPPED[0][0], CAPPED[0][1]
    print(f"'Accessible no faster than standard' rule, main run (GPs, morning, unknown = no): {k:,} of {n:,} cell-site pairs "
          f"({100 * k / n:.2f}%), by minutes: {CAPPED[0][2]}; {'NOT applied' if NO_CAP else 'applied'}")
    k2, n2 = CAPPED[1][1], CAPPED[1][0]
    print(f"  unknown = yes: {k2:,} of {n2:,} ({100 * k2 / n2:.2f}%)")

    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(cells.crs)
    mapping, extra = cells_to_iris(cells, iris)
    out = aggregate(values, cells, mapping, extra).reindex(iris.code_iris)
    out.index.name = "code_iris"
    for v in ("no", "yes"):
        for sfx, base in (("", "gp_std"), ("_small", "gp_std_small"), ("_large", "gp_std_large"), ("_pm", "gp_std_pm"), ("_slow", "gp_std")):
            out[f"gp_gap_{v}{sfx}"] = out[f"gp_acc_{v}{sfx}"] / out[base].replace(0, np.nan)
    # Sensitivity: worst-quartile status (lowest values) under -5 / +5 min bounds.
    for base in ("gp_std", "pharmacy_std", "gp_gap_no", "gp_gap_yes"):
        q_small = out[base + "_small"] <= out[base + "_small"].quantile(0.25)
        q_large = out[base + "_large"] <= out[base + "_large"].quantile(0.25)
        out[base + "_q4_flip"] = (q_small != q_large) & out[base].notna()
    ACCESS_DIR.mkdir(parents=True, exist_ok=True)
    out.reset_index().to_csv(OUT_PATH, index=False)
    print(f"Saved {len(out)} IRIS to {OUT_PATH}; {out.gp_std.isna().sum()} without grid residents")


if __name__ == "__main__":
    main()
