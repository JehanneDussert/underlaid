"""Everyday destinations for the "Your neighbourhood" page, Île-de-France.

Pre-registered and validated on 2026-10-03 (CLAUDE.md, "Hypothèse de
travail", addendum to the routes pre-registration): seven places, all for
information (no sub-score), Tuesday 13 October 2026 10:00, the four
profiles of script 34. Markets were dropped (OpenStreetMap is the only
source and it is not mapped evenly across départements).

Types and sources:
- creche: BPE 2025 D502 (establishments receiving a CAF service grant);
- food_store: BPE 2025 B104 (hypermarket and department store), B105
  (supermarket and multi-store, 400-2,500 m²), B201 (convenience store,
  120-400 m²); groceries under 120 m² (B202) excluded;
- nursery_school: BPE 2025 C107 (nursery school) and C108 (primary school
  with at least one nursery class), public sector only (SECTEUR = 1);
- schools (added 2026-10-04, same run as the corrected attachment of
  points): elementary (C108 primary, C109 elementary), lower secondary
  (C201 collège), upper secondary (C301 general and technological, C302
  vocational lycée); public (SECTEUR = 1) and private under contract with
  the State (SECTEUR = 3) as separate types; private without contract
  (SECTEUR = 2) excluded. Codes 2 and 3 read from establishment names
  (2: Montessori, private tutoring schools; 3: Massillon, Francs-Bourgeois);
- police: BPE 2025 A140 (national police open to the public);
- social_centre: BPE 2025 D506 (social centres, CNAF);
- library: BPE 2025 F307 (local-authority libraries);
- park: regional inventory of green and wooded spaces open to the public
  (data.iledefrance.fr, same raw file as script 04), status "Ouvert";
  entrances are unknown, so each space contributes points every 100 m
  along its outline (at least one per space), parks within 3 km of the
  MGP only, one point per 100 m square.

Output: data/processed/access/neighbourhood_destinations_idf.geojson
(dest_id, type, name, insee_com, geometry), read by script 34 when
ROUTES_SET=neighbourhood.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

import config
from utils.io import save_geojson

OUT = config.DATA_PROCESSED / "access" / "neighbourhood_destinations_idf.geojson"
BPE_CSV = config.DATA_RAW / "bpe" / "extracted" / "BPE25.csv"
GREEN = config.DATA_RAW / "cool_spots_green_areas" / "cool_spots_green_areas_raw.geojson"
IDF = config.IDF_DEP_CODES
PARK_STEP_M = 100
PARK_BUFFER_M = 3_000

BPE_TYPES = {
    "creche": ["D502"],
    "food_store": ["B104", "B105", "B201"],
    "nursery_school": ["C107", "C108"],
    "police": ["A140"],
    "social_centre": ["D506"],
    "library": ["F307"],
}
# Schools: (BPE codes, SECTEUR) per type.
SCHOOL_TYPES = {
    "elementary_public": (["C108", "C109"], "1"),
    "elementary_private": (["C108", "C109"], "3"),
    "college_public": (["C201"], "1"),
    "college_private": (["C201"], "3"),
    "lycee_public": (["C301", "C302"], "1"),
    "lycee_private": (["C301", "C302"], "3"),
}


def bpe_points() -> gpd.GeoDataFrame:
    b = pd.read_csv(BPE_CSV, sep=";", dtype=str, usecols=["TYPEQU", "DEP", "DEPCOM", "NOMRS", "SECTEUR", "LONGITUDE", "LATITUDE"])
    b = b[b.DEP.isin(IDF) & b.LONGITUDE.notna()]
    parts = []
    for kind, codes in BPE_TYPES.items():
        x = b[b.TYPEQU.isin(codes)]
        if kind == "nursery_school":
            x = x[x.SECTEUR == "1"]
        parts.append(x.assign(type=kind))
    for kind, (codes, sector) in SCHOOL_TYPES.items():
        parts.append(b[b.TYPEQU.isin(codes) & (b.SECTEUR == sector)].assign(type=kind))
    df = pd.concat(parts).rename(columns={"NOMRS": "name", "DEPCOM": "insee_com"})
    return gpd.GeoDataFrame(df[["type", "name", "insee_com"]],
                            geometry=gpd.points_from_xy(df.LONGITUDE.astype(float), df.LATITUDE.astype(float)), crs=config.CRS_LATLON)


def park_points() -> gpd.GeoDataFrame:
    g = gpd.read_file(GREEN)
    g = g[(g["statouvlib"] == "Ouvert") & g["insee"].astype(str).str[:2].isin(IDF) & g.geometry.notna()].to_crs(config.CRS_PROJECTED)
    rows = []
    for _, r in g.iterrows():
        boundary = r.geometry.boundary
        n = max(1, int(boundary.length // PARK_STEP_M))
        for d in np.linspace(0, boundary.length, n, endpoint=False):
            rows.append({"type": "park", "name": r["nom"], "insee_com": str(r["insee"]), "geometry": boundary.interpolate(d)})
    pts = gpd.GeoDataFrame(rows, geometry="geometry", crs=config.CRS_PROJECTED)
    # The nearest park of an MGP resident is always close: keep only parks
    # within PARK_BUFFER_M of the MGP, and one point per 100 m square, to
    # keep the routing matrix within memory (no effect on the nearest time
    # beyond a few metres).
    mgp = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).union_all().buffer(PARK_BUFFER_M)
    pts = pts[pts.within(mgp)]
    key = (pts.geometry.x // PARK_STEP_M).astype(int).astype(str) + "_" + (pts.geometry.y // PARK_STEP_M).astype(int).astype(str)
    pts = pts.loc[~key.duplicated()]
    return pts.to_crs(config.CRS_LATLON)


def main():
    dest = pd.concat([bpe_points(), park_points()], ignore_index=True)
    dest.insert(0, "dest_id", range(len(dest)))
    dest = gpd.GeoDataFrame(dest, geometry="geometry", crs=config.CRS_LATLON)
    save_geojson(dest, OUT)
    dep = dest["insee_com"].str[:2]
    print(pd.crosstab(dest["type"], dep).reindex(columns=["75", "92", "93", "94"]).to_string())
    print(dest.groupby("type").size().to_string())


if __name__ == "__main__":
    main()
