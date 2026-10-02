"""Community pharmacies (officines) in Île-de-France.

Supply side of the pharmacy E2SFCA (script 31). Source: FINESS extract
of geolocated establishments (Etalab, Licence Ouverte 2.0), category 620
"Pharmacie d'Officine", already geocoded (Lambert-93) by the publisher.
Capacity: 1 per pharmacy — no open data on staff or opening hours.

Whole region kept (edge effect), same as script 27.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.download import download_file, find_datagouv_resource
from utils.io import save_geojson

RAW_PATH = config.DATA_RAW / "finess" / "etalab_cs1100507.csv"
OUT_PATH = config.DATA_PROCESSED / "access" / "pharmacy_sites_idf.geojson"

# structureet line layout (etalab_cs1100507 documentation): field 2 is
# nofinesset, 4 the short name, 14 the department, 19 the category.
F_ID, F_NAME, F_DEP, F_CATEGORY = 1, 3, 13, 18


def main():
    if not RAW_PATH.exists():
        download_file(find_datagouv_resource(config.FINESS_DATASET_SLUG, config.FINESS_GEO_RESOURCE_TITLE), RAW_PATH)
    structures, coords = [], {}
    with open(RAW_PATH, encoding="utf-8", errors="replace") as f:
        for line in f:
            row = line.rstrip("\n").split(";")
            if row[0] == "structureet" and row[F_CATEGORY] == config.FINESS_PHARMACY_CATEGORY and row[F_DEP] in config.IDF_DEP_CODES:
                structures.append((row[F_ID], row[F_NAME], row[F_DEP]))
            elif row[0] == "geolocalisation":
                coords[row[1]] = (row[2], row[3])
    df = pd.DataFrame(structures, columns=["finess", "name", "dep"])
    df["x"] = pd.to_numeric(df.finess.map(lambda k: coords.get(k, (None, None))[0]), errors="coerce")
    df["y"] = pd.to_numeric(df.finess.map(lambda k: coords.get(k, (None, None))[1]), errors="coerce")
    missing = df.x.isna().sum()
    print(f"{len(df)} pharmacies in Île-de-France, {missing} without coordinates (dropped)")
    df = df.dropna(subset=["x", "y"])
    df["capacity"] = 1.0
    df["site_id"] = "ph" + df.finess
    gdf = gpd.GeoDataFrame(df.drop(columns=["x", "y"]), geometry=gpd.points_from_xy(df.x, df.y), crs=config.CRS_PROJECTED)
    print(gdf.groupby("dep").size().to_string())
    save_geojson(gdf.to_crs(config.CRS_LATLON), OUT_PATH, required_cols=["site_id", "capacity"])


if __name__ == "__main__":
    main()
