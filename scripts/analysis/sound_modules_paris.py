"""Audit: pedestrian crossings with a sound module in Paris (19 October 2026).

Descriptive only, no indicator: how many signalised pedestrian crossings of
Paris have a sound module for blind and partially sighted people, by
arrondissement and by neighbourhood (IRIS).

Sources (Ville de Paris, Open Database License, both updated on 1 October
2026), downloaded as CSV (";") from opendata.paris.fr:
- "Modules sonores passages piétons" (modules-sonores-passages-pietons):
  one row per module, key code_ouvrage;
- "Signalisation lumineuse tricolore" (signalisation-tricolore): one row per
  lamp, key cod_ouvrag. A crossing is taken to be an "ouvrage" with at least
  one pedestrian signal head (lib_lumi_1 starting with "Caisson Piéton");
  86 % of them have exactly two heads, which suggests one ouvrage = one
  signalised crossing (to be confirmed by the Ville de Paris).

Usage (in the project's Docker image, which has geopandas):
  python scripts/analysis/sound_modules_paris.py <folder with modules.csv and feux.csv>
"""
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

D = sys.argv[1]
feux = pd.read_csv(f"{D}/feux.csv", sep=";", encoding="utf-8-sig", dtype=str)
mod = pd.read_csv(f"{D}/modules.csv", sep=";", encoding="utf-8-sig", dtype=str)
heads = feux[feux.lib_lumi_1.fillna("").str.startswith("Caisson Piéton")]
print(f"modules: {len(mod)}; ouvrages with a module: {mod.code_ouvrage.nunique()}")
print(f"lamps: {len(feux)}; ouvrages: {feux.cod_ouvrag.nunique()}; ouvrages with pedestrian heads: {heads.cod_ouvrag.nunique()}")
print("pedestrian heads per ouvrage:", heads.groupby("cod_ouvrag").size().value_counts().sort_index().to_dict())
print("installation years of the modules:", mod.date_inst_accessoire.fillna("none").str[:4].value_counts().sort_index().to_dict())

crossings = heads.drop_duplicates("cod_ouvrag").copy()
latlon = crossings.geo_point_2d.str.split(",", expand=True).astype(float)
g = gpd.GeoDataFrame(crossings[["cod_ouvrag"]], geometry=[Point(xy) for xy in zip(latlon[1], latlon[0])], crs=4326)
g["sound"] = g.cod_ouvrag.isin(set(mod.code_ouvrage))
print(f"signalised crossings: {len(g)}; with a module: {int(g.sound.sum())} ({100 * g.sound.mean():.1f} %)")

iris = gpd.read_file("/app/data/processed/iris_mgp.geojson")[["code_iris", "insee_com", "geometry"]]
iris = iris[iris.insee_com.astype(str).str.startswith("75")].to_crs(4326)
j = gpd.sjoin(g, iris, predicate="within", how="left")
per = j.groupby("code_iris").agg(n=("sound", "size"), s=("sound", "sum"))
per["share"] = per.s / per.n
print(f"Paris IRIS: {len(iris)}; with a signalised crossing: {len(per)}; with at least 5: {int((per.n >= 5).sum())}")
print("share with a module, IRIS with at least 5 crossings:")
print(per[per.n >= 5].share.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2).to_string())
arr = j.groupby(j.insee_com.astype(str)).agg(n=("sound", "size"), s=("sound", "sum"))
arr["share_pct"] = (100 * arr.s / arr.n).round(1)
print(arr.sort_values("share_pct").to_string())
