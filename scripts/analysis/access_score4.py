"""After step 4: the score on 4 sub-scores, plus two checks asked on 2026-10-02.

Nothing published. Decisions (CLAUDE.md, "Hypothèse de travail", 6th
series, taken after the crossing): cumulative score on 4 sub-scores
(heat, air/noise, housing, access to care); inclusive mobility shown as
information only. Verdicts unchanged.

1. Absolute GP access when travelling step-free (gp_acc_no, and the
   unknown = yes variant), by department and means third — does it stay
   lower in the inner suburbs than in Paris?
2. Robustness of the access-to-care gap in 92 and 94 at equal population
   density (MGP density quintiles of inhabited IRIS) — reported as a
   nuance, the verdict doesn't change.
3. The score on 4: distribution, IRIS at 3 and 4, findings 1 to 3, means
   grid, and what /ranking would list.

Usage: python scripts/analysis/access_score4.py
"""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

DEPS = ["75", "92", "93", "94"]
TIERS = {0: "lowest third", 1: "middle third", 2: "highest third"}
NAMES = {"thermal": "heat", "pollution": "air/noise", "housing": "housing", "access_care": "access to care"}


def spearman(a, b):
    ok = a.notna() & b.notna()
    return a[ok].rank().corr(b[ok].rank())


def main():
    access = pd.read_csv(config.DATA_PROCESSED / "access_e2sfca_iris.csv", dtype={"code_iris": str}).set_index("code_iris")
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris")
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson").set_index("code_iris").population

    d = access.join(cap[["capacity_index", "capacity_class"]]).join(pop)
    d["dep"] = d.index.str[:2]
    d["density"] = d.population / (iris.area.reindex(d.index) / 1e6)
    inh = d.population >= 50

    # ---- 1. absolute accessible access ------------------------------------
    print("== 1. GP access travelling step-free (per 10,000 age-weighted residents), median of inhabited IRIS")
    for col in ("gp_acc_no", "gp_acc_yes"):
        x = d[inh & d.capacity_class.notna()]
        t = x.pivot_table(index="dep", columns="capacity_class", values=col, aggfunc="median").rename(columns=TIERS)
        t["all"] = d[inh].groupby("dep")[col].median()
        print(f"  {col}:")
        print(t.round(2).to_string())
        paris = t.loc["75"]
        holds = all((t.loc[dp] < paris).all() for dp in ("92", "93", "94"))
        print(f"  lower than Paris in every department and every means third: {holds}")
        for dp in ("92", "93", "94"):
            print(f"    {dp} vs Paris, all IRIS: {t.loc[dp, 'all']:.2f} vs {paris['all']:.2f} ({(t.loc[dp, 'all'] / paris['all'] - 1):+.0%})")

    # ---- the score on 4 ---------------------------------------------------
    s11 = importlib.import_module("11_compute_vulnerability_score")
    full = dict(s11.SUB_SCORES)
    # "/3" reference: the published score without access_care.
    s11.SUB_SCORES = {k: v for k, v in full.items() if k != "access_care"}
    s11.SUB_SCORE_MIN_INDICATORS = {n: len(i) // 2 + 1 for n, i in s11.SUB_SCORES.items()}
    base = s11.build_dataset()
    ref3 = s11.compute_cumulative_score(s11.compute_subscores(s11.build_indicators(base.copy()))).set_index("code_iris")
    df = s11.build_indicators(base.copy())
    df["gp_deficit"] = -df.code_iris.map(access.gp_std)
    df["pharmacy_deficit"] = -df.code_iris.map(access.pharmacy_std)
    s11.SUB_SCORES = full
    s11.SUB_SCORE_MIN_INDICATORS = {n: len(i) // 2 + 1 for n, i in s11.SUB_SCORES.items()}
    s11.RANK_STANDARDIZED_INDICATORS = {"access_time", "gp_deficit", "pharmacy_deficit"}
    r = s11.compute_cumulative_score(s11.compute_subscores(df)).set_index("code_iris")
    r = r.join(cap[["capacity_index", "capacity_class"]])
    inh4 = r.population.fillna(0) >= 50
    dep = pd.Series(r.index.str[:2], index=r.index)
    q4 = (r.subscore_access_care_quartile == 4)

    # ---- 2. robustness at equal density -----------------------------------
    print("\n== 2. Access to care: worst-quarter share, lowest vs highest means third, within MGP density quintiles")
    x = d[inh & d.capacity_class.notna()].copy()
    x["q4"] = q4.reindex(x.index)
    x["band"] = pd.qcut(x.density, 5, labels=["Q1 least dense", "Q2", "Q3", "Q4", "Q5 densest"])
    x["access_care"] = r.subscore_access_care.reindex(x.index)
    for dp in ("92", "94"):
        y = x[(x.dep == dp) & x.access_care.notna()]
        rows, w_gap, w = [], 0.0, 0
        for band, g in y.groupby("band", observed=True):
            low, high = g[g.capacity_class == 0], g[g.capacity_class == 2]
            ok = len(low) >= 10 and len(high) >= 10
            gap = 100 * (low.q4.mean() - high.q4.mean()) if ok else np.nan
            rows.append({"band": band, "n low": len(low), "n high": len(high), "Q4 low %": round(100 * low.q4.mean(), 1) if len(low) else np.nan,
                         "Q4 high %": round(100 * high.q4.mean(), 1) if len(high) else np.nan, "gap pts": round(gap, 1)})
            if ok:
                n = min(len(low), len(high))
                w_gap += gap * n
                w += n
        print(f"  {dp}:")
        print(pd.DataFrame(rows).set_index("band").to_string())
        print(f"  {dp}: gap at equal density (weighted mean over quintiles with >= 10 IRIS per third): "
              f"{w_gap / w:+.1f} pts" if w else f"  {dp}: no quintile with enough IRIS in both thirds")
        print(f"  {dp}: overall gap without density control: "
              f"{100 * (y[y.capacity_class == 0].q4.mean() - y[y.capacity_class == 2].q4.mean()):+.1f} pts; "
              f"Spearman(means, access-to-care deficit) partial on density: "
              f"{np.corrcoef(*(v - np.polyval(np.polyfit(y.density.rank(), v, 1), y.density.rank()) for v in (y.capacity_index.rank(), y.access_care.rank())))[0, 1]:+.2f}")

    # ---- 3. the score on 4 ------------------------------------------------
    print("\n== 3. Score on 4 (heat, air/noise, housing, access to care), inhabited IRIS")
    print("  /3 (published):", ref3.cumulative_vulnerability_score[inh4.reindex(ref3.index)].value_counts().sort_index().astype(int).to_dict())
    print("  /4:", r.cumulative_vulnerability_score[inh4].value_counts().sort_index().astype(int).to_dict())
    old_top = ref3.index[(ref3.cumulative_vulnerability_score == 3) & inh4.reindex(ref3.index)]
    print("  the 31 inhabited IRIS at 3/3 -> /4:", r.cumulative_vulnerability_score.reindex(old_top).value_counts().sort_index().astype(int).to_dict())
    for thr in (4, 3):
        top = r.index[(r.cumulative_vulnerability_score >= thr) & inh4]
        print(f"  >= {thr}/4: {len(top)} IRIS, by department {dep[top].value_counts().sort_index().to_dict()}")
    qcols = [f"subscore_{k}_quartile" for k in NAMES]
    combo = r[qcols].eq(4).apply(lambda row: " + ".join(NAMES[c.replace("subscore_", "").replace("_quartile", "")] for c, v in row.items() if v), axis=1)
    top4 = r[(r.cumulative_vulnerability_score == 4) & inh4]
    print("\n  IRIS at 4/4:")
    print(top4.assign(means=top4.capacity_class.map(TIERS))[["nom_com", "nom_iris", "means"]].sort_values("nom_com").to_string())
    t3 = r[(r.cumulative_vulnerability_score == 3) & inh4]
    print("\n  IRIS at 3/4 — combinations by department:")
    print(pd.crosstab(combo[t3.index], dep[t3.index]).to_string())
    new_in = r.index[(r.cumulative_vulnerability_score >= 3) & inh4 & ~r.index.isin(old_top)]
    out = [i for i in old_top if r.cumulative_vulnerability_score.get(i, 0) < 3]
    print(f"\n  enter 3+/4 (were below 3/3): {len(new_in)} — all through access to care: {bool(q4[new_in].all())}; leave: {len(out)}")

    m = inh4 & r.capacity_index.notna()
    tier = r.capacity_class
    expo = pd.cut(r.cumulative_vulnerability_score, [-1, 0, 1, 5], labels=["0", "1", "2+"])
    print("\n  exposure (0 / 1 / 2+) x means grid:")
    print(pd.crosstab(expo[m], tier[m].map(TIERS))[list(TIERS.values())].to_string())
    print(f"\n  Finding 2 — Spearman(means, score /4): {spearman(r.capacity_index[m], r.cumulative_vulnerability_score[m]):+.2f} "
          f"(/3: {spearman(r.capacity_index[m], ref3.cumulative_vulnerability_score.reindex(r.index)[m]):+.2f}); by department "
          + ", ".join(f"{dp} {spearman(r.capacity_index[m & (dep == dp)], r.cumulative_vulnerability_score[m & (dep == dp)]):+.2f}" for dp in DEPS))
    hi = m & (r.cumulative_vulnerability_score >= 2)
    print("  Finding 3 — share of IRIS at 2+/4 in the lowest means third:",
          {dp: f"{(tier[hi & (dep == dp)] == 0).mean():.0%} of {int((hi & (dep == dp)).sum())}" for dp in DEPS})
    hi3 = m & (r.cumulative_vulnerability_score >= 3)
    print("                   at 3+/4:", {dp: f"{(tier[hi3 & (dep == dp)] == 0).mean():.0%} of {int((hi3 & (dep == dp)).sum())}" for dp in DEPS})
    print("  Finding 1 — sub-score profile of IRIS at 2+/4 (% in worst quarter), by means third, and where they are:")
    prof = r.loc[hi, qcols].eq(4).groupby(tier[hi]).mean().mul(100).round(0)
    prof.columns = list(NAMES.values())
    prof.index = prof.index.map(TIERS)
    prof["n"] = tier[hi].map(TIERS).value_counts()
    print(prof.to_string())
    print(pd.crosstab(tier[hi].map(TIERS), dep[hi]).to_string())
    pd.DataFrame({"score4": r.cumulative_vulnerability_score, "score3": ref3.cumulative_vulnerability_score.reindex(r.index)}).to_csv(
        config.DATA_INTERIM / "analysis" / "access_score4.csv")


if __name__ == "__main__":
    main()
