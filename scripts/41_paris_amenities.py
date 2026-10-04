"""Public toilets and drinking fountains, Paris only (decision of 3 October
2026, CLAUDE.md "Toilettes publiques et points d'eau potable"): the City of
Paris publishes complete lists; most inner-suburb communes do not, so these
places are shown for Paris neighbourhoods only. For information, never a
sub-score; same method as the other everyday places (script 34,
ROUTES_SET=paris: Tuesday 13 October 2026 10:00, four profiles, Paris cells
as origins).

Sources (opendata.paris.fr, Open Database License):
- sanisettesparis: public toilets (sanisettes, park toilets, lavatories);
  only those "En service". Types written:
  - toilets: all toilets in service except urinals (not usable by everyone);
  - toilets_pmr: those marked accessible to wheelchair users (acces_pmr =
    Oui), the destination of the wheelchair profile;
  - toilets_24h: those open 24 hours a day (horaire "24/24h");
- fontaines-a-boire (Eau de Paris): drinking fountains marked available
  (dispo = OUI), type drinking_water (includes the fountains of the Paris
  cemeteries outside Paris).

Output: data/processed/access/paris_amenities_idf.geojson (dest_id, type,
name, geometry), read by script 34 when ROUTES_SET=paris; the raw exports
are kept in data/raw/paris_amenities/ with their download date.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
import requests

import config
from utils.io import save_geojson

RAW = config.DATA_RAW / "paris_amenities"
OUT = config.DATA_PROCESSED / "access" / "paris_amenities_idf.geojson"
API = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{ds}/exports/geojson"


def fetch(ds: str) -> gpd.GeoDataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"{ds}.geojson"
    r = requests.get(API.format(ds=ds), timeout=120)
    r.raise_for_status()
    path.write_bytes(r.content)
    (RAW / f"{ds}.downloaded.txt").write_text(dt.date.today().isoformat() + "\n", encoding="utf-8")
    return gpd.read_file(path)


def main():
    toilets = fetch("sanisettesparis")
    toilets = toilets[(toilets["statut"] == "En service") & ~toilets["type"].fillna("").str.startswith("Urinoir")]
    parts = [
        toilets.assign(kind="toilets"),
        toilets[toilets["acces_pmr"] == "Oui"].assign(kind="toilets_pmr"),
        toilets[toilets["horaire"].fillna("").str.replace(" ", "") == "24/24h"].assign(kind="toilets_24h"),
    ]
    t = pd.concat(parts, ignore_index=True)
    t["name"] = t["adresse"].fillna("")
    fountains = fetch("fontaines-a-boire")
    fountains = fountains[fountains["dispo"] == "OUI"].assign(kind="drinking_water")
    fountains["name"] = fountains["voie"].fillna("")
    dest = pd.concat([t[["kind", "name", "geometry"]], fountains[["kind", "name", "geometry"]]], ignore_index=True)
    dest = gpd.GeoDataFrame(dest.rename(columns={"kind": "type"}), geometry="geometry", crs=config.CRS_LATLON)
    # Points only (a few records are lines or polygons): their centroid.
    dest["geometry"] = dest.to_crs(config.CRS_PROJECTED).geometry.centroid.to_crs(config.CRS_LATLON)
    dest.insert(0, "dest_id", range(len(dest)))
    save_geojson(dest, OUT)
    print(dest.groupby("type").size().to_string())


if __name__ == "__main__":
    main()
