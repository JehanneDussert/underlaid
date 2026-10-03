"""Key figures shown on the site, computed from the published data.

The redesigned pages (home, method, address) quote figures in sentences:
"4 neighbourhoods combine all four", "77% in Seine-Saint-Denis", etc.
They are computed here from the very files the site publishes, never typed
by hand, so a quarterly pipeline run updates the text along with the map.
tests/test_pipeline.py checks this file against the published data.

Definitions (same as SCORING.md):
- inhabited neighbourhood: IRIS with at least 50 residents;
- "highly exposed": 2 or more of the 3 exposures (heat, air and noise,
  housing) in their worst quarter (decision of 3 October 2026: access to
  care is a separate axis, never counted in "highly exposed");
- thirds of means: tertiles of the adaptive-capacity index over the whole
  metropolis (capacity_class 0 = lowest third), script 26;
- access-to-care gap by département: share of the worst quarter for
  access to care among the lowest third of means minus the share among the
  highest third (pre-registered test, step 4 of the access rebuild).

Output: data/processed/key_figures.json (copied to frontend/public/data/
like the other published files). The data date is not repeated here: the
site reads it from last_updated.json, written at the very end of a run.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config

MIN_POPULATION = 50
DEPARTMENTS = ["75", "92", "93", "94"]
OUT = config.DATA_PROCESSED / "key_figures.json"


def pct(x: float) -> float:
    return round(100 * float(x), 1)


def main():
    score = gpd.read_file(config.DATA_PROCESSED / "vulnerability_score_iris.geojson").drop(columns="geometry")
    cap = pd.DataFrame(json.load(open(config.DATA_PROCESSED / "adaptive_capacity_iris.json", encoding="utf-8"))["iris"])
    df = score.merge(cap[["code_iris", "capacity_class", "capacity_index"]], on="code_iris", how="left")
    df["dep"] = df["code_iris"].str[:2]
    inhabited = df[df["population"] >= MIN_POPULATION]
    s = df["cumulative_vulnerability_score"]

    distribution = {str(k): int((s == k).sum()) for k in range(5)}
    distribution_inhabited = {str(k): int((inhabited["cumulative_vulnerability_score"] == k).sum()) for k in range(5)}
    at_max = inhabited[inhabited["cumulative_vulnerability_score"] == 4]
    at_three_plus = inhabited[inhabited["cumulative_vulnerability_score"] >= 3]

    with_means = df[df["capacity_class"].notna()]
    exposures = sum((with_means[f"subscore_{k}_quartile"] == 4).astype(int) for k in ["thermal", "pollution", "housing"])
    high = with_means[exposures >= 2]
    highly_exposed_lowest_third = {d: pct((high[high.dep == d]["capacity_class"] == 0).mean()) for d in DEPARTMENTS}
    spearman = round(with_means["capacity_index"].corr(with_means["cumulative_vulnerability_score"], method="spearman"), 2)

    worst_care = inhabited["subscore_access_care_quartile"] == 4
    care_gap = {}
    for d in DEPARTMENTS:
        x = inhabited[(inhabited.dep == d) & inhabited["capacity_class"].notna()]
        w = x["subscore_access_care_quartile"] == 4
        low, top = w[x["capacity_class"] == 0], w[x["capacity_class"] == 2]
        care_gap[d] = {
            "lowest_third_pct": pct(low.mean()) if len(low) else None,
            "highest_third_pct": pct(top.mean()) if len(top) else None,
            "lowest_third_n": int(len(low)),
            "highest_third_n": int(len(top)),
        }

    # Same gap at equal population density (pre-registered robustness
    # check, scripts/analysis/access_score4.py): within MGP density fifths
    # of inhabited IRIS with a means index, weighted by the smaller third,
    # fifths with at least 10 IRIS in both thirds only.
    iris_area = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris").area / 1e6
    dens = inhabited[inhabited["capacity_class"].notna()].copy()
    dens["density"] = dens["population"] / dens["code_iris"].map(iris_area)
    dens["fifth"] = pd.qcut(dens["density"], 5, labels=False)
    dens["worst"] = dens["subscore_access_care_quartile"] == 4
    care_gap_equal_density = {}
    for d in ["92", "94"]:
        y = dens[(dens.dep == d) & dens["subscore_access_care_quartile"].notna()]
        weighted, weight = 0.0, 0
        for _, g in y.groupby("fifth"):
            low, top = g[g["capacity_class"] == 0], g[g["capacity_class"] == 2]
            if len(low) >= 10 and len(top) >= 10:
                n = min(len(low), len(top))
                weighted += 100 * (low["worst"].mean() - top["worst"].mean()) * n
                weight += n
        care_gap_equal_density[d] = round(weighted / weight, 1) if weight else None

    wheelchair_gp_median = {d: round(float(inhabited[inhabited.dep == d]["gp_acc_no"].median()), 2) for d in DEPARTMENTS}

    example = df[(df["nom_com"] == "Drancy") & (df["nom_iris"] == "Économie 1")].iloc[0]
    example_out = {
        "code_iris": example["code_iris"],
        "name": example["nom_iris"],
        "commune": example["nom_com"],
        "score": int(example["cumulative_vulnerability_score"]),
        "worst_quarter": {k: bool(example[f"subscore_{k}_quartile"] == 4) for k in ["thermal", "pollution", "housing", "access_care"]},
    }

    out = {
        "n_iris": int(len(df)),
        "n_inhabited": int(len(inhabited)),
        "distribution": distribution,
        "distribution_inhabited": distribution_inhabited,
        "at_max": [{"code_iris": r.code_iris, "name": r.nom_iris, "commune": r.nom_com} for r in at_max.itertuples()],
        "n_three_plus_inhabited": int(len(at_three_plus)),
        "three_plus_by_department": {d: int((at_three_plus.dep == d).sum()) for d in DEPARTMENTS},
        "highly_exposed_lowest_third_pct": highly_exposed_lowest_third,
        "spearman_means_exposure": spearman,
        "worst_access_care_pct": {d: pct(worst_care[inhabited.dep == d].mean()) for d in DEPARTMENTS},
        "access_care_by_means": care_gap,
        "access_care_gap_equal_density": care_gap_equal_density,
        "wheelchair_gp_median": wheelchair_gp_median,
        "example": example_out,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
