"""Descriptive decomposition of wheelchair travel times (pre-registered on
2026-10-07 at 07:28, docs/checks/2026-10-07-wheelchair-time-decomposition-
preregistration.md). No verdict, nothing published.

Per cell x place pair (Tuesday 10:00, key places and everyday places):
1. "entirely on foot" when the combined time (walk and public transport,
   published second run) is not shorter than walking alone at the same pace;
   population-weighted share by way of getting around, place and département;
2. total = wheelchair - without constraint; speed and slopes = wheelchair
   with every stop - without constraint; inaccessible stops = wheelchair -
   wheelchair with every stop (the two parts add up to the total). Pairs not
   reached in one of the runs are counted apart. Complement: walking alone
   at 0.8 m/s on the slope network - walking alone at 4.5 km/h.
Writes data/interim/analysis/wheelchair_decomposition.txt.
"""
import importlib
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ROUTES_VERSION", "2")
import config  # noqa: E402

A = config.DATA_INTERIM / "access"
OUT = config.DATA_INTERIM / "analysis" / "wheelchair_decomposition.txt"
SETS = {"key": ("routes_ttm", 46), "neighbourhood": ("routes_ttm_neighbourhood", 92)}
MODES = {"standard": "sans contrainte", "slow": "marche lente", "step_free_no": "fauteuil roulant"}
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def load(folder: str, task: str, n: int) -> pd.DataFrame:
    files = sorted((A / folder).glob(f"{task}_[0-9][0-9].parquet"))
    if len(files) < n:
        raise SystemExit(f"{folder}/{task}: {len(files)} of {n} chunks")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def wavg(v, w):
    return float(np.average(v, weights=w)) if len(v) else float("nan")


def wmed(v, w):
    if not len(v):
        return float("nan")
    o = np.argsort(v)
    c = np.cumsum(np.asarray(w)[o])
    return float(np.asarray(v)[o][np.searchsorted(c, c[-1] / 2)])


def main():
    s36 = importlib.import_module("36_route_aggregate")
    cells = s36.cells_by_iris().drop_duplicates("cell_id")[["cell_id", "code_iris", "pop"]]
    cells["dep"] = cells.code_iris.str[:2]
    say("Wheelchair travel times — descriptive decomposition (pre-registered 2026-10-07 07:28)")
    say("=" * 88)
    for name, (folder, n) in SETS.items():
        say(f"\n##### {name} places (Tuesday 10:00)")
        comb = {m: load(folder + "_v2", f"{m}_tue10", n) for m in MODES}
        walk = {m: load(folder + "_v2_decomp", f"{m}_places_walk", n) for m in MODES}
        allstops = load(folder + "_v2_decomp", "wc_allstops_tue10", n)

        say("\n1. Share of cell x place pairs entirely on foot (population-weighted, pairs reached by the combined time)")
        for m, label in MODES.items():
            x = comb[m].merge(walk[m], on=["cell_id", "type"], how="left", suffixes=("", "_walk")).merge(cells, on="cell_id")
            x["on_foot"] = x["minutes_walk"].notna() & (x["minutes"] >= x["minutes_walk"])
            by_type = x.groupby("type").apply(lambda g: 100 * wavg(g.on_foot, g["pop"]), include_groups=False)
            by_dep = x.groupby("dep").apply(lambda g: 100 * wavg(g.on_foot, g["pop"]), include_groups=False)
            say(f"   {label}: on foot {100 * wavg(x.on_foot, x['pop']):.1f} %, with public transport {100 - 100 * wavg(x.on_foot, x['pop']):.1f} %"
                f" | by département " + ", ".join(f"{k} {v:.0f} %" for k, v in by_dep.items()))
            say("      by place: " + ", ".join(f"{k} {v:.0f} %" for k, v in by_type.items()))

        say("\n2. Wheelchair minus without constraint: speed and slopes vs inaccessible stops (minutes, population-weighted)")
        d = (comb["standard"].rename(columns={"minutes": "std"})
             .merge(comb["step_free_no"].rename(columns={"minutes": "wc"}), on=["cell_id", "type"], how="outer")
             .merge(allstops.rename(columns={"minutes": "all"}), on=["cell_id", "type"], how="outer")
             .merge(cells, on="cell_id"))
        complete = d[["std", "wc", "all"]].notna().all(axis=1)
        say(f"   pairs reached in all three runs: {int(complete.sum()):,}; not reached in at least one: {int((~complete).sum()):,} "
            f"(without constraint {int(d['std'].isna().sum()):,}, wheelchair {int(d['wc'].isna().sum()):,}, wheelchair with every stop {int(d['all'].isna().sum()):,})")
        c = d[complete].copy()
        c["total"], c["speed"], c["stops"] = c.wc - c["std"], c["all"] - c["std"], c.wc - c["all"]
        say(f"   all places: total mean {wavg(c.total, c['pop']):.1f} (median {wmed(c.total.values, c['pop'].values):.0f}); "
            f"speed and slopes {wavg(c.speed, c['pop']):.1f} (median {wmed(c.speed.values, c['pop'].values):.0f}); "
            f"inaccessible stops {wavg(c.stops, c['pop']):.1f} (median {wmed(c.stops.values, c['pop'].values):.0f}); "
            f"pairs with no stop effect {100 * wavg(c.stops == 0, c['pop']):.0f} %")
        for key, g in [*c.groupby("type"), *[(f"dep {k}", v) for k, v in c.groupby("dep")]]:
            say(f"   {key:22} total {wavg(g.total, g['pop']):5.1f} | speed and slopes {wavg(g.speed, g['pop']):5.1f} | inaccessible stops {wavg(g.stops, g['pop']):5.1f}"
                f" | share of the total from stops {100 * wavg(g.stops, g['pop']) / max(wavg(g.total, g['pop']), 1e-9):4.0f} %")

        w = walk["standard"].rename(columns={"minutes": "w_std"}).merge(walk["step_free_no"].rename(columns={"minutes": "w_wc"}), on=["cell_id", "type"]).merge(cells, on="cell_id")
        w["diff"] = w.w_wc - w.w_std
        say(f"\n   Complement, walking alone: wheelchair (0.8 m/s, slope network) - without constraint (4.5 km/h): mean {wavg(w['diff'], w['pop']):.1f} min, "
            f"ratio of means {wavg(w.w_wc, w['pop']) / wavg(w.w_std, w['pop']):.2f} (pairs reached on foot in both: {len(w):,})")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
