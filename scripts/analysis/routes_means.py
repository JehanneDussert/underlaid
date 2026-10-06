"""Crossing of the routes with residents' means — exactly as pre-registered
on 2026-10-02 (CLAUDE.md, routes pre-registration, point 7). To be run only
once the travel-time run is complete and the controls have been shown
(scripts/analysis/routes_controls.py). The public-service times are
information, not a scored sub-score (decision of 2026-10-03, taken before
any crossing); this test is reported anyway, as planned.

Primary indicators (two only):
- access to public services = mean percentile rank of the times to the
  nearest town hall, France Services, CAF, CPAM, France Travail and post
  office, Tuesday 10:00, oriented "higher = less favourable";
  (a) no-constraint profile, (b) step-free profile — the conclusion for (b)
  holds only if identical with "unknown = not accessible" and "unknown =
  accessible".
- Thirds of means computed WITHIN each département (published means index,
  2021); worst quarter defined over the MGP's inhabited neighbourhoods.
- For each département d: gap_d = share in the worst quarter among the
  lowest third of means - share among the highest third; rho_d = Spearman
  (means index, indicator). Clearly unfavourable if gap_d >= +10 points and
  rho_d <= -0.10.
- Supported if clearly unfavourable in at least 2 départements, at least
  one other than Seine-Saint-Denis; refuted if at least 2 départements are
  clearly reversed (gap_d <= -10 and rho_d >= +0.10); qualified otherwise.
- Robustness, reported without changing the verdict: same gaps within MGP
  density fifths.

Output printed and written to data/interim/analysis/routes_means.txt.
"""
import importlib
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

agg = importlib.import_module("36_route_aggregate")
OUT = config.DATA_INTERIM / "analysis" / ("routes_means_v2.txt" if getattr(agg, "VERSION", "1") == "2" else "routes_means.txt")
SERVICES = ["town_hall", "france_services", "caf", "cpam", "employment", "post_office"]
DEPS = ["75", "92", "93", "94"]


def indicator(profile: str, cells: pd.DataFrame) -> pd.Series:
    task = agg.load_task(f"{profile}_tue10")
    if task is None:
        sys.exit(f"{profile}_tue10 incomplete: run only once script 34 has finished.")
    tab = pd.DataFrame(agg.summarise(task, cells, SERVICES)).T.apply(pd.to_numeric, errors="coerce")
    # "More than 90 min" ranks as the worst value.
    ranks = tab.fillna(np.inf).rank(pct=True)
    return ranks.mean(axis=1).rename(profile)


def verdict(results: dict) -> str:
    clear = [d for d, r in results.items() if r["evaluable"] and r["gap"] >= 10 and r["rho"] <= -0.10]
    reversed_ = [d for d, r in results.items() if r["evaluable"] and r["gap"] <= -10 and r["rho"] >= 0.10]
    if len(clear) >= 2 and any(d != "93" for d in clear):
        return f"SOUTENUE (nettement défavorable dans {', '.join(clear)})"
    if len(reversed_) >= 2:
        return f"INFIRMÉE (nettement inversée dans {', '.join(reversed_)})"
    return f"NUANCÉE (défavorable : {', '.join(clear) or 'aucun'} ; inversée : {', '.join(reversed_) or 'aucun'})"


def test(ind: pd.Series, base: pd.DataFrame, label: str) -> dict:
    df = base.join(ind.rename("ind"), how="inner").dropna(subset=["ind", "capacity_index"])
    threshold = df["ind"].quantile(0.75)
    df["worst"] = df["ind"] > threshold
    out = {}
    print(f"\n--- {label} (seuil du quart le plus défavorable : rang moyen > {threshold:.3f}) ---")
    for d in DEPS:
        x = df[df.dep == d].copy()
        x["third"] = pd.qcut(x["capacity_index"], 3, labels=[0, 1, 2])
        low, high = x[x.third == 0], x[x.third == 2]
        evaluable = len(low) >= 20 and len(high) >= 20
        gap = 100 * (low.worst.mean() - high.worst.mean())
        rho = x["capacity_index"].corr(x["ind"], method="spearman")
        out[d] = {"gap": gap, "rho": rho, "evaluable": evaluable}
        print(f"  {d}: tiers bas {100 * low.worst.mean():5.1f} % ({len(low)}) | tiers haut {100 * high.worst.mean():5.1f} % ({len(high)}) | "
              f"écart {gap:+5.1f} pts | rho {rho:+.2f}{'' if evaluable else ' | non évaluable'}")
    # Robustness at equal density (reported, verdict unchanged).
    df["fifth"] = pd.qcut(df["density"], 5, labels=False)
    for d in DEPS:
        x = df[df.dep == d].copy()
        x["third"] = pd.qcut(x["capacity_index"], 3, labels=[0, 1, 2])
        w_gap = w = 0
        for _, g in x.groupby("fifth"):
            lo, hi = g[g.third == 0], g[g.third == 2]
            if len(lo) >= 10 and len(hi) >= 10:
                n = min(len(lo), len(hi))
                w_gap += 100 * (lo.worst.mean() - hi.worst.mean()) * n
                w += n
        print(f"  {d} à densité égale : {w_gap / w:+.1f} pts" if w else f"  {d} à densité égale : effectifs insuffisants")
    print(f"  Verdict : {verdict(out)}")
    return out


def main():
    cells = agg.cells_by_iris()
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")[["code_iris", "population"]].set_index("code_iris")
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris")
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")
    base = pop.join(cap[["capacity_index"]])
    base = base[base.population >= 50]
    base["dep"] = base.index.str[:2]
    base["density"] = base.population / (iris.area.reindex(base.index) / 1e6)

    test(indicator("standard", cells), base, "(a) Sans contrainte")
    no = test(indicator("step_free_no", cells), base, "(b) Sans marches, inconnu = non accessible")
    yes = test(indicator("step_free_yes", cells), base, "(b) Sans marches, inconnu = accessible")
    same = verdict(no).split(" ")[0] == verdict(yes).split(" ")[0]
    print(f"\n(b) conclusion retenue : {verdict(no) if same else 'NUANCÉE (les deux variantes divergent)'}")


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(buf.getvalue(), encoding="utf-8")
    print(buf.getvalue())
