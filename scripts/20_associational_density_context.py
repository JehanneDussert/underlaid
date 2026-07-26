"""Commune-level associational density context (RNA), across the 4 MGP
departments.

Source: data.iledefrance.fr, "Repertoire National des Associations -
Ile-de-France" (mirrors the Ministry of the Interior's RNA for the
region). Counts currently-active associations (dissolution_date is
null) headquartered in each commune, via com_code_asso — the official
commune code, which already matches this project's insee_com convention
directly (751xx for Paris arrondissements, normal 5-digit codes for
every other commune), no parsing needed.

Phase 5: this was originally an "arrondissement" fact (Paris only, 20
rows) — dissolving by insee_com already produces the right grain for
92/93/94 too (one row per real commune, since those departments aren't
subdivided the way Paris is), so no dissolve-logic change was needed,
only renaming "arrondissement" to "commune" throughout since most rows
are now real communes, not arrondissements.

A deliberately cautious, never-scored context fact: originally
reported as density per km2 only, since no clean per-commune population
figure was available at the time. Now that script 21 provides IRIS-level
population (summed here per commune), both are reported — per-1,000-
inhabitants as the primary, more standard associational-density metric,
and per-km2 kept alongside it since the Bois de Vincennes/Boulogne
caveat below is still a real, separate distortion that per-capita alone
doesn't fix (a commune can have a normal population but still have its
area caveat). Context only — never joined to code_iris, never scored,
and deliberately paired with a caveat in the frontend copy that
higher/lower density says nothing about a neighborhood's civic health on
its own (headquarters location != where members live or activity happens).

Electoral abstention (the other Priority 4 idea) was investigated and
NOT pursued: the only accessible dataset for the 2026 municipales results
was a third-party commune's Opendatasoft mirror, not a confirmed direct
Ministry of the Interior source — not solid enough footing for something
this politically sensitive, especially under this project's own
"descriptive, never accusatory" principle.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.io import save_geojson
from utils.opendatasoft import query_records

IDF_BASE = "https://data.iledefrance.fr"


def fetch_association_counts() -> pd.DataFrame:
    dept_filter = " or ".join(f'dep_code="{d}"' for d in config.MGP_DEP_CODES)
    records = query_records(
        IDF_BASE,
        config.RNA_DATASET_ID,
        where=f"({dept_filter}) and dissolution_date is null",
        select="com_code_asso, count(*) as active_association_count",
        group_by="com_code_asso",
    )
    df = pd.DataFrame(records).rename(columns={"com_code_asso": "insee_com"})
    return df


def dissolve_communes() -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)
    iris["insee_com"] = iris["insee_com"].astype(str)
    communes = iris.dissolve(by="insee_com", as_index=False).rename(columns={"nom_com": "nom_commune"})
    return communes[["insee_com", "nom_commune", "geometry"]]


def fetch_population_by_commune() -> pd.DataFrame:
    population = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[[config.IRIS_JOIN_COLUMN, "insee_com"]]
    iris["insee_com"] = iris["insee_com"].astype(str)
    merged = population.merge(iris, on=config.IRIS_JOIN_COLUMN, how="left")
    return merged.groupby("insee_com")["population"].sum().reset_index()


def main():
    counts = fetch_association_counts()
    communes = dissolve_communes()
    population_by_commune = fetch_population_by_commune()

    result = communes.merge(counts, on="insee_com", how="left").merge(population_by_commune, on="insee_com", how="left")
    result_proj = result.to_crs(config.CRS_PROJECTED)
    result["area_km2"] = result_proj.geometry.area / 1_000_000
    result["associations_per_km2"] = result["active_association_count"] / result["area_km2"]
    result["associations_per_1000_inhabitants"] = result["active_association_count"] / (result["population"] / 1000)

    save_geojson(
        result[[
            "insee_com", "nom_commune", "active_association_count",
            "associations_per_km2", "associations_per_1000_inhabitants",
            "geometry",
        ]],
        config.DATA_PROCESSED / "associational_density_context_commune.geojson",
        required_cols=["insee_com", "geometry"],
    )


if __name__ == "__main__":
    main()
