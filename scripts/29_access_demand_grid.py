"""Demand for the E2SFCA: residents on INSEE's 200 m grid, Île-de-France.

Source: Filosofi 2021 gridded data, 200 m squares ("Données au carreau de
200m, y compris données imputées", INSEE) — same vintage as the income
and population data used elsewhere. Squares with fewer than 11 tax
households are imputed by INSEE (i_est_200 = 1); they're kept, flagged.

Why a grid rather than IRIS centroids: travel times are computed from
where people live. An IRIS centroid can sit in a park or a rail yard,
several minutes from most of its residents.

Two demand columns:
- pop: residents (ind), used for pharmacies;
- pop_gp: residents weighted by age with the DREES APL weights for
  general practice (2024 column of the APL "Paramètres" sheet: average GP
  consumption of each age band relative to the national average). The
  grid's age bands don't match the DREES 5-year bands, so each grid band
  gets the mean of the DREES weights over the years it covers (DREES_WEIGHT_BY_YEAR).
  The 80+ band gets the plain mean of 80-84, 85-89 and 90+ (1.85): the
  grid has no finer split.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config
from utils.download import download_file, extract_zip, find_download_link, find_extracted_file
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "filosofi_grid"
OUT_PATH = config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson"
CELL_M = 200

# DREES APL general practice, age weights, 2024 (5-year bands).
DREES_GP_WEIGHTS_2024 = [
    (0, 4, 1.12), (5, 9, 0.61), (10, 14, 0.58), (15, 19, 0.60), (20, 24, 0.78),
    (25, 29, 0.79), (30, 34, 0.82), (35, 39, 0.86), (40, 44, 0.91), (45, 49, 0.90),
    (50, 54, 1.02), (55, 59, 1.13), (60, 64, 1.14), (65, 69, 1.21), (70, 74, 1.39),
    (75, 79, 1.59), (80, 84, 1.57), (85, 89, 1.81), (90, 120, 2.18),
]
GRID_BANDS = {
    "ind_0_3": (0, 3), "ind_4_5": (4, 5), "ind_6_10": (6, 10), "ind_11_17": (11, 17),
    "ind_18_24": (18, 24), "ind_25_39": (25, 39), "ind_40_54": (40, 54), "ind_55_64": (55, 64),
    "ind_65_79": (65, 79),
}
WEIGHT_80_PLUS = round(np.mean([1.57, 1.81, 2.18]), 3)


def drees_weight(age: int) -> float:
    return next(w for lo, hi, w in DREES_GP_WEIGHTS_2024 if lo <= age <= hi)


def grid_band_weights() -> dict[str, float]:
    weights = {band: round(np.mean([drees_weight(a) for a in range(lo, hi + 1)]), 3) for band, (lo, hi) in GRID_BANDS.items()}
    weights["ind_80p"] = WEIGHT_80_PLUS
    return weights


def load_grid() -> pd.DataFrame:
    url = find_download_link(config.FILOSOFI_GRID_PAGE, r"Filosofi2021_carreaux_200m_csv\.zip")
    zip_path = download_file(url, RAW_DIR / Path(url).name)
    extract_dir = extract_zip(zip_path, RAW_DIR / "extract")
    path = find_extracted_file(extract_dir, r"carreaux_200m_met\.csv", "Filosofi 200 m grid (metropolitan France)")
    cols = ["idcar_200m", "i_est_200", "lcog_geo", "ind", *GRID_BANDS, "ind_80p"]
    chunks = []
    for chunk in pd.read_csv(path, usecols=cols, dtype={"idcar_200m": str, "lcog_geo": str}, chunksize=500_000):
        chunks.append(chunk[chunk.lcog_geo.str[:2].isin(config.IDF_DEP_CODES)])
    return pd.concat(chunks, ignore_index=True)


def main():
    grid = load_grid()
    weights = grid_band_weights()
    print("Age weights per grid band:", weights)
    grid["pop"] = grid["ind"]
    grid["pop_gp"] = sum(grid[band] * w for band, w in weights.items())
    # idcar_200m = "CRS3035RES200mN{northing}E{easting}", lower-left corner in EPSG:3035.
    parts = grid.idcar_200m.str.extract(r"N(\d+)E(\d+)").astype(float)
    grid["x3035"], grid["y3035"] = parts[1] + CELL_M / 2, parts[0] + CELL_M / 2
    grid = grid[grid["pop"] > 0]
    gdf = gpd.GeoDataFrame(
        grid[["idcar_200m", "i_est_200", "pop", "pop_gp"]].rename(columns={"idcar_200m": "cell_id"}),
        geometry=gpd.points_from_xy(grid.x3035, grid.y3035), crs="EPSG:3035",
    ).to_crs(config.CRS_LATLON)
    print(f"{len(gdf)} inhabited cells, {gdf['pop'].sum():,.0f} residents, "
          f"{100 * (gdf.i_est_200 == 1).mean():.1f}% of cells imputed ({100 * gdf.loc[gdf.i_est_200 == 1, 'pop'].sum() / gdf['pop'].sum():.1f}% of residents)")
    save_geojson(gdf, OUT_PATH, required_cols=["cell_id", "pop", "pop_gp"])


if __name__ == "__main__":
    main()
