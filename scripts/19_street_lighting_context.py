"""Arrondissement-level street-lighting density context — Paris only.

Source: `street_lighting_iris.geojson` (script 13's already-collected,
IRIS-grain lamp count from opendata.paris.fr's "eclairage-public"
dataset). Feeds an optional "security/mobility" signal — kept as
narrative context rather than a real 5th sub-score: turning it into a
scored sub-score would
change the cumulative score's own framing from "X out of 4" to "X out
of 5" everywhere, resting on a single indicator that, unlike the other
four sub-scores, doesn't actually capture "inclusive mobility" (that's
already partly covered by the access sub-score's PMR/footway
indicators) — lighting alone is a nighttime-visibility proxy, not more.

Phase 5: the source itself is Paris-only (no Petite Couronne
equivalent), so this stays explicitly scoped to Paris's 20
arrondissements rather than attempting to cover all of MGP — filtering
to Paris up front, rather than aggregating across all communes and
hoping nulls survive, sidesteps a real trap: pandas' `.sum()` silently
treats an all-null group as 0, which would have made every Petite
Couronne commune look like a verified "0 lamps" instead of "not
measured by this source."

Aggregated here to arrondissement grain (area-weighted lamp density, not
a raw count average, so a few large low-density IRIS don't skew a small
arrondissement) for `ContextBanner.vue`'s narrative fact — same
treatment as tree age in script 18. Never joined to code_iris at this
grain, never scored.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.io import save_geojson

IRIS_LIGHTING_PATH = config.DATA_PROCESSED / "street_lighting_iris.geojson"


def dissolve_arrondissements() -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)
    iris["insee_com"] = iris["insee_com"].astype(str)
    iris = iris[iris["insee_com"].str[:2] == config.PARIS_DEP_CODE]
    arrondissements = iris.dissolve(by="insee_com", as_index=False).rename(columns={"nom_com": "nom_arrondissement"})
    return arrondissements[["insee_com", "nom_arrondissement", "geometry"]]


def compute_density_by_arrondissement() -> gpd.GeoDataFrame:
    lighting = gpd.read_file(IRIS_LIGHTING_PATH).to_crs(config.CRS_PROJECTED)
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED)
    iris["insee_com"] = iris["insee_com"].astype(str)
    iris = iris[iris["insee_com"].str[:2] == config.PARIS_DEP_CODE]

    lighting = lighting.merge(
        iris[[config.IRIS_JOIN_COLUMN, "insee_com"]], on=config.IRIS_JOIN_COLUMN, how="inner"
    )
    lighting["area_km2"] = iris.set_index(config.IRIS_JOIN_COLUMN).loc[lighting[config.IRIS_JOIN_COLUMN], "geometry"].area.values / 1_000_000

    grouped = lighting.groupby("insee_com").agg(
        total_lamps=("street_lighting_count", "sum"),
        total_area_km2=("area_km2", "sum"),
    ).reset_index()
    grouped["lamps_per_km2"] = grouped["total_lamps"] / grouped["total_area_km2"]
    return grouped[["insee_com", "lamps_per_km2"]]


def main():
    arrondissements = dissolve_arrondissements()
    density = compute_density_by_arrondissement()
    result = arrondissements.merge(density, on="insee_com", how="left")
    save_geojson(
        result,
        config.DATA_PROCESSED / "street_lighting_context_arrondissement.geojson",
        required_cols=["insee_com", "geometry"],
    )


if __name__ == "__main__":
    main()
