"""Arrondissement-level tree-age context: average trunk circumference and

young-tree share, from opendata.paris.fr's citywide tree inventory.

Source: dataset "les-arbres" ("Arbres"), ~219k trees across Paris. There
is no planting-date field (checked directly — the schema only has
circonferenceencm, hauteurenm and a stadedeveloppement stage label), so
trunk circumference is used as the standard arboriculture proxy for age:
a wider trunk means an older tree. Aggregated server-side (Opendatasoft's
`group_by`/`select` aggregation functions) rather than downloading all
~219k raw points — this is per-arrondissement narrative context on
historical investment trajectory, not something to score a
neighborhood on, so it stays out of the IRIS-level sub-score model.

NOT joined to code_iris and NOT fed into the cumulative score — same
treatment as the life-expectancy/heatwave-mortality/school-AC context
facts already in ContextBanner.vue.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.io import save_geojson
from utils.opendatasoft import query_records

ARRONDISSEMENT_PATTERN = re.compile(r"PARIS (\d{1,2})(?:ER|E) ARRDT")


def arrondissement_to_insee(label: str) -> str | None:
    match = ARRONDISSEMENT_PATTERN.match(label or "")
    if not match:
        return None
    return f"751{int(match.group(1)):02d}"


def fetch_tree_stats() -> pd.DataFrame:
    overall = query_records(
        config.PARIS_OPENDATASOFT_BASE,
        config.TREES_DATASET_ID,
        where='arrondissement like "PARIS%"',
        select="arrondissement, avg(circonferenceencm) as avg_circumference_cm, count(*) as tree_count",
        group_by="arrondissement",
    )
    young = query_records(
        config.PARIS_OPENDATASOFT_BASE,
        config.TREES_DATASET_ID,
        where=f'arrondissement like "PARIS%" and stadedeveloppement="{config.TREE_YOUNG_STAGE_LABEL}"',
        select="arrondissement, count(*) as young_tree_count",
        group_by="arrondissement",
    )

    overall_df = pd.DataFrame(overall)
    young_df = pd.DataFrame(young)
    merged = overall_df.merge(young_df, on="arrondissement", how="left")
    merged["young_tree_count"] = merged["young_tree_count"].fillna(0)
    merged["pct_young_trees"] = merged["young_tree_count"] / merged["tree_count"]

    merged["insee_com"] = merged["arrondissement"].apply(arrondissement_to_insee)
    unmatched = merged[merged["insee_com"].isna()]
    if not unmatched.empty:
        print(f"[WARN] Could not parse arrondissement label for: {unmatched['arrondissement'].tolist()}")
    return merged.dropna(subset=["insee_com"])


def dissolve_arrondissements() -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)
    iris["insee_com"] = iris["insee_com"].astype(str)
    # The reference covers all of the MGP since Phase 5; this layer is Paris-only.
    iris = iris[iris["insee_com"].str[:2] == config.PARIS_DEP_CODE]
    arrondissements = iris.dissolve(by="insee_com", as_index=False).rename(columns={"nom_com": "nom_arrondissement"})
    return arrondissements[["insee_com", "nom_arrondissement", "geometry"]]


def main():
    stats = fetch_tree_stats()
    arrondissements = dissolve_arrondissements()
    result = arrondissements.merge(
        stats[["insee_com", "avg_circumference_cm", "tree_count", "pct_young_trees"]],
        on="insee_com",
        how="left",
    )
    save_geojson(
        result,
        config.DATA_PROCESSED / "tree_age_context_arrondissement.geojson",
        required_cols=["insee_com", "geometry"],
    )


if __name__ == "__main__":
    main()
