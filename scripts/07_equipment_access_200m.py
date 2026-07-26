"""Download and normalize equipment-access times, aggregated from 200m grid cells to IRIS.

Source: data.gouv.fr dataset "donnees-sur-la-localisation-et-lacces-de-la-
population-aux-equipements" (INSEE, built on BPE + Metric-OSRM). Parquet
files partitioned by region; this script picks the Ile-de-France partition
(reg=11) via the data.gouv.fr resource API rather than a hardcoded URL,
since the dataset is refreshed with every new BPE edition.

Actual schema (confirmed by inspecting the downloaded file): one row per
(200m grid cell x specific equipment type), with columns X/Y (cell
centroid, EPSG:3035), pop (cell population, repeated across its rows),
domaine (BPE domain letter A-G, matching BPE_DOMAINS_OF_INTEREST) and
duree (minutes to the nearest equipment of that specific type). The
dataset's own `depcom` column uses Paris's pre-2019 single-commune code
("75056") rather than the per-arrondissement codes (751xx) used by our
IRIS reference, so cells are matched to IRIS by spatial join on X/Y
instead of by attribute join. `depcom` is a normal 5-digit INSEE commune
code for every other commune though (department = its first 2 digits),
so a plain dept-prefix filter covers Paris's legacy code and every real
Petite Couronne commune code uniformly — no need to enumerate all ~131
commune codes individually.

For each domain of interest, we take the minimum duree across equipment
types per cell (time to the nearest equipment in that domain), then
aggregate to IRIS with a population-weighted mean.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.download import download_file, fetch_datagouv_resource_urls
from utils.geo import join_points_to_iris, load_iris_reference
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "equipment_access_200m"


def download() -> Path:
    resources = fetch_datagouv_resource_urls(config.EQUIPMENT_ACCESS_DATASET_SLUG)
    match = next(
        (r for r in resources if r["url"] and f"reg{config.IDF_REGION_CODE}" in r["url"].lower()),
        None,
    )
    if match is None:
        raise RuntimeError(
            f"No Ile-de-France (reg={config.IDF_REGION_CODE}) resource found among: "
            f"{[r['title'] for r in resources]}"
        )
    dest = RAW_DIR / Path(match["url"]).name
    return download_file(match["url"], dest)


def load_mgp_rows(parquet_path: Path) -> pd.DataFrame:
    columns = ["X", "Y", "depcom", "domaine", "typeeq_id", "duree", "pop"]
    df = pd.read_parquet(parquet_path, columns=columns)
    return df[df["depcom"].astype(str).str[:2].isin(config.MGP_DEP_CODES)]


def nearest_duree_per_domain(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["domaine"].isin(config.BPE_DOMAINS_OF_INTEREST)]
    nearest = df.groupby(["X", "Y", "domaine"], as_index=False)["duree"].min()
    wide = nearest.pivot_table(index=["X", "Y"], columns="domaine", values="duree").reset_index()
    wide.columns = [f"access_minutes_domain_{c}" if c not in ("X", "Y") else c for c in wide.columns]
    return wide


def normalize(df: pd.DataFrame) -> gpd.GeoDataFrame:
    pop_per_cell = df.drop_duplicates(subset=["X", "Y"])[["X", "Y", "pop"]]
    wide = nearest_duree_per_domain(df).merge(pop_per_cell, on=["X", "Y"], how="left")

    points = gpd.GeoDataFrame(wide, geometry=gpd.points_from_xy(wide["X"], wide["Y"]), crs="EPSG:3035")
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)
    joined = join_points_to_iris(points.to_crs(iris.crs), iris, config.IRIS_JOIN_COLUMN)
    joined = joined.dropna(subset=[config.IRIS_JOIN_COLUMN])

    access_cols = [c for c in wide.columns if c.startswith("access_minutes_domain_")]
    for col in access_cols:
        joined[f"_weighted_{col}"] = joined[col] * joined["pop"]

    grouped = joined.groupby(config.IRIS_JOIN_COLUMN).agg(
        **{f"_weighted_{c}": (f"_weighted_{c}", "sum") for c in access_cols},
        pop=("pop", "sum"),
    )
    for col in access_cols:
        grouped[col] = grouped[f"_weighted_{col}"] / grouped["pop"]
    grouped = grouped[access_cols].reset_index()

    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(grouped, on=config.IRIS_JOIN_COLUMN, how="left")
    return result.to_crs(config.CRS_LATLON)


def main():
    parquet_path = download()
    df = load_mgp_rows(parquet_path)
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "equipment_access_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
