"""Pre-registered crossing "ménages sans voiture" (CLAUDE.md, proposed and
validated by the project owner on 2026-10-03, before any calculation; run
after the switch to the 2022 census, as decided).

Main question: are the neighbourhoods with the highest share of households
without a car more often in the quarter farthest from public services, on
foot and by public transport?

- Car-free share = 1 - P22_RP_VOIT1P / P22_RP (2022 census, IRIS base
  "logement"; floor of 20 households, as the other rates).
- Indicator: the one of the published crossing (scripts/analysis/
  routes_means.py): mean percentile rank of the times to the nearest town
  hall, France Services, CAF, CPAM, France Travail and post office, Tuesday
  10:00, no-constraint profile; worst quarter over the MGP's inhabited
  neighbourhoods.
- Thirds of car-free share computed WITHIN each département. For each
  département d: gap_d = share in the worst quarter among the most car-free
  third - share among the least car-free third; rho_d = Spearman(car-free
  share, indicator).
- Supported if gap_d >= +10 points and rho_d >= +0.10 in at least 2
  départements, at least one other than Paris; refuted if at least 2
  départements are clearly reversed (gap_d <= -10 and rho_d <= -0.10);
  qualified otherwise. Reported without changing the verdict: same gaps at
  equal density (MGP density fifths).
- Number of car-free households (P22_RP - P22_RP_VOIT1P) living in the
  worst-quarter neighbourhoods, by département.
- Check of the same pre-registration: the published crossing means x public
  services redone at comparable motorisation (MGP fifths of car-free share,
  same weighting as the density check), reported beside the published
  verdict, which does not change. Motorisation depends partly on income:
  this check can remove part of the gap without saying anything about its
  cause.

Output: data/interim/analysis/carfree_means.txt.
"""
import importlib.util
import io
import json
import sys
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

import config

spec = importlib.util.spec_from_file_location("routes_means", Path(__file__).resolve().parent / "routes_means.py")
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)

OUT = config.DATA_INTERIM / "analysis" / "carfree_means.txt"
DEPS = rm.DEPS


def carfree_share() -> pd.DataFrame:
    with zipfile.ZipFile(config.DATA_RAW / "rp2022" / "base-ic-logement-2022_csv.zip") as z:
        df = pd.read_csv(z.open("base-ic-logement-2022.CSV"), sep=";", dtype={"IRIS": str}, usecols=["IRIS", "P22_RP", "P22_RP_VOIT1P"])
    df = df.set_index("IRIS")
    df["households"] = df.P22_RP
    df["carfree_n"] = df.P22_RP - df.P22_RP_VOIT1P
    df["carfree"] = (df.carfree_n / df.P22_RP).where(df.P22_RP >= 20)
    return df[["households", "carfree_n", "carfree"]]


def verdict(results: dict) -> str:
    clear = [d for d, r in results.items() if r["evaluable"] and r["gap"] >= 10 and r["rho"] >= 0.10]
    reversed_ = [d for d, r in results.items() if r["evaluable"] and r["gap"] <= -10 and r["rho"] <= -0.10]
    if len(clear) >= 2 and any(d != "75" for d in clear):
        return f"SOUTENUE (nettement plus éloignés dans {', '.join(clear)})"
    if len(reversed_) >= 2:
        return f"INFIRMÉE (nettement inversée dans {', '.join(reversed_)})"
    return f"NUANCÉE (plus éloignés : {', '.join(clear) or 'aucun'} ; inversée : {', '.join(reversed_) or 'aucun'})"


def main():
    cells = rm.agg.cells_by_iris()
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")[["code_iris", "population"]].set_index("code_iris")
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris")
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")
    base = pop.join(cap[["capacity_index"]]).join(carfree_share())
    base = base[base.population >= 50]
    base["dep"] = base.index.str[:2]
    base["density"] = base.population / (iris.area.reindex(base.index) / 1e6)

    ind = rm.indicator("standard", cells)
    df = base.join(ind.rename("ind"), how="inner").dropna(subset=["ind"])
    threshold = df["ind"].quantile(0.75)
    df["worst"] = df["ind"] > threshold
    d2 = df.dropna(subset=["carfree"]).copy()

    print(f"--- Ménages sans voiture x éloignement des services publics (sans contrainte, mardi 10 h ; seuil du quart le plus éloigné : rang moyen > {threshold:.3f}) ---")
    print(f"  quartiers habités avec une part de ménages sans voiture : {len(d2)} ; part médiane {d2.carfree.median():.1%} "
          f"(75 : {d2[d2.dep == '75'].carfree.median():.1%}, 92 : {d2[d2.dep == '92'].carfree.median():.1%}, "
          f"93 : {d2[d2.dep == '93'].carfree.median():.1%}, 94 : {d2[d2.dep == '94'].carfree.median():.1%})")
    out = {}
    for d in DEPS:
        x = d2[d2.dep == d].copy()
        x["third"] = pd.qcut(x["carfree"], 3, labels=[0, 1, 2])
        least, most = x[x.third == 0], x[x.third == 2]
        evaluable = len(least) >= 20 and len(most) >= 20
        gap = 100 * (most.worst.mean() - least.worst.mean())
        rho = x["carfree"].corr(x["ind"], method="spearman")
        out[d] = {"gap": gap, "rho": rho, "evaluable": evaluable}
        print(f"  {d}: tiers le plus sans voiture {100 * most.worst.mean():5.1f} % ({len(most)}) | tiers le moins {100 * least.worst.mean():5.1f} % ({len(least)}) | "
              f"écart {gap:+5.1f} pts | rho {rho:+.2f}{'' if evaluable else ' | non évaluable'}")
    d2["fifth"] = pd.qcut(d2["density"], 5, labels=False)
    for d in DEPS:
        x = d2[d2.dep == d].copy()
        x["third"] = pd.qcut(x["carfree"], 3, labels=[0, 1, 2])
        w_gap = w = 0
        for _, g in x.groupby("fifth"):
            lo, hi = g[g.third == 0], g[g.third == 2]
            if len(lo) >= 10 and len(hi) >= 10:
                n = min(len(lo), len(hi))
                w_gap += 100 * (hi.worst.mean() - lo.worst.mean()) * n
                w += n
        print(f"  {d} à densité égale : {w_gap / w:+.1f} pts" if w else f"  {d} à densité égale : effectifs insuffisants")
    print(f"  Verdict : {verdict(out)}")

    print("\n--- Ménages sans voiture vivant dans un quartier du quart le plus éloigné ---")
    w = d2[d2.worst]
    for d in DEPS:
        print(f"  {d}: {w[w.dep == d].carfree_n.sum():,.0f} ménages sans voiture (sur {d2[d2.dep == d].carfree_n.sum():,.0f} dans le département)")
    print(f"  MGP : {w.carfree_n.sum():,.0f} sur {d2.carfree_n.sum():,.0f}")

    print("\n--- Vérification : ressources x services publics à motorisation comparable (verdict publié inchangé) ---")
    d3 = df.dropna(subset=["carfree", "capacity_index"]).copy()
    d3["fifth"] = pd.qcut(d3["carfree"], 5, labels=False)
    for d in DEPS:
        x = d3[d3.dep == d].copy()
        x["third"] = pd.qcut(x["capacity_index"], 3, labels=[0, 1, 2])
        raw = 100 * (x[x.third == 0].worst.mean() - x[x.third == 2].worst.mean())
        w_gap = w = 0
        for _, g in x.groupby("fifth"):
            lo, hi = g[g.third == 0], g[g.third == 2]
            if len(lo) >= 10 and len(hi) >= 10:
                n = min(len(lo), len(hi))
                w_gap += 100 * (lo.worst.mean() - hi.worst.mean()) * n
                w += n
        controlled = f"{w_gap / w:+.1f} pts" if w else "effectifs insuffisants"
        print(f"  {d}: écart ressources faibles − élevées {raw:+.1f} pts ; à part de ménages sans voiture comparable : {controlled}")
    print("  Note : la motorisation dépend en partie du revenu ; ce contrôle peut effacer une partie de l'écart sans rien dire de sa cause.")


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(buf.getvalue(), encoding="utf-8")
    print(buf.getvalue())
