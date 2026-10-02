"""Audit: does the DPE's old small-dwelling penalty inflate the housing sub-score?

One-off analysis, nothing written to the pipeline outputs. Since 1 July
2024 (arrêté of 25 March 2024), DPE class thresholds are adjusted for
dwellings under 40 m², which the 2021 method penalised (fixed hot-water
and heating needs spread over a small surface). ADEME's dataset has no
field saying whether a label was recalculated.

Answer (2026-10-02): the published labels are already on the 2024 scale.
Reclassified from their own consumption and emissions with the official
thresholds (dpe_2024_thresholds.py), pre-reform small-dwelling
certificates match the 2024 rule for 99.8% of them (the 2021 rule:
92.9%). So the two counterfactuals of step 3 below do NOT measure a bias
— they drop certificates that are already correct. They're kept only to
reproduce the first (mistaken) reading; the exact relabelling, done with
dpe_2024_thresholds.py, changes 0.06% of certificates (see SCORING.md,
"Known caveats").

Steps:
1. fetch the MGP certificates (same source and filter as script 10) with
   surface, issue date and building type;
2. F/G share by surface band (< 30, 30-40, 40-70, > 70 m²), department,
   and issued before / after 1 July 2024;
3. counterfactual F/G share per IRIS, two versions:
   - "over_40": certificates of 40 m² and more only;
   - "corrected_small": >= 40 m² plus < 40 m² certificates issued from
     1 July 2024 (already under the corrected thresholds) — the pre-reform
     small-dwelling certificates are left out, not relabelled, since the
     corrected thresholds aren't reproduced here;
4. housing sub-score and cumulative score recomputed with script 11's own
   functions on each counterfactual, compared with the published score.

Usage: python scripts/analysis/dpe_small_surfaces.py [--refetch]
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import requests

import config
from utils.download import DEFAULT_TIMEOUT

RAW = config.DATA_RAW / "energy_performance" / "dpe_mgp_with_surface.parquet"
OUT_DIR = config.DATA_INTERIM / "analysis"
LINES_URL = f"{config.ADEME_OPENDATASOFT_BASE}/data-fair/api/v1/datasets/{config.ENERGY_PERFORMANCE_DATASET_ID}/lines"
FIELDS = ("etiquette_dpe,coordonnee_cartographique_x_ban,coordonnee_cartographique_y_ban,code_insee_ban,"
          "surface_habitable_logement,date_etablissement_dpe,type_batiment,numero_dpe,numero_dpe_remplace,"
          "conso_5_usages_par_m2_ep,emission_ges_5_usages_par_m2")
REFORM_DATE = "2024-07-01"


def fetch() -> pd.DataFrame:
    params = {"qs": " OR ".join(f"code_insee_ban:{d}*" for d in config.MGP_DEP_CODES), "select": FIELDS, "size": 10_000}
    url, rows = LINES_URL, []
    session = requests.Session()
    while url:
        for attempt in range(6):  # ADEME sometimes cuts a page mid-transfer (ChunkedEncodingError)
            try:
                r = session.get(url, params=params if url == LINES_URL else None, timeout=DEFAULT_TIMEOUT * 3)
                r.raise_for_status()
                payload = r.json()
                break
            except (requests.RequestException, ValueError) as exc:
                if attempt == 5:
                    raise
                print(f"  retry after {exc.__class__.__name__}", flush=True)
                time.sleep(10 * (attempt + 1))
        rows.extend(payload.get("results", []))
        url = payload.get("next")
        if len(rows) % 200_000 < 10_000:
            print(f"  {len(rows)} certificates", flush=True)
    df = pd.DataFrame(rows)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(RAW, index=False)
    return df


BANDS = [0, 30, 40, 70, float("inf")]
BAND_LABELS = ["< 30 m²", "30-40 m²", "40-70 m²", "> 70 m²"]


def load() -> "gpd.GeoDataFrame":
    import geopandas as gpd

    from utils.geo import join_points_to_iris, load_iris_reference

    df = pd.read_parquet(RAW)
    df = df.dropna(subset=["coordonnee_cartographique_x_ban", "coordonnee_cartographique_y_ban"])
    df["dep"] = df.code_insee_ban.astype(str).str[:2]
    df["surface"] = pd.to_numeric(df.surface_habitable_logement, errors="coerce")
    df["band"] = pd.cut(df.surface, BANDS, right=False, labels=BAND_LABELS)
    df["after_reform"] = df.date_etablissement_dpe.astype(str) >= REFORM_DATE
    df["fg"] = df.etiquette_dpe.isin(config.ENERGY_PERFORMANCE_POOR_CLASSES)
    points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.coordonnee_cartographique_x_ban, df.coordonnee_cartographique_y_ban), crs=config.CRS_PROJECTED)
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    return join_points_to_iris(points, iris, config.IRIS_JOIN_COLUMN).dropna(subset=[config.IRIS_JOIN_COLUMN])


def describe(d: pd.DataFrame) -> None:
    print(f"\n{len(d):,} certificates joined to MGP IRIS; surface missing for {d.surface.isna().mean():.1%}")
    small = d.surface < 40
    print(f"Under 40 m²: {small.mean():.1%} of certificates; of those, issued before {REFORM_DATE}: {(~d.after_reform[small]).mean():.1%}")
    print("\nShare of certificates by surface band, per department (%)")
    print((pd.crosstab(d.dep, d.band, normalize="index") * 100).round(1).to_string())
    print("\nF/G share by surface band and department (%), all certificates")
    print((d.pivot_table(index="dep", columns="band", values="fg", aggfunc="mean", observed=False) * 100).round(1).to_string())
    print("\nF/G share under 40 m², before vs after the reform (%), per department")
    s = d[small]
    print((s.pivot_table(index="dep", columns="after_reform", values="fg", aggfunc="mean") * 100).round(1)
          .rename(columns={False: "before 2024-07-01", True: "from 2024-07-01"}).to_string())
    print("\nF/G share per department: all / 40 m² and more only / corrected_small")
    keep = (d.surface >= 40) | (small & d.after_reform)
    print(pd.DataFrame({
        "all": d.groupby("dep").fg.mean(), "over_40": d[d.surface >= 40].groupby("dep").fg.mean(),
        "corrected_small": d[keep].groupby("dep").fg.mean(),
    }).mul(100).round(1).to_string())


def rescore(d: pd.DataFrame) -> None:
    import importlib

    s11 = importlib.import_module("11_compute_vulnerability_score")
    base = s11.build_dataset()
    variants = {
        "all (refetched)": d,
        "over_40": d[d.surface >= 40],
        "corrected_small": d[(d.surface >= 40) | ((d.surface < 40) & d.after_reform)],
    }
    import geopandas as gpd

    published = gpd.read_file(config.DATA_PROCESSED / "vulnerability_score_iris.geojson").set_index("code_iris")
    inhabited = published.population.fillna(0) >= 50
    paris = published.index.str[:2] == "75"
    results = {}
    for name, sub in variants.items():
        fg = sub.groupby(config.IRIS_JOIN_COLUMN).fg.agg(["mean", "size"]).rename(columns={"mean": "pct_dpe_fg", "size": "dpe_sample_size"})
        df = base.drop(columns=["pct_dpe_fg", "dpe_sample_size"]).merge(fg, left_on="code_iris", right_index=True, how="left")
        df = s11.compute_cumulative_score(s11.compute_subscores(s11.build_indicators(df)))
        results[name] = df.set_index("code_iris")
    print("\nHousing sub-score in worst quartile, share of inhabited IRIS per department (%)")
    print(pd.DataFrame({n: (r.subscore_housing_quartile == 4)[inhabited].groupby(r.index[inhabited].str[:2]).mean() * 100
                        for n, r in results.items()}).round(1).to_string())
    print("\nCumulative score, inhabited IRIS (0/1/2/3)")
    for n, r in results.items():
        print(f"  {n:18s}", r.cumulative_vulnerability_score[inhabited].value_counts().sort_index().to_dict())
    ref = results["all (refetched)"]
    print(f"\nRefetched baseline vs published score: {(ref.cumulative_vulnerability_score != published.cumulative_vulnerability_score.reindex(ref.index)).sum()} IRIS differ")
    for n in ("over_40", "corrected_small"):
        r = results[n]
        hi_before = (ref.cumulative_vulnerability_score >= 2) & inhabited.reindex(ref.index)
        hi_after = (r.cumulative_vulnerability_score >= 2) & inhabited.reindex(r.index)
        p = ref.index.str[:2] == "75"
        print(f"\n{n}: Paris IRIS at 2-3 before {int((hi_before & p).sum())}, after {int((hi_after & p).sum())}; "
              f"leave 2-3: {int((hi_before & ~hi_after & p).sum())}, enter: {int((~hi_before & hi_after & p).sum())}; "
              f"at 3/3 before {int(((ref.cumulative_vulnerability_score == 3) & inhabited & p).sum())}, after {int(((r.cumulative_vulnerability_score == 3) & inhabited & p).sum())}")
        for dep in ("92", "93", "94"):
            m = ref.index.str[:2] == dep
            print(f"   {dep}: at 2-3 before {int((hi_before & m).sum())}, after {int((hi_after & m).sum())}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({n: r.cumulative_vulnerability_score for n, r in results.items()}).to_csv(OUT_DIR / "dpe_small_surfaces_scores.csv")


if __name__ == "__main__":
    if "--refetch" in sys.argv or not RAW.exists():
        df = fetch()
        print(f"Saved {len(df)} certificates to {RAW}")
    d = load()
    describe(d)
    rescore(d)
