"""Key destinations for the routes page (Itinéraires), Île-de-France.

One point per destination, with its type, for the nearest-destination
travel times of script 34. Supply covers the whole of Île-de-France so
that neighbourhoods at the edge of the inner ring see destinations across
the boundary (same edge rule as the E2SFCA).

Types and inclusion rules (pre-registered on 2026-10-02 before any travel
time was computed, CLAUDE.md "Hypothèse de travail" — same kind of
service in all four départements):
- emergency: BPE 2025 D106, general emergency departments only — units
  reserved to one specialty or to children excluded by name (Quinze-Vingts,
  Trousseau, Necker, Robert-Debré);
- town_hall: BPE A129, one per commune (per arrondissement in Paris),
  duplicates at the same point counted once; town-hall annexes are not in
  the BPE and are not counted;
- employment: BPE A122, local France Travail agencies ("APE") only;
  specialised agencies ("APES": performing arts, airport) excluded;
- post_office: BPE A206 (post-office counters; relay points and communal
  postal agencies left out: partial services);
- france_services: ANCT list, fixed sites and antennas; mobile buses
  excluded (no fixed location);
- caf, cpam: DILA public-administration directory, the fund's own offices
  open to all ("accueil de …", "siège de …", "accueil national");
  excluded: "Point d'accueil" (sessions hosted by partner organisations,
  reserved to specific groups), "Service …" (specialised services), and
  four offices hosted by a partner or reserved to one group (listed in
  PARTNER_HOSTED);
- gp, pharmacy: the sites of scripts 27 and 28 (cleaned supply);
- station: heavy-network stop points (metro, RER, Transilien, tram) from
  the IDFM GTFS, with their wheelchair accessibility (1 yes, 2 no, 0
  unknown, inherited from the parent station as in script 30).

Outputs (data/processed/access/): route_destinations_idf.geojson,
route_destinations_excluded.csv (every excluded record and its reason).
"""
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.io import save_geojson

ACCESS_DIR = config.DATA_PROCESSED / "access"
OUT = ACCESS_DIR / "route_destinations_idf.geojson"
OUT_EXCLUDED = ACCESS_DIR / "route_destinations_excluded.csv"
BPE_CSV = config.DATA_RAW / "bpe" / "extracted" / "BPE25.csv"
FRANCE_SERVICES = config.DATA_RAW / "public_services" / "france_services.csv"
CAF_CPAM = config.DATA_RAW / "public_services" / "annuaire_caf_cpam_idf.json"
GTFS = config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"
IDF = config.IDF_DEP_CODES

EMERGENCY_EXCLUDED = {
    "QUINZE VINGTS": "ophthalmology only",
    "TROUSSEAU": "children only",
    "NECKER": "children only",
    "ROBERT DEBRE": "children only",
}
PARTNER_HOSTED = ["Mairie du 9", "Maison dans la rue", "Armée du Salut", "Hauts de Belleville AME"]
HEAVY_ROUTE_TYPES = {"0", "1", "2"}  # tram, metro, rail (RER, Transilien)


def points(df, lon, lat):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lon].astype(float), df[lat].astype(float)), crs=config.CRS_LATLON)


def bpe_destinations(excluded: list) -> gpd.GeoDataFrame:
    b = pd.read_csv(BPE_CSV, sep=";", dtype=str,
                    usecols=["TYPEQU", "DEP", "DEPCOM", "NOMRS", "LONGITUDE", "LATITUDE"])
    b = b[b.DEP.isin(IDF) & b.LONGITUDE.notna()]
    parts = []

    u = b[b.TYPEQU == "D106"]
    for _, r in u.iterrows():
        for key, why in EMERGENCY_EXCLUDED.items():
            if key in r.NOMRS:
                excluded.append(("emergency", r.NOMRS, r.DEPCOM, why))
    keep = ~u.NOMRS.apply(lambda n: any(k in n for k in EMERGENCY_EXCLUDED))
    parts.append(u[keep].assign(type="emergency"))

    m = b[b.TYPEQU == "A129"].drop_duplicates(["DEPCOM", "LONGITUDE", "LATITUDE"])
    parts.append(m.assign(type="town_hall"))

    f = b[b.TYPEQU == "A122"]
    spec = f.NOMRS.str.startswith("APES")
    for _, r in f[spec].iterrows():
        excluded.append(("employment", r.NOMRS, r.DEPCOM, "specialised agency"))
    parts.append(f[~spec].assign(type="employment"))

    parts.append(b[b.TYPEQU == "A206"].assign(type="post_office"))

    out = pd.concat(parts).rename(columns={"NOMRS": "name", "DEPCOM": "insee_com"})
    return points(out[["type", "name", "insee_com", "LONGITUDE", "LATITUDE"]], "LONGITUDE", "LATITUDE").drop(columns=["LONGITUDE", "LATITUDE"])


def france_services(excluded: list) -> gpd.GeoDataFrame:
    fs = pd.read_csv(FRANCE_SERVICES, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
    fs = fs[fs.insee_dep.str.zfill(2).isin(IDF)]
    bus = fs.format_fs.str.startswith("Bus")
    for _, r in fs[bus].iterrows():
        excluded.append(("france_services", r.lib_fs, r.insee_com, "mobile bus, no fixed location"))
    fs = fs[~bus].rename(columns={"lib_fs": "name"})
    return points(fs.assign(type="france_services")[["type", "name", "insee_com", "longitude", "latitude"]], "longitude", "latitude").drop(columns=["longitude", "latitude"])


def caf_cpam(excluded: list) -> gpd.GeoDataFrame:
    rows = []
    for x in json.load(open(CAF_CPAM, encoding="utf-8")):
        suffix = re.split(r"\s[-–]\s", x["nom"], maxsplit=1)[1].strip()
        adr = json.loads(x["adresse"] or "[]")[0]
        com = next((p.get("code_insee_commune", [""])[0] for p in json.loads(x["pivot"]) if p["type_service_local"] == x["type"]), "")
        reason = None
        if suffix.startswith("Point d'accueil"):
            reason = "session hosted by a partner organisation, reserved to specific groups"
        elif suffix.startswith("Service"):
            reason = "specialised service"
        elif any(p in suffix for p in PARTNER_HOSTED):
            reason = "office hosted by a partner or reserved to one group"
        elif not suffix.startswith(("accueil", "siège")):
            reason = "not an office of the fund"
        if reason:
            excluded.append((x["type"], x["nom"], com, reason))
            continue
        rows.append({"type": x["type"], "name": x["nom"], "insee_com": com,
                     "lon": float(adr["longitude"]), "lat": float(adr["latitude"])})
    df = pd.DataFrame(rows)
    return points(df, "lon", "lat").drop(columns=["lon", "lat"])


def access_sites() -> gpd.GeoDataFrame:
    parts = []
    for name, kind in [("gp_sites_idf.geojson", "gp"), ("pharmacy_sites_idf.geojson", "pharmacy")]:
        g = gpd.read_file(ACCESS_DIR / name).to_crs(config.CRS_LATLON)
        parts.append(gpd.GeoDataFrame({"type": kind, "name": g["site_id"].astype(str), "insee_com": ""}, geometry=g.geometry, crs=config.CRS_LATLON))
    return pd.concat(parts)


def stations() -> gpd.GeoDataFrame:
    with zipfile.ZipFile(GTFS) as z:
        rd = lambda n, **k: pd.read_csv(z.open(n), dtype=str, **k)
        routes = rd("routes.txt")
        trips = rd("trips.txt", usecols=["route_id", "trip_id"])
        stops = rd("stops.txt")
        st = rd("stop_times.txt", usecols=["trip_id", "stop_id"])
    heavy = set(routes.loc[routes.route_type.isin(HEAVY_ROUTE_TYPES), "route_id"])
    heavy_trips = set(trips.loc[trips.route_id.isin(heavy), "trip_id"])
    served = set(st.loc[st.trip_id.isin(heavy_trips), "stop_id"])
    wb = stops.set_index("stop_id")["wheelchair_boarding"].fillna("0").replace("", "0")
    parent = stops.set_index("stop_id")["parent_station"].fillna("")
    wb = wb.where(wb != "0", parent.map(wb).fillna("0"))
    s = stops[stops.stop_id.isin(served)].copy()
    s["wheelchair"] = s.stop_id.map(wb)
    s = s.assign(type="station", name=s.stop_name, insee_com="")
    return points(s[["type", "name", "insee_com", "wheelchair", "stop_lon", "stop_lat"]], "stop_lon", "stop_lat").drop(columns=["stop_lon", "stop_lat"])


def main():
    excluded = []
    dest = pd.concat([bpe_destinations(excluded), france_services(excluded), caf_cpam(excluded), access_sites(), stations()], ignore_index=True)
    dest["wheelchair"] = dest["wheelchair"].fillna("")
    dest.insert(0, "dest_id", range(len(dest)))
    dest = gpd.GeoDataFrame(dest, geometry="geometry", crs=config.CRS_LATLON)
    save_geojson(dest, OUT)
    pd.DataFrame(excluded, columns=["type", "name", "insee_com", "reason"]).to_csv(OUT_EXCLUDED, index=False)
    dep = dest.insee_com.str[:2]
    print(dest.groupby("type").size().to_string())
    print("MGP by department (75/92/93/94):")
    print(pd.crosstab(dest["type"], dep).reindex(columns=["75", "92", "93", "94"]).to_string())
    print(f"{len(excluded)} records excluded -> {OUT_EXCLUDED.name}")


if __name__ == "__main__":
    main()
