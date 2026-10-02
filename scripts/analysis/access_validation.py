"""Step 3 of the access rebuild: validation of the E2SFCA indicators.

Reads data/processed/access/access_e2sfca_iris.csv (script 32). Never
looks at residents' means (working hypothesis, CLAUDE.md): only
distributions, departments, the DREES APL, extremes and sensitivity.

Usage: python scripts/analysis/access_validation.py path/to/apl_mg.xlsx
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

OUT_DIR = config.DATA_INTERIM / "analysis"
MAIN = ["gp_std", "gp_acc_no", "gp_acc_yes", "gp_gap_no", "gp_gap_yes", "pharmacy_std"]


def spearman(a: pd.Series, b: pd.Series) -> float:
    ok = a.notna() & b.notna()
    return a[ok].rank().corr(b[ok].rank())


def load() -> pd.DataFrame:
    acc = pd.read_csv(config.DATA_PROCESSED / "access" / "access_e2sfca_iris.csv", dtype={"code_iris": str})
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "nom_iris", "nom_com", "insee_com"]]
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")[["code_iris", "population"]]
    d = acc.merge(iris, on="code_iris").merge(pop, on="code_iris")
    d["insee_com"] = d.insee_com.astype(str).str.zfill(5)
    d["dep"] = d.code_iris.str[:2]
    return d[d.population.fillna(0) >= 50].copy()


def distributions(d: pd.DataFrame) -> None:
    print("== Distributions (inhabited IRIS)")
    rows = []
    for c in MAIN:
        s = d[c].dropna()
        z = (s - s.mean()) / s.std()
        rows.append({"indicator": c, "n": len(s), "min": s.min(), "p25": s.quantile(.25), "median": s.median(),
                     "p75": s.quantile(.75), "max": s.max(), "skew": s.skew(), "max|z|": z.abs().max(),
                     "share_at_min": (s == s.min()).mean(), "share_>=0.98": (s >= 0.98).mean() if "gap" in c else np.nan})
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("\n== Worst quartile (lowest access) share by department (%)")
    t = {}
    for c in MAIN:
        q = d[c] <= d[c].quantile(0.25)
        t[c] = (q.groupby(d.dep).mean() * 100).round(1)
    print(pd.DataFrame(t).to_string())
    print("\n== Median by department")
    print(d.groupby("dep")[MAIN].median().round(3).to_string())
    print("\n== Bias checks: worst-quartile share by share of imputed grid residents and by number of grid cells (%)")
    d["imp_band"] = pd.cut(d.pop_imputed_share.fillna(0), [-0.01, 0.0, 0.2, 1.0], labels=["0", "0-20%", ">20%"])
    d["cell_band"] = pd.cut(d.n_cells.fillna(0), [-1, 0, 3, 10, 1000], labels=["fallback", "1-3", "4-10", ">10"])
    for band in ("imp_band", "cell_band"):
        t = {c: ((d[c] <= d[c].quantile(0.25)).groupby(d[band], observed=True).mean() * 100).round(1) for c in ("gp_std", "gp_gap_no", "pharmacy_std")}
        n = d.groupby(band, observed=True).size().rename("n")
        print(pd.concat([n, pd.DataFrame(t)], axis=1).to_string())


def drees(d: pd.DataFrame, apl_path: str) -> None:
    apl = pd.read_excel(apl_path, sheet_name="APL 2024", skiprows=8, dtype={"Code commune INSEE": str})
    apl = apl.rename(columns={apl.columns[0]: "insee_com", apl.columns[2]: "apl"})[["insee_com", "apl"]].dropna()
    w = d.population
    com = (d[["gp_std"]].mul(w, axis=0).groupby(d.insee_com).sum().div(w.groupby(d.insee_com).sum(), axis=0)
           .join(d.groupby("insee_com").agg(nom=("nom_com", "first"), dep=("dep", "first"), pop=("population", "sum"))))
    m = com.join(apl.set_index("insee_com"), how="inner")
    print(f"\n== Commune level vs DREES APL 2024 (GPs): {len(m)} communes / arrondissements")
    print(f"Spearman {spearman(m.gp_std, m.apl):.2f}, Pearson {m.gp_std.corr(m.apl):.2f}")
    for dep, g in m.groupby("dep"):
        print(f"  {dep}: n {len(g)}, Spearman {spearman(g.gp_std, g.apl):.2f}")
    m["rank_gap"] = m.gp_std.rank(pct=True) - m.apl.rank(pct=True)
    cols = ["nom", "dep", "gp_std", "apl", "rank_gap"]
    print("Largest gaps (ours ranks higher than APL):")
    print(m.sort_values("rank_gap", ascending=False)[cols].head(6).round(2).to_string())
    print("Largest gaps (ours ranks lower than APL):")
    print(m.sort_values("rank_gap")[cols].head(6).round(2).to_string())
    m.to_csv(OUT_DIR / "access_vs_apl_commune.csv")


def extremes(d: pd.DataFrame) -> None:
    cols = ["code_iris", "nom_com", "nom_iris", "population", "gp_std", "gp_acc_no", "gp_gap_no", "pharmacy_std"]
    for c in ("gp_std", "gp_gap_no", "pharmacy_std"):
        print(f"\n== Extremes of {c} (5 lowest, 5 highest)")
        s = d.dropna(subset=[c]).sort_values(c)
        print(pd.concat([s.head(5), s.tail(5)])[cols].round(3).to_string(index=False))


def sensitivity(d: pd.DataFrame) -> None:
    print("\n== Sensitivity")
    for base in ("gp_std", "pharmacy_std", "gp_gap_no", "gp_gap_yes"):
        flips = d[base + "_q4_flip"].astype(bool)
        print(f"  {base}: {flips.sum()} IRIS ({flips.mean():.1%}) change worst-quartile status between -5 and +5 min bounds; "
              f"Spearman small/large {spearman(d[base + '_small'], d[base + '_large']):.2f}")
    for a, b, label in [("gp_std", "gp_std_pm", "morning vs evening, standard"),
                        ("gp_gap_no", "gp_gap_no_pm", "morning vs evening, gap (unknown = no)"),
                        ("gp_gap_no", "gp_gap_no_slow", "gap: main vs reduced walking speed (unknown = no)"),
                        ("gp_acc_no", "gp_acc_no_slow", "main vs reduced speed, accessible (unknown = no)"),
                        ("gp_gap_no", "gp_gap_yes", "gap: unknown = no vs unknown = yes"),
                        ("gp_std", "gp_gap_no", "GP access vs gap (independence of the 2 indicators)"),
                        ("gp_std", "pharmacy_std", "GP vs pharmacy access")]:
        qa, qb = d[a] <= d[a].quantile(.25), d[b] <= d[b].quantile(.25)
        print(f"  {label}: Spearman {spearman(d[a], d[b]):.2f}; same worst-quartile status {(qa == qb).mean():.1%}")


def stability_criterion(d: pd.DataFrame) -> None:
    """Decision of 2026-10-02: the gap is scored only if its share of IRIS
    changing worst-quartile status at -5/+5 min is at most that of GPs."""
    gp = d["gp_std_q4_flip"].astype(bool).mean()
    print("\n== Stability criterion for the inclusive-mobility gap (inhabited IRIS)")
    print(f"  GP access: {gp:.1%} of IRIS enter or leave the worst quarter between -5 and +5 min")
    for v in ("no", "yes"):
        g = d[f"gp_gap_{v}_q4_flip"].astype(bool).mean()
        print(f"  gap (unknown = {v}): {g:.1%} -> {'meets' if g <= gp else 'fails'} the criterion")


def density_check(d: pd.DataFrame) -> None:
    """Does neighbourhood size still matter at equal population density?"""
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].to_crs(config.CRS_PROJECTED)
    iris["area_km2"] = iris.area / 1e6
    d = d.merge(iris[["code_iris", "area_km2"]], on="code_iris")
    d["density"] = d.population / d.area_km2
    d["density_band"] = pd.qcut(d.density, 5, labels=["Q1 least dense", "Q2", "Q3", "Q4", "Q5 densest"])
    d["size_band"] = d.groupby("density_band", observed=True).area_km2.transform(
        lambda a: pd.qcut(a, 2, labels=["smaller half", "larger half"]).astype(str))
    print("\n== Worst-quarter share (%) by density fifth, and within it by IRIS area (smaller / larger half)")
    for c in ("gp_std", "pharmacy_std"):
        q = d[c] <= d[c].quantile(0.25)
        t = q.groupby([d.density_band, d.size_band], observed=True).mean().unstack().mul(100).round(1)
        t["all"] = q.groupby(d.density_band, observed=True).mean().mul(100).round(1)
        print(f"  {c}:")
        print(t.to_string())
    for c in ("gp_std", "pharmacy_std"):
        ok = d[c].notna()
        rd, ra, rc = d.density[ok].rank(), d.area_km2[ok].rank(), d[c][ok].rank()
        res_a = ra - np.polyval(np.polyfit(rd, ra, 1), rd)
        res_c = rc - np.polyval(np.polyfit(rd, rc, 1), rd)
        print(f"  {c}: Spearman with density {spearman(d[c], d.density):.2f}; with area {spearman(d[c], d.area_km2):.2f}; "
              f"partial with area at equal density {np.corrcoef(res_a, res_c)[0, 1]:.2f}")


def maps(d: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "geometry"]].merge(d, on="code_iris", how="left")
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))
    for ax, (c, title) in zip(axes, [("gp_std", "GPs (standard), per 10,000 age-weighted residents"),
                                     ("gp_gap_no", "Inclusive-mobility gap (accessible / standard, unknown = no)"),
                                     ("pharmacy_std", "Pharmacies within 15 min walk, per 10,000 residents")]):
        iris.plot(column=c, ax=ax, cmap="viridis", scheme="quantiles", k=5, legend=True, missing_kwds={"color": "lightgrey"},
                  legend_kwds={"loc": "lower left", "fontsize": 8}, linewidth=0)
        ax.set_title(title, fontsize=10)
        ax.set_axis_off()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "access_maps.png", dpi=110, bbox_inches="tight")
    print(f"\nMaps: {OUT_DIR / 'access_maps.png'}")


def main():
    d = load()
    distributions(d)
    drees(d, sys.argv[1])
    extremes(d)
    sensitivity(d)
    stability_criterion(d)
    density_check(d)
    maps(d)


if __name__ == "__main__":
    main()
