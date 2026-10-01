"""Download and normalize the social position index (IPS) of MGP schools.

Source: data.education.gouv.fr (Opendatasoft Explore API v2.1), datasets
"fr-en-ips-ecoles-ap2022" (primary schools) and "fr-en-ips-colleges-ap2023"
(middle schools). Each school is geolocated, assigned to its enclosing
IRIS, and IPS values are averaged per IRIS — separately for each school
level, since primary/middle school catchment areas differ.

Schema notes confirmed by inspection: both datasets key schools by `uai`
and filter by `code_insee_de_la_commune` (already using Paris's per-
arrondissement codes, e.g. "75103" — same format as our IRIS reference).
The colleges dataset carries its own `position` (geo_point_2d); the
ecoles dataset does not, so it is geolocated via a join on `uai` against
the "fr-en-adresse-et-geolocalisation-etablissements-premier-et-second-
degre" directory dataset, which has `numero_uai`/`latitude`/`longitude`.

Intended use (step 2): enriches the "access to services" sub-score with a
socio-economic / school-segregation signal, complementary to income.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson
from utils.opendatasoft import dept_where_clause, query_records

SCHOOL_DIRECTORY_DATASET_ID = "fr-en-adresse-et-geolocalisation-etablissements-premier-et-second-degre"

MGP_COMMUNE_WHERE = dept_where_clause("code_insee_de_la_commune", config.MGP_DEP_CODES)


def fetch_ips_records(dataset_id: str) -> pd.DataFrame:
    records = query_records(config.EDUCATION_OPENDATASOFT_BASE, dataset_id, where=MGP_COMMUNE_WHERE)
    return pd.json_normalize(records)


def fetch_school_directory() -> pd.DataFrame:
    records = query_records(
        config.EDUCATION_OPENDATASOFT_BASE,
        SCHOOL_DIRECTORY_DATASET_ID,
        where=dept_where_clause("code_commune", config.MGP_DEP_CODES),
        select="numero_uai,latitude,longitude",
    )
    return pd.json_normalize(records)


def to_points(df: pd.DataFrame, lon_col: str, lat_col: str) -> gpd.GeoDataFrame:
    df = df.dropna(subset=[lon_col, lat_col])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon_col], df[lat_col]), crs=config.CRS_LATLON)


def average_ips_per_iris(points: gpd.GeoDataFrame, iris: gpd.GeoDataFrame, out_col: str) -> pd.DataFrame:
    joined = join_points_to_iris(points.to_crs(iris.crs), iris, config.IRIS_JOIN_COLUMN)
    joined["ips"] = pd.to_numeric(joined["ips"], errors="coerce")
    joined = joined.dropna(subset=[config.IRIS_JOIN_COLUMN, "ips"])
    return joined.groupby(config.IRIS_JOIN_COLUMN)["ips"].mean().rename(out_col).reset_index()


def geolocate_by_uai(ips_df: pd.DataFrame, directory_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Coordinates from the national school directory, joined on the UAI
    code. Used for both datasets: the primary-school IPS never carried
    coordinates, and the middle-school IPS dropped its `position` field
    when it was republished on 2026-09-01 (found by a cold pipeline run —
    the quarterly workflow would have failed on it right after script 21).
    """
    merged = ips_df.merge(directory_df, left_on="uai", right_on="numero_uai", how="inner")
    return to_points(merged, "longitude", "latitude")


def build_ecoles_points(directory_df: pd.DataFrame) -> gpd.GeoDataFrame:
    return geolocate_by_uai(fetch_ips_records(config.SOCIAL_INDEX_SCHOOLS_DATASET_ID), directory_df)


def build_colleges_points(directory_df: pd.DataFrame) -> gpd.GeoDataFrame:
    return geolocate_by_uai(fetch_ips_records(config.SOCIAL_INDEX_MIDDLE_SCHOOLS_DATASET_ID), directory_df)


def main():
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)

    directory_df = fetch_school_directory()
    ecoles_points = build_ecoles_points(directory_df)
    colleges_points = build_colleges_points(directory_df)

    ecoles_ips = average_ips_per_iris(ecoles_points, iris, "social_index_schools")
    colleges_ips = average_ips_per_iris(colleges_points, iris, "social_index_middle_schools")

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]] \
        .merge(ecoles_ips, on=config.IRIS_JOIN_COLUMN, how="left") \
        .merge(colleges_ips, on=config.IRIS_JOIN_COLUMN, how="left")

    result = result.to_crs(config.CRS_LATLON)
    save_geojson(result, config.DATA_PROCESSED / "social_index_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
