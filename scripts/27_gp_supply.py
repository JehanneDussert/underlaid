"""General practitioners' practice sites in Île-de-France, with a capacity.

Supply side of the GP E2SFCA (script 31). Source: RPPS open extract
(Annuaire Santé, ANS, "Extractions des données en libre accès", Licence
Ouverte 2.0), file Personne_activite — one row per practitioner and
practice site.

Who counts (same field as the DREES APL, which covers "omnipraticiens
libéraux ... et salariés en centre de santé"):
- physicians (profession 10) with a general-practice qualification
  (savoir-faire SM26, SM53 or SM54);
- liberal practice in a solo or group practice or a practice company
  (secteur SA07, SA08, SA09);
- salaried in a health centre (SA05, including municipal ones), or in a
  practice (SA07-SA09).
Left out: teleconsultation companies (SA64, no physical site), hospitals,
PMI, social security, companies, care homes and other settings that don't
offer open-access primary care.

Also left out, by an explicit list (EXCLUDED_BY_NAME, EXCLUDED_BY_ADDRESS,
decided on 2026-10-02 before any crossing with residents' means): structures
registered in the retained sectors that don't offer local, everyday GP
consultations. Found by reviewing by hand every address with 15 or more
GPs, plus name patterns. Four kinds:
- teleconsultation platforms registered as health centres (their GP
  headcount is the remote workforce);
- on-call and home-visit services (SOS Médecins, Urgences Médicales de
  Paris): their doctors are registered at every on-call point;
- hospital and clinic emergency departments run by doctors' companies;
- health services reserved to one population (students, airport staff).
The list, with the reason for each line, is published in SCORING.md. A
practitioner's capacity is split across their remaining sites; one with
no remaining site drops out. Excluded rows stay as zero-capacity points so
site ids, and the travel-time matrices of script 31, stay valid.

Capacity: each practitioner counts 1, split equally across their
retained sites. Actual activity (consultations per year, used by the
APL) isn't public; part-time work is therefore not captured.

Location: the FINESS coordinates of the site when the RPPS row carries a
FINESS site number found in the FINESS extract, otherwise the site address
geocoded against the Base Adresse Nationale. Sites geocoded below
MIN_GEOCODE_SCORE are dropped and counted.

The whole of Île-de-France is kept, not just the MGP, so that IRIS on
the edge of the inner ring see the supply across the boundary (edge
effect, see SCORING.md).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd

import config
from utils.download import download_file, find_datagouv_resource, find_extracted_file, extract_zip
from utils.geocode import geocode
from utils.io import save_geojson

RAW_DIR = config.DATA_RAW / "rpps"
OUT_PATH = config.DATA_PROCESSED / "access" / "gp_sites_idf.geojson"
GEOCODE_CACHE = config.DATA_INTERIM / "geocode_cache_rpps.csv"

GP_SAVOIR_FAIRE = {"SM26", "SM53", "SM54"}
PRACTICE_SECTORS = {"SA07", "SA08", "SA09"}
HEALTH_CENTRE_SECTOR = "SA05"
MIN_GEOCODE_SCORE = 0.5

# (case-insensitive regex on "Raison sociale site", reason).
EXCLUDED_BY_NAME = [
    (r"\bQARE\b|ACCESS SANTE", "teleconsultation platform (Qare / Access Santé)"),
    (r"^CDS\b.*\bLIVI\b", "teleconsultation platform (Livi)"),
    (r"MEDIKSANTE|MEDADOM", "teleconsultation platform (Medadom / Mediksanté)"),
    (r"URGENC|\bSEL URG\b", "hospital or clinic emergency department"),
    (r"SOS M[EÉ]DECIN", "on-call and home-visit service (SOS Médecins)"),
    (r"SANTE ETUDIANTE", "reserved to students (university health service)"),
    (r"AEROPORT", "airport medical service"),
]
# (address as built by select_gp_sites, postcode, reason, certainty).
EXCLUDED_BY_ADDRESS = [
    ("87 BOULEVARD DE PORT ROYAL", "75013", "SOS Médecins Paris (centre and home visits)", "confirmed"),
    ("128 BOULEVARD MACDONALD", "75019", "SOS Médecins Paris 19", "confirmed"),
    ("2 RUE FRANCIS GARNIER", "75017", "SOS Médecins Paris 17", "confirmed"),
    ("27 RUE DE SEVRES", "92100", "SOS 92 on-call point (Boulogne-Billancourt)", "confirmed"),
    ("14 RUE DE L ABBAYE", "92160", "on-call point, same doctors as SOS 92 (Antony)", "probable"),
    ("24 RUE DE L EST", "75020", "Urgences Médicales de Paris", "confirmed"),
    ("21 RUE DE CHAZELLES", "75017", "Urgences Médicales de Paris / Urgences Franciliennes (Clinique du Parc Monceau)", "confirmed"),
    ("122 RUE DE BAGNOLET", "75020", "on-call network, same doctors as Urgences Médicales de Paris (rue de Bagnolet)", "probable"),
    ("178 BIS RUE DE VAUGIRARD", "75015", "on-call network, same doctors as Urgences Médicales de Paris (rue de Vaugirard)", "probable"),
    ("35 RUE DES CORDELIERS", "77100", "SOS Médecins 77 network (Meaux)", "probable"),
    ("5 PLACE DE LA REVOLUTION", "77680", "SOS Médecins 77 network (Roissy-en-Brie)", "probable"),
    ("PLACE MICHEL HOUEL", "77580", "SOS Médecins 77 network (Crécy-la-Chapelle)", "probable"),
    ("14 ALLEE DE LA ROTONDE", "77120", "SOS Médecins 77 network (Coulommiers)", "probable"),
    ("18 RUE GUSTAVE NAST", "77500", "SOS Médecins 77 network (Chelles)", "probable"),
    ("1 RUE DU THEATRE", "77700", "SOS Médecins 77 network (Serris)", "probable"),
    ("37 RUE DU GENERAL LECLERC", "77170", "on-call network, same doctors as SOS Médecins 91 (Brie-Comte-Robert)", "probable"),
    ("18 TRAIT D UNION", "77127", "on-call network (Lieusaint)", "probable"),
    ("11 BOULEVARD DE L ALMONT", "77000", "on-call network, same doctors as SOS Médecins 91 (Melun)", "probable"),
    ("19 RUE DE LA LIBERATION", "91750", "SOS Médecins 91 (Chevannes)", "confirmed"),
    ("14 RUE TITREVILLE", "78160", "SOS Médecins on-call point (Marly-le-Roi)", "confirmed"),
    ("2 PLACE DES 7 FONTAINES", "95150", "SOS Médecins 95 network (Taverny)", "probable"),
    ("54 RUE VIGNERONDE", "95100", "SOS Médecins 95 network (Argenteuil)", "probable"),
    ("21 RUE DES FRERES CAPUCINS", "95310", "SOS Médecins 95 network (Saint-Ouen-l'Aumône)", "probable"),
    ("5 RUE DES OUCHES", "95410", "on-call network (Groslay)", "probable"),
    ("17 AVENUE HENRI BARBUSSE", "93700", "on-call network, same doctors as Bondy and Épinay (Drancy)", "probable"),
    ("17 AVENUE HENRI VARAGNAT", "93140", "on-call network (Bondy)", "probable"),
    ("12 RUE DU GENERAL JULIEN", "93800", "on-call network (Épinay-sur-Seine)", "probable"),
    ("35 RUE D AMIENS", "93240", "clinic (Clinique de l'Estrée, Stains)", "confirmed"),
]


def load_rpps() -> pd.DataFrame:
    url = find_datagouv_resource(config.RPPS_DATASET_SLUG, config.RPPS_RESOURCE_TITLE)
    zip_path = download_file(url, RAW_DIR / "PS_LibreAcces.zip")
    extract_dir = extract_zip(zip_path, RAW_DIR / "extract")
    path = find_extracted_file(extract_dir, r"PS_LibreAcces_Personne_activite_.*\.txt", "RPPS Personne_activite file")
    df = pd.read_csv(path, sep="|", dtype=str, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]
    return df


def select_gp_sites(df: pd.DataFrame) -> pd.DataFrame:
    df = df[(df["Code profession"] == "10") & df["Code savoir-faire"].isin(GP_SAVOIR_FAIRE)].copy()
    df["citycode"] = df["Code commune (coord. structure)"].fillna("")
    df["dep"] = df["citycode"].str[:2]
    df = df[df["dep"].isin(config.IDF_DEP_CODES)]
    mode, sector = df["Code mode exercice"].fillna(""), df["Code secteur d'activité"].fillna("")
    kind = pd.Series(pd.NA, index=df.index, dtype="object")
    kind[(mode == "L") & sector.isin(PRACTICE_SECTORS)] = "liberal"
    kind[(mode == "S") & (sector == HEALTH_CENTRE_SECTOR)] = "salaried_health_centre"
    kind[(mode == "S") & sector.isin(PRACTICE_SECTORS)] = "salaried_practice"
    df["kind"] = kind
    df = df[df["kind"].notna()].copy()
    parts = ["Numéro Voie (coord. structure)", "Indice répétition voie (coord. structure)",
             "Libellé type de voie (coord. structure)", "Libellé Voie (coord. structure)"]
    df["address"] = df[parts].fillna("").agg(" ".join, axis=1).str.split().str.join(" ")
    df["postcode"] = df["Code postal (coord. structure)"].fillna("")
    df["finess"] = df["Numéro FINESS site"].fillna("")
    df["excluded_reason"] = exclusion_reasons(df)
    kept = df["excluded_reason"].isna()
    # Capacity split across the practitioner's remaining sites only.
    df["capacity"] = 0.0
    df.loc[kept, "capacity"] = 1 / df[kept].groupby("Identifiant PP")["Identifiant PP"].transform("size")
    return df


def exclusion_reasons(df: pd.DataFrame) -> pd.Series:
    reason = pd.Series(pd.NA, index=df.index, dtype="object")
    name = df["Raison sociale site"].fillna("")
    for pattern, why in EXCLUDED_BY_NAME:
        reason[name.str.contains(pattern, case=False, regex=True) & reason.isna()] = why
    key = df["address"].str.upper() + "|" + df["postcode"]
    for address, postcode, why, certainty in EXCLUDED_BY_ADDRESS:
        hit = key == f"{address}|{postcode}"
        if not hit.any():
            raise RuntimeError(f"Exclusion matches no RPPS row (address renamed upstream?): {address} {postcode}")
        reason[hit & reason.isna()] = f"{why} [{certainty}]"
    return reason


def load_finess_coordinates() -> pd.DataFrame:
    path = config.DATA_RAW / "finess" / "etalab_cs1100507.csv"
    if not path.exists():
        download_file(find_datagouv_resource(config.FINESS_DATASET_SLUG, config.FINESS_GEO_RESOURCE_TITLE), path)
    rows = [line.rstrip("\n").split(";") for line in open(path, encoding="utf-8", errors="replace")
            if line.startswith("geolocalisation;")]
    geo = pd.DataFrame([(r[1], r[2], r[3]) for r in rows], columns=["finess", "x", "y"])
    geo[["x", "y"]] = geo[["x", "y"]].apply(pd.to_numeric, errors="coerce")
    return geo.dropna()


def locate(df: pd.DataFrame) -> gpd.GeoDataFrame:
    finess = load_finess_coordinates()
    df = df.merge(finess, on="finess", how="left")
    by_finess = df[df["x"].notna()].copy()
    by_finess["geocode_source"] = "finess"
    by_finess["geocode_score"] = 1.0
    by_finess = gpd.GeoDataFrame(by_finess, geometry=gpd.points_from_xy(by_finess.x, by_finess.y), crs=config.CRS_PROJECTED)

    rest = geocode(df[df["x"].isna()], GEOCODE_CACHE)
    rest["geocode_source"] = "ban"
    rest["geocode_score"] = rest["result_score"]
    low = rest["geocode_score"].isna() | (rest["geocode_score"] < MIN_GEOCODE_SCORE)
    print(f"BAN geocoding: {len(rest)} rows, {low.sum()} below score {MIN_GEOCODE_SCORE} dropped "
          f"(capacity {rest.loc[low, 'capacity'].sum():.1f} of {df['capacity'].sum():.1f})")
    rest = rest[~low]
    rest = gpd.GeoDataFrame(rest, geometry=gpd.points_from_xy(rest.longitude, rest.latitude), crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED)
    cols = ["Identifiant PP", "kind", "capacity", "dep", "citycode", "geocode_source", "geocode_score", "geometry"]
    return pd.concat([by_finess[cols], rest[cols]], ignore_index=True)


def to_sites(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """One row per location (practitioners sharing an address are summed)."""
    points["xr"], points["yr"] = points.geometry.x.round(0), points.geometry.y.round(0)
    sites = points.groupby(["xr", "yr"]).agg(
        capacity=("capacity", "sum"),
        n_practitioners=("Identifiant PP", "nunique"),
        capacity_liberal=("capacity", lambda s: s[points.loc[s.index, "kind"] == "liberal"].sum()),
        capacity_health_centre=("capacity", lambda s: s[points.loc[s.index, "kind"] == "salaried_health_centre"].sum()),
        dep=("dep", "first"),
        geocode_source=("geocode_source", "first"),
    ).reset_index()
    sites["site_id"] = [f"gp{i:05d}" for i in range(len(sites))]
    gdf = gpd.GeoDataFrame(sites.drop(columns=["xr", "yr"]), geometry=gpd.points_from_xy(sites.xr, sites.yr), crs=config.CRS_PROJECTED)
    return gdf.to_crs(config.CRS_LATLON)


def main():
    df = select_gp_sites(load_rpps())
    excluded = df[df.excluded_reason.notna()]
    print("Excluded rows, by reason (distinct practitioners):")
    print(excluded.groupby("excluded_reason")["Identifiant PP"].nunique().to_string())
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    excluded.groupby(["excluded_reason", "Raison sociale site", "address", "postcode"], dropna=False)["Identifiant PP"] \
        .nunique().rename("practitioners").reset_index().to_csv(OUT_PATH.parent / "gp_excluded_structures.csv", index=False)
    summary = df.pivot_table(index="kind", columns="dep", values="capacity", aggfunc="sum").round(0)
    print("GP capacity (practitioners, split across sites) by kind and department:\n", summary.to_string())
    sites = to_sites(locate(df))
    print(f"{len(sites)} sites, capacity {sites.capacity.sum():.0f}")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_geojson(sites, OUT_PATH, required_cols=["site_id", "capacity"])


if __name__ == "__main__":
    main()
