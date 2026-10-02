"""Freshness check: what would switching to the 2022 census (IRIS) change?

One-off analysis, nothing published. Compares the 2021 census bases used
by the pipeline (population: script 21; housing: scripts 24-25) with the
2022 ones (insee.fr/fr/statistiques/8647014 and 8647012, published
2025-10-16, IRIS geography of 1 January 2024 — the same IRIS edition as
the pipeline). Filosofi (income, 200 m grid) has no newer IRIS or grid
vintage than 2021, so it stays as is.

Reports: IRIS code match; population change and IRIS crossing the
50-resident floor; secondary-residence share change; overcrowding (the
2021 variable C21_RP_HSTU1P_SUROCC no longer exists in 2022, replaced by
C22_RP_SUROCC_MOD + C22_RP_SUROCC_ACC over all main residences); effect on
the exposure score (script 11 rerun with 2022 population) and on the
means axis (capacity index rebuilt with 2022 overcrowding and secondary
residences, income unchanged).

Usage: python scripts/analysis/rp2022_freshness.py
"""
import importlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

RP22 = config.DATA_RAW / "rp2022"


def read_insee(zip_path: Path, member: str, cols: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        df = pd.read_csv(z.open(member), sep=";", dtype={"IRIS": str}, usecols=lambda c: c in ["IRIS", *cols], low_memory=False)
    return df.set_index("IRIS")


def spearman(a, b):
    ok = a.notna() & b.notna()
    return a[ok].rank().corr(b[ok].rank())


def main():
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris"]].set_index("code_iris")
    pop21 = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson").set_index("code_iris").population
    pop22 = read_insee(RP22 / "base-ic-evol-struct-pop-2022_csv.zip", "base-ic-evol-struct-pop-2022.CSV", ["P22_POP"]).P22_POP
    log22 = read_insee(RP22 / "base-ic-logement-2022_csv.zip", "base-ic-logement-2022.CSV",
                       ["P22_LOG", "P22_RP", "P22_RSECOCC", "C22_RP_SUROCC_MOD", "C22_RP_SUROCC_ACC"])
    import json
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")

    print("== IRIS codes")
    print(f"  MGP IRIS in reference: {len(iris)}; found in RP 2022 population: {iris.index.isin(pop22.index).sum()}; "
          f"in RP 2022 housing: {iris.index.isin(log22.index).sum()}")

    p = pd.DataFrame({"p21": pop21, "p22": pop22.reindex(pop21.index)})
    ch = (p.p22 - p.p21) / p.p21.replace(0, np.nan)
    print("\n== Population 2021 -> 2022 (MGP IRIS)")
    print(f"  total {p.p21.sum():,.0f} -> {p.p22.sum():,.0f}; median IRIS change {ch.median():+.1%}, "
          f"|change| > 10%: {(ch.abs() > 0.10).mean():.1%} of IRIS")
    print(f"  IRIS crossing the 50-resident floor: {((p.p21 >= 50) != (p.p22 >= 50)).sum()}")

    sec22 = log22.P22_RSECOCC / log22.P22_LOG.where(log22.P22_LOG >= 20)
    over22 = (log22.C22_RP_SUROCC_MOD + log22.C22_RP_SUROCC_ACC) / log22.P22_RP.where(log22.P22_LOG >= 20)
    print("\n== Means axis indicators")
    sec21 = gpd.read_file(config.DATA_PROCESSED / "secondary_residences_iris.geojson").set_index("code_iris").pct_secondary_residences
    over21 = cap.pct_overcrowded
    print(f"  secondary residences 2021 vs 2022: Spearman {spearman(sec21, sec22.reindex(sec21.index)):.2f}, "
          f"median {sec21.median():.3f} -> {sec22.reindex(sec21.index).median():.3f}")
    print(f"  overcrowding 2021 (HSTU1P definition) vs 2022 (MOD+ACC / main residences): Spearman "
          f"{spearman(over21, over22.reindex(over21.index)):.2f}, median {over21.median():.3f} -> {over22.reindex(over21.index).median():.3f}")

    # Capacity index rebuilt (same recipe as script 26: mean of percentile ranks, income required).
    inc = gpd.read_file(config.DATA_PROCESSED / "income_iris.geojson").set_index("code_iris").median_income
    def index(over, sec):
        df = pd.DataFrame({"inc": inc, "over": over.reindex(inc.index), "sec": sec.reindex(inc.index)})
        r = pd.concat([df.inc.rank(pct=True), 1 - df.over.rank(pct=True), df.sec.rank(pct=True)], axis=1).mean(axis=1)
        r[df.inc.isna()] = np.nan
        return pd.qcut(r, 3, labels=False)
    c21 = index(over21, sec21)
    c22 = index(over22, sec22)
    moved = (c21 != c22) & c21.notna() & c22.notna()
    print(f"\n== Means tier (thirds) rebuilt: IRIS changing tier {moved.sum()} of {c21.notna().sum()} ({moved.mean():.1%}); "
          f"check vs published tiers: {(c21 == cap.capacity_class.reindex(c21.index)).mean():.1%} identical")

    s11 = importlib.import_module("11_compute_vulnerability_score")
    base = s11.build_dataset()
    res = {}
    for name, pop in (("2021", pop21), ("2022", pop22)):
        df = base.drop(columns=["population"]).merge(pop.rename("population"), left_on="code_iris", right_index=True, how="left")
        res[name] = s11.compute_cumulative_score(s11.compute_subscores(s11.build_indicators(df))).set_index("code_iris")
    a, b = res["2021"], res["2022"]
    inh = a.population.fillna(0) >= 50
    print("\n== Exposure score with 2022 population (inhabited IRIS, 0/1/2/3)")
    print("  2021:", a.cumulative_vulnerability_score[inh].value_counts().sort_index().to_dict())
    print("  2022:", b.cumulative_vulnerability_score[inh.reindex(b.index)].value_counts().sort_index().to_dict())
    print(f"  IRIS whose score changes: {(a.cumulative_vulnerability_score != b.cumulative_vulnerability_score.reindex(a.index)).sum()}")


if __name__ == "__main__":
    main()
