"""Step 4 of the access rebuild: the score on 5 sub-scores, then the
crossing with residents' means, against the pre-registered criteria.

Nothing is published or written to data/processed. Sub-score
construction and the operational criteria were written to CLAUDE.md
("Pré-enregistrement de l'étape 4", 2026-10-02) before this script was
run; they're reproduced here as code, not tuned.

- access_care: rank-standardized GP deficit (-gp_std) and pharmacy
  deficit (-pharmacy_std), both required;
- mobility: loss when travelling step-free (-gp_gap_no; variant
  -gp_gap_yes), one indicator;
- worst quartile set on inhabited IRIS (script 11's rule).

Usage: python scripts/analysis/access_step4.py
"""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import config

OUT_DIR = config.DATA_INTERIM / "analysis"
DEPS = ["75", "92", "93", "94"]
NEW = ["access_care", "mobility"]
GAP_PP, RHO, MIN_PER_TERTILE = 10.0, 0.10, 20


def spearman(a, b):
    ok = a.notna() & b.notna()
    return a[ok].rank().corr(b[ok].rank())


def score(s11, base, access, gap_col):
    df = s11.build_indicators(base.copy())
    acc = access.set_index("code_iris")
    df["gp_deficit"] = -df.code_iris.map(acc.gp_std)
    df["pharmacy_deficit"] = -df.code_iris.map(acc.pharmacy_std)
    df["mobility_loss"] = -df.code_iris.map(acc[gap_col])
    s11.SUB_SCORES = dict(s11.SUB_SCORES_3, access_care=["gp_deficit", "pharmacy_deficit"], mobility=["mobility_loss"])
    s11.SUB_SCORE_MIN_INDICATORS = {n: len(i) // 2 + 1 for n, i in s11.SUB_SCORES.items()}
    s11.RANK_STANDARDIZED_INDICATORS = {"access_time", "gp_deficit", "pharmacy_deficit", "mobility_loss"}
    df = s11.compute_cumulative_score(s11.compute_subscores(df))
    return df.set_index("code_iris")


def main():
    s11 = importlib.import_module("11_compute_vulnerability_score")
    # The published score now has access_care; the "/3" reference drops it.
    s11.SUB_SCORES = {k: v for k, v in s11.SUB_SCORES.items() if k != "access_care"}
    s11.SUB_SCORE_MIN_INDICATORS = {n: len(i) // 2 + 1 for n, i in s11.SUB_SCORES.items()}
    s11.SUB_SCORES_3 = dict(s11.SUB_SCORES)
    base = s11.build_dataset()
    ref3 = s11.compute_cumulative_score(s11.compute_subscores(s11.build_indicators(base.copy()))).set_index("code_iris")
    access = pd.read_csv(config.DATA_PROCESSED / "access_e2sfca_iris.csv", dtype={"code_iris": str})
    runs = {"main (unknown = no)": score(s11, base, access, "gp_gap_no"),
            "variant (unknown = yes)": score(s11, base, access, "gp_gap_yes")}
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"]).set_index("code_iris")
    main = runs["main (unknown = no)"]
    inh = main.population.fillna(0) >= 50
    dep = pd.Series(main.index.str[:2], index=main.index)
    names = {"thermal": "heat", "pollution": "air/noise", "housing": "housing", "access_care": "access to care", "mobility": "inclusive mobility"}

    print("== 1. Distribution, inhabited IRIS")
    print("  score /3 (published):", ref3.cumulative_vulnerability_score[inh.reindex(ref3.index)].value_counts().sort_index().astype(int).to_dict())
    for n, r in runs.items():
        print(f"  score /5, {n}:", r.cumulative_vulnerability_score[inh].value_counts().sort_index().astype(int).to_dict())
    print("  insufficient data, access_care / mobility:", int((main.subscore_access_care_status != "ok")[inh].sum()), "/", int((main.subscore_mobility_status != "ok")[inh].sum()))

    print("\n== 2. Worst-quarter share by department (%), inhabited IRIS")
    t = pd.DataFrame({names[k]: (main[f"subscore_{k}_quartile"] == 4)[inh].groupby(dep[inh]).mean() * 100 for k in names})
    print(t.round(1).to_string())
    print("  Spearman between sub-scores (inhabited):")
    sub = main.loc[inh, [f"subscore_{k}" for k in names]].rename(columns=lambda c: names[c.replace("subscore_", "")])
    print(sub.rank().corr().round(2).to_string())

    print("\n== 3. High scores: the 31 inhabited IRIS at 3/3 before, and the IRIS at 4+/5 now")
    old_top = ref3.index[(ref3.cumulative_vulnerability_score == 3) & inh.reindex(ref3.index)]
    print("  old 3/3 -> new score /5:", main.cumulative_vulnerability_score.reindex(old_top).value_counts().sort_index().astype(int).to_dict())
    for thr in (4, 3):
        top = main.index[(main.cumulative_vulnerability_score >= thr) & inh]
        print(f"  new score >= {thr}/5: {len(top)} IRIS; by department {dep[top].value_counts().sort_index().to_dict()}")
    top4 = main.loc[(main.cumulative_vulnerability_score >= 4) & inh]
    combo = top4[[f"subscore_{k}_quartile" for k in names]].eq(4).apply(lambda r: " + ".join(names[c.replace("subscore_", "").replace("_quartile", "")] for c, v in r.items() if v), axis=1)
    print("  4+/5 combinations:", combo.value_counts().to_dict())
    print(top4.assign(combo=combo)[["nom_com", "nom_iris", "cumulative_vulnerability_score", "combo"]].sort_values(["cumulative_vulnerability_score", "nom_com"], ascending=[False, True]).to_string())
    entered = main.index[(main.cumulative_vulnerability_score >= 3) & inh & ~main.index.isin(old_top)]
    reason = main.loc[entered, ["subscore_access_care_quartile", "subscore_mobility_quartile"]].eq(4)
    print(f"  IRIS at 3+/5 that were not 3/3: {len(entered)}; with access to care in worst quarter {int(reason.subscore_access_care_quartile.sum())}, "
          f"with inclusive mobility {int(reason.subscore_mobility_quartile.sum())}")

    # ---- crossing with means ----------------------------------------------
    c = cap.reindex(main.index)
    m = inh & c.capacity_index.notna()
    tier = c.capacity_class
    print("\n== 4. Exposure (score /5) x means grid, inhabited IRIS with a means index")
    expo = pd.cut(main.cumulative_vulnerability_score, [-1, 0, 1, 2, 5], labels=["0", "1", "2", "3+"])
    grid = pd.crosstab(expo[m], tier[m].map({0: "lowest third", 1: "middle third", 2: "highest third"}))
    print(grid[["lowest third", "middle third", "highest third"]].to_string())
    print(f"  Spearman(means, score /5): {spearman(c.capacity_index[m], main.cumulative_vulnerability_score[m]):+.2f} (score /3: "
          f"{spearman(c.capacity_index[m], ref3.cumulative_vulnerability_score.reindex(main.index)[m]):+.2f})")
    for d in DEPS:
        mm = m & (dep == d)
        print(f"    {d}: {spearman(c.capacity_index[mm], main.cumulative_vulnerability_score[mm]):+.2f}")
    hi = m & (main.cumulative_vulnerability_score >= 3)
    print("  Finding 3 — share of IRIS at 3+/5 in the lowest third of means, by department:",
          {d: f"{(tier[hi & (dep == d)] == 0).mean():.0%} of {int((hi & (dep == d)).sum())}" for d in DEPS})
    print("  Finding 1 — sub-score profile of IRIS at 3+/5 (% in worst quarter), by means third:")
    prof = main.loc[hi, [f"subscore_{k}_quartile" for k in names]].eq(4).groupby(tier[hi]).mean().mul(100).round(0)
    prof.columns = [names[c.replace("subscore_", "").replace("_quartile", "")] for c in prof.columns]
    prof.index = prof.index.map({0: "lowest third", 1: "middle third", 2: "highest third"})
    print(prof.to_string())

    print("\n== 5. Does access bring back disguised income? Spearman(means, sub-score), higher sub-score = worse")
    for k in NEW:
        print(f"  {names[k]}: {spearman(c.capacity_index[m], main[f'subscore_{k}'][m]):+.2f}  (old access sub-score: −0.52)")
    print(f"  inclusive mobility, variant unknown = yes: {spearman(c.capacity_index[m], runs['variant (unknown = yes)'].subscore_mobility[m]):+.2f}")

    print("\n== 6. Working hypothesis, pre-registered criteria (CLAUDE.md, 2026-10-02)")
    verdicts = {}
    for label, k, r in [("access to care", "access_care", main), ("inclusive mobility (unknown = no)", "mobility", main),
                        ("inclusive mobility (unknown = yes)", "mobility", runs["variant (unknown = yes)"])]:
        q4 = (r[f"subscore_{k}_quartile"] == 4)
        rows = []
        for d in ["MGP", *DEPS]:
            mm = m if d == "MGP" else m & (dep == d)
            low, high = mm & (tier == 0), mm & (tier == 2)
            ok = low.sum() >= MIN_PER_TERTILE and high.sum() >= MIN_PER_TERTILE
            gap = 100 * (q4[low].mean() - q4[high].mean()) if ok else np.nan
            rho = spearman(c.capacity_index[mm], r[f"subscore_{k}"][mm])
            rows.append({"area": d, "n low": int(low.sum()), "n high": int(high.sum()), "Q4 low %": round(100 * q4[low].mean(), 1),
                         "Q4 high %": round(100 * q4[high].mean(), 1), "gap pts": round(gap, 1), "rho": round(rho, 2),
                         "clearly unfavourable": bool(ok and gap >= GAP_PP and rho <= -RHO),
                         "clearly inverted": bool(ok and gap <= -GAP_PP and rho >= RHO), "assessed": ok})
        t = pd.DataFrame(rows).set_index("area")
        print(f"\n  {label}")
        print(t.to_string())
        deps = t.drop("MGP")
        fav = deps.index[deps["clearly unfavourable"]].tolist()
        inv = deps.index[deps["clearly inverted"]].tolist()
        mgp_gap = t.loc["MGP", "gap pts"]
        if len(fav) >= 2 and any(x != "93" for x in fav) and mgp_gap >= GAP_PP:
            v = "SUPPORTED"
        elif mgp_gap <= -GAP_PP or len(inv) >= 2:
            v = "INVALIDATED"
        else:
            v = "NUANCED"
        verdicts[label] = v
        print(f"  -> departments clearly unfavourable to the lowest third: {fav or 'none'}; clearly inverted: {inv or 'none'}; MGP gap {mgp_gap:+.1f} pts -> {v}")
    mob = {verdicts["inclusive mobility (unknown = no)"], verdicts["inclusive mobility (unknown = yes)"]}
    print(f"\n  VERDICT access to care: {verdicts['access to care']}")
    print(f"  VERDICT inclusive mobility: {mob.pop() if len(mob) == 1 else 'NUANCED (differs between the unknown = no / yes variants)'}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({n: r.cumulative_vulnerability_score for n, r in runs.items()}).assign(score3=ref3.cumulative_vulnerability_score).to_csv(OUT_DIR / "access_step4_scores.csv")


if __name__ == "__main__":
    main()
