"""Pre-registered controls for the routes (CLAUDE.md, routes pre-registration,
point 6), run BEFORE any crossing with residents' means. Nothing here uses
the means axis.

For each time slot, profile and destination type, over inhabited IRIS
(>= 50 residents):
- distribution of neighbourhood medians: median, p10, p90, max, share of
  neighbourhoods at the floor (<= 2 min), skew, max |z| (crushing check, as
  for the former access_time);
- completeness: share of the MGP population whose cell does not reach the
  destination within 90 min;
- by département: median of neighbourhood medians (descriptive only);
- step-free vs standard: median ratio and imposed detour.
Stations: walking time to the nearest heavy-network stop point.

Runs on whatever tasks are complete (ROUTES_ALLOW_PARTIAL is not needed:
incomplete tasks are skipped and listed). Output printed and written to
data/interim/analysis/routes_controls.txt.
"""
import importlib
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

agg = importlib.import_module("36_route_aggregate")
OUT = config.DATA_INTERIM / "analysis" / "routes_controls.txt"
DEPS = ["75", "92", "93", "94"]
NAMES = {"emergency": "urgences", "gp": "médecin", "pharmacy": "pharmacie", "town_hall": "mairie", "france_services": "France Services",
         "caf": "CAF", "cpam": "CPAM", "employment": "France Travail", "post_office": "poste", "station": "station"}


def neighbourhood_table(task: pd.DataFrame, cells: pd.DataFrame, types: list[str]) -> pd.DataFrame:
    rows = agg.summarise(task, cells, types)
    return pd.DataFrame(rows).T  # IRIS x type, None = more than 90 min


def pop_not_reached(task: pd.DataFrame, cells: pd.DataFrame, types: list[str]) -> dict:
    reached = task.groupby("type")["cell_id"].apply(set)
    total = cells["pop"].sum()
    return {t: 100 * cells.loc[~cells.cell_id.isin(reached.get(t, set())), "pop"].sum() / total for t in types}


def describe(series: pd.Series) -> str:
    v = pd.to_numeric(series, errors="coerce").dropna()
    z = (v - v.mean()) / v.std() if v.std() else v * 0
    return (f"méd {v.median():4.0f} | p10 {v.quantile(.1):3.0f} p90 {v.quantile(.9):3.0f} max {v.max():3.0f} | "
            f"plancher<=2 {100 * (v <= 2).mean():4.1f}% | skew {v.skew():4.1f} | |z|max {z.abs().max():4.1f}")


def main():
    cells = agg.cells_by_iris()
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")[["code_iris", "population"]].set_index("code_iris").population
    inhabited = set(pop[pop >= 50].index)
    dep = lambda idx: pd.Series(idx.str[:2], index=idx)

    for slot in agg.SLOTS:
        print(f"\n===== Créneau {slot} =====")
        tables = {}
        for prof in agg.PROFILES:
            task = agg.load_task(f"{prof}_{slot}")
            if task is None:
                print(f"[{prof}] incomplet, ignoré")
                continue
            tab = neighbourhood_table(task, cells, agg.TYPES)
            tab = tab[tab.index.isin(inhabited)]
            tables[prof] = tab
            nr = pop_not_reached(task, cells, agg.TYPES)
            print(f"\n[{prof}] {len(tab)} quartiers habités")
            for t in agg.TYPES:
                over = 100 * tab[t].isna().mean()
                print(f"  {NAMES[t]:15s} {describe(tab[t])} | quartiers >90 {over:4.1f}% | pop. non atteinte {nr[t]:4.1f}%")
            d = tab.apply(pd.to_numeric, errors="coerce").groupby(dep(tab.index)).median().reindex(DEPS)
            print("  médiane par département (75/92/93/94) : " + " ; ".join(f"{NAMES[t]} {'/'.join(f'{x:.0f}' for x in d[t])}" for t in agg.TYPES))
        if "standard" in tables and "step_free_no" in tables:
            s = tables["standard"].apply(pd.to_numeric, errors="coerce")
            a = tables["step_free_no"].apply(pd.to_numeric, errors="coerce")
            print("\n[sans marches / sans contrainte] rapport médian des médianes de quartier, et part des quartiers où la durée au moins double")
            for t in agg.TYPES:
                r = (a[t] / s[t].replace(0, np.nan)).dropna()
                by = r.groupby(dep(r.index)).median().reindex(DEPS)
                print(f"  {NAMES[t]:15s} rapport méd {r.median():.2f} | x2 ou plus {100 * (r >= 2).mean():4.1f}% | par dép. {'/'.join(f'{x:.2f}' for x in by)}")
            det = agg.detour(agg.load_task(f"step_free_no_{slot}"), agg.load_task(f"standard_{slot}"), cells, agg.TYPES)
            det = pd.DataFrame(det).T
            det = det[det.index.isin(inhabited)].apply(pd.to_numeric, errors="coerce")
            print("  détour imposé (min, médiane des quartiers ; 75/92/93/94) : " + " ; ".join(
                f"{NAMES[t]} {det[t].median():.0f} ({'/'.join(f'{x:.0f}' for x in det[t].groupby(dep(det.index)).median().reindex(DEPS))})" for t in agg.TYPES))

    print("\n===== Stabilité : sans marches, inconnu = non / inconnu = oui (mardi 10 h) =====")
    no, yes = agg.load_task("step_free_no_tue10"), agg.load_task("step_free_yes_tue10")
    if no is None or yes is None:
        print("variante incomplète, contrôle reporté")
    else:
        tn = neighbourhood_table(no, cells, agg.TYPES).apply(pd.to_numeric, errors="coerce")
        ty = neighbourhood_table(yes, cells, agg.TYPES).apply(pd.to_numeric, errors="coerce")
        tn, ty = tn[tn.index.isin(inhabited)], ty[ty.index.isin(inhabited)]
        for t in agg.TYPES:
            a, b = tn[t].fillna(np.inf), ty[t].fillna(np.inf)
            qa, qb = a > a.quantile(.75), b > b.quantile(.75)
            print(f"  {NAMES[t]:15s} Spearman {a.corr(b, method='spearman'):.3f} | bascules du quart le plus long {100 * (qa != qb).mean():4.1f} % | écart médian {(b - a).replace([np.inf, -np.inf], np.nan).median():+.0f} min")
        services = ["town_hall", "france_services", "caf", "cpam", "employment", "post_office"]
        ra, rb = tn[services].fillna(np.inf).rank(pct=True).mean(axis=1), ty[services].fillna(np.inf).rank(pct=True).mean(axis=1)
        print(f"  indicateur services publics (rang moyen) : Spearman {ra.corr(rb, method='spearman'):.3f} | bascules du quart {100 * ((ra > ra.quantile(.75)) != (rb > rb.quantile(.75))).mean():.1f} %")

    print("\n===== Urgences la nuit (mardi 1 h) : distribution par quartier =====")
    for prof in ["standard", "slow", "step_free_no", "step_free_yes"]:
        task = agg.load_task(f"{prof}_tue01")
        if task is None:
            print(f"[{prof}] incomplet")
            continue
        e = pd.to_numeric(neighbourhood_table(task, cells, ["emergency"])["emergency"], errors="coerce")
        e = e[e.index.isin(inhabited)].fillna(np.inf)
        line = lambda v: f"méd {v.replace(np.inf, np.nan).median():.0f} min | >30 min {100 * (v > 30).mean():4.1f} % | >45 min {100 * (v > 45).mean():4.1f} % | >90 {100 * np.isinf(v).mean():.1f} %"
        print(f"[{prof}] ensemble : {line(e)}")
        for d in DEPS:
            print(f"    {d} : {line(e[e.index.str[:2] == d])}")

    print("\n===== Stations (à pied) =====")
    for prof in agg.PROFILES:
        task = agg.load_task(f"{prof}_stations_walk")
        if task is None:
            print(f"[{prof}] incomplet, ignoré")
            continue
        tab = neighbourhood_table(task, cells, ["station"])
        tab = tab[tab.index.isin(inhabited)]
        nr = pop_not_reached(task, cells, ["station"])["station"]
        d = pd.to_numeric(tab["station"], errors="coerce").groupby(dep(tab.index)).median().reindex(DEPS)
        print(f"[{prof}] {describe(tab['station'])} | quartiers >90 {100 * tab['station'].isna().mean():.1f}% | pop. non atteinte {nr:.1f}% | par dép. {'/'.join(f'{x:.0f}' for x in d)}")


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(buf.getvalue(), encoding="utf-8")
    print(buf.getvalue())
