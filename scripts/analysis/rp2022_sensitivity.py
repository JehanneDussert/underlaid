"""Sensitivity check: switching the census from 2021 to 2022 (step 1 of 2).

Decision of 3 October 2026, taken before seeing these results: the 2022
census becomes the site's reference whatever they show; the differences
with 2021 are published as a sensitivity check, and the verdicts already
published stay unchanged. This script shows the differences only — no
crossing between exposure (or access) and residents' means: those are
redone in step 2, after the project owner's agreement.

What changes with the 2022 census (IRIS geography of 1 January 2024, the
same as the pipeline): population (score thresholds on inhabited IRIS,
cool-spot deficit per resident), second homes and overcrowding (means
axis; overcrowding changes definition: C22_RP_SUROCC_MOD + _ACC over all
main residences, instead of C21_RP_HSTU1P_SUROCC excluding one-person
studios). Income (Filosofi 2021) and the 200 m grid (access to care
demand) have no newer IRIS or grid vintage and stay as they are.

Reports: inhabited IRIS; score distribution (/4); IRIS changing score,
entering or leaving 3+/4 (the "most exposed" list) and 4/4; "highly
exposed" (2 of the 3 exposures) and access-to-care worst quarter
memberships; means thirds: share of IRIS changing third and the
transition table.

Usage (Docker image underlaid-access): python scripts/analysis/rp2022_sensitivity.py
Output: data/interim/analysis/rp2022_sensitivity.txt
"""
import importlib
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

RP22 = config.DATA_RAW / "rp2022"
OUT = config.DATA_INTERIM / "analysis" / "rp2022_sensitivity.txt"
EXPOSURES = ["thermal", "pollution", "housing"]
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def read_insee(zip_path, member, cols):
    with zipfile.ZipFile(zip_path) as z:
        df = pd.read_csv(z.open(member), sep=";", dtype={"IRIS": str}, usecols=lambda c: c in ["IRIS", *cols], low_memory=False)
    return df.set_index("IRIS")


def means_thirds(inc, over, sec):
    """Same recipe as script 26: mean of percentile ranks (income +,
    overcrowding −, second homes +), income required, thirds."""
    df = pd.DataFrame({"inc": inc, "over": over.reindex(inc.index), "sec": sec.reindex(inc.index)})
    r = pd.concat([df.inc.rank(pct=True), 1 - df.over.rank(pct=True), df.sec.rank(pct=True)], axis=1).mean(axis=1)
    r[df.inc.isna()] = np.nan
    return pd.qcut(r, 3, labels=False)


def main():
    pop21 = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson").set_index("code_iris").population
    pop22 = read_insee(RP22 / "base-ic-evol-struct-pop-2022_csv.zip", "base-ic-evol-struct-pop-2022.CSV", ["P22_POP"]).P22_POP
    log22 = read_insee(RP22 / "base-ic-logement-2022_csv.zip", "base-ic-logement-2022.CSV",
                       ["P22_LOG", "P22_RP", "P22_RSECOCC", "C22_RP_SUROCC_MOD", "C22_RP_SUROCC_ACC"])

    s11 = importlib.import_module("11_compute_vulnerability_score")
    base = s11.build_dataset()
    res = {}
    for name, pop in (("2021", pop21), ("2022", pop22)):
        df = base.drop(columns=["population"]).merge(pop.rename("population"), left_on="code_iris", right_index=True, how="left")
        res[name] = s11.compute_cumulative_score(s11.compute_subscores(s11.build_indicators(df))).set_index("code_iris")
    a, b = res["2021"], res["2022"].reindex(res["2021"].index)
    inh_a = a.population.fillna(0) >= 50
    inh_b = b.population.fillna(0) >= 50
    say("== Population")
    say(f"  total {pop21.sum():,.0f} -> {pop22.reindex(pop21.index).sum():,.0f}; inhabited IRIS (>= 50) {inh_a.sum()} -> {inh_b.sum()}")

    sa, sb = a.cumulative_vulnerability_score, b.cumulative_vulnerability_score
    say("\n== Exposure score /4, inhabited IRIS")
    say(f"  2021: {sa[inh_a].value_counts().sort_index().astype(int).to_dict()}")
    say(f"  2022: {sb[inh_b].value_counts().sort_index().astype(int).to_dict()}")
    changed = (sa != sb) & sa.notna() & sb.notna()
    say(f"  IRIS whose score changes: {changed.sum()} of {len(sa)} ({changed.mean():.1%}); by 1 point: {((sa - sb).abs() == 1).sum()}")
    top_a = set(sa[inh_a & (sa >= 3)].index)
    top_b = set(sb[inh_b & (sb >= 3)].index)
    say(f"  3+/4 list: {len(top_a)} -> {len(top_b)}; leaving {len(top_a - top_b)}, entering {len(top_b - top_a)}")
    for code in sorted(top_a - top_b):
        say(f"    leaves: {code} {a.loc[code, 'nom_iris']}, {a.loc[code, 'nom_com']} ({int(sa[code])} -> {sb[code]})")
    for code in sorted(top_b - top_a):
        say(f"    enters: {code} {a.loc[code, 'nom_iris']}, {a.loc[code, 'nom_com']} ({sa[code]} -> {int(sb[code])})")
    say(f"  4/4: {sorted(sa[inh_a & (sa == 4)].index)} -> {sorted(sb[inh_b & (sb == 4)].index)}")

    def very(x):
        return sum((x[f"subscore_{k}_quartile"] == 4).astype(int) for k in EXPOSURES) >= 2
    va, vb = very(a) & inh_a, very(b) & inh_b
    say(f"\n== Highly exposed (2 of the 3 exposures): {va.sum()} -> {vb.sum()}; leaving {(va & ~vb).sum()}, entering {(vb & ~va).sum()}")
    ca, cb = (a.subscore_access_care_quartile == 4) & inh_a, (b.subscore_access_care_quartile == 4) & inh_b
    say(f"== Access to care, worst quarter: {ca.sum()} -> {cb.sum()}; leaving {(ca & ~cb).sum()}, entering {(cb & ~ca).sum()}")
    for k in EXPOSURES + ["access_care"]:
        qa, qb = a[f"subscore_{k}_quartile"], b[f"subscore_{k}_quartile"]
        moved = (qa != qb) & qa.notna() & qb.notna()
        say(f"   {k:12s} quarter changes: {moved.sum()} IRIS ({moved.mean():.1%})")

    say("\n== Means axis (income 2021 kept; overcrowding and second homes 2021 -> 2022)")
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")
    inc = gpd.read_file(config.DATA_PROCESSED / "income_iris.geojson").set_index("code_iris").median_income
    sec21 = gpd.read_file(config.DATA_PROCESSED / "secondary_residences_iris.geojson").set_index("code_iris").pct_secondary_residences
    over21 = cap.pct_overcrowded
    floor = log22.P22_LOG >= 20
    sec22 = (log22.P22_RSECOCC / log22.P22_LOG).where(floor)
    over22 = ((log22.C22_RP_SUROCC_MOD + log22.C22_RP_SUROCC_ACC) / log22.P22_RP).where(floor)
    say(f"  overcrowding median {over21.median():.3f} -> {over22.reindex(over21.index).median():.3f} (definition changes); "
        f"second homes median {sec21.median():.3f} -> {sec22.reindex(sec21.index).median():.3f}")
    t21 = means_thirds(inc, over21, sec21)
    t22 = means_thirds(inc, over22, sec22)
    say(f"  check: rebuilt 2021 thirds equal to published: {(t21 == cap.capacity_class.reindex(t21.index)).mean():.1%}")
    ok = t21.notna() & t22.notna()
    say(f"  IRIS changing third: {(t21[ok] != t22[ok]).sum()} of {ok.sum()} ({(t21[ok] != t22[ok]).mean():.1%})")
    tab = pd.crosstab(t21[ok].map({0: "low", 1: "middle", 2: "high"}), t22[ok].map({0: "low", 1: "middle", 2: "high"}))
    say("  2021 third (rows) x 2022 third (columns):")
    for line in tab.reindex(index=["low", "middle", "high"], columns=["low", "middle", "high"]).to_string().splitlines():
        say("    " + line)
    by_dep = pd.Series(t21[ok] != t22[ok]).groupby(t21[ok].index.str[:2]).mean()
    say("  share changing third by département: " + ", ".join(f"{d} {v:.1%}" for d, v in by_dep.items()))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
