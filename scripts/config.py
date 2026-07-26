"""Shared constants and paths for all download/normalize scripts."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Metropole du Grand Paris, "Petite Couronne": Paris (75) plus the three
# inner-ring departments. Grande Couronne is explicitly out of scope for
# now (no strong signal to extend further yet). A code_iris or commune
# code's first 2 digits are its department — filter with e.g.
# `df["code_iris"].str[:2].isin(MGP_DEP_CODES)`.
MGP_DEP_CODES = ["75", "92", "93", "94"]
# Kept for the few things that are genuinely Paris-specific by nature (the
# hand-compiled school-AC context in script 16 has no equivalent for the
# other 3 departments) rather than just a filter that needs broadening.
PARIS_DEP_CODE = "75"
IRIS_JOIN_COLUMN = "code_iris"

# CRS_LATLON is used for all file I/O and frontend consumption.
# CRS_PROJECTED (Lambert-93, meters) is used internally for area-weighted
# spatial joins, since area/distance math is meaningless in EPSG:4326.
CRS_LATLON = "EPSG:4326"
CRS_PROJECTED = "EPSG:2154"

IRIS_VINTAGE = 2024
IRIS_REFERENCE_PATH = DATA_PROCESSED / "iris_mgp.geojson"

# --- Source-specific settings ---

IDF_OPENDATASOFT_BASE = "https://data.iledefrance.fr"
IRIS_DATASET_ID = "iris"

PARIS_OPENDATASOFT_BASE = "https://opendata.paris.fr"

# Phase 5: the original "cool spots" indicators (ilots-de-fraicheur-*) only
# ever existed for the city of Paris — no Petite Couronne equivalent. Both
# re-sourced so the thermal sub-score is built the same way everywhere,
# Paris included (a deliberate methodology change, not an oversight — see
# SCORING.md): "cool facilities" moved to BPE (already used elsewhere in
# this pipeline — a regional pools dataset was considered and rejected,
# it turned out to be funding records, not a pools inventory); "cool
# green area" moved to this genuine Ile-de-France-wide dataset.
COOL_GREEN_SPACE_DATASET_ID = "espaces-verts-et-boises-surfaciques-ouverts-ou-en-projets-douverture-au-public"

ICU_SAT4BDNB_ZIP_URL = (
    "https://static.data.gouv.fr/resources/"
    "cartographie-nationale-des-indicateurs-lies-a-lilot-de-chaleur-urbain/"
    "20250114-092141/indicateurs-icu.zip"
)

# Bruitparif serves files behind a path containing literal spaces; the
# download helper takes care of percent-encoding it.
AIR_NOISE_ZIP_URL = (
    "https://www.bruitparif.fr/pages/En-tete/800 Le bruit en "
    "Île-de-France/300 carto-air-bruit-en-idf/600 Opendata air-bruit/"
    "Couches SIG air-bruit 2024_9_classes.zip"
)

# INSEE serves statistics-page files at a stable /fr/statistiques/fichier/
# {page_id}/{filename} pattern; confirmed working for the BPE 2025 edition
# (page https://www.insee.fr/fr/statistiques/8217525). This will need
# updating ("BPE25.zip" -> "BPE26.zip"...) whenever INSEE ships a new
# edition and changes the page id / filename.
BPE_ZIP_URL = "https://www.insee.fr/fr/statistiques/fichier/8217525/BPE25.zip"
BPE_RAW_ZIP = DATA_RAW / "bpe" / "BPE25.zip"
# BPE domain codes: C=education, D=health, E=transport/mobility
BPE_DOMAINS_OF_INTEREST = ("C", "D", "E")

EQUIPMENT_ACCESS_DATASET_SLUG = (
    "donnees-sur-la-localisation-et-lacces-de-la-population-aux-equipements"
)
IDF_REGION_CODE = "11"  # INSEE region code for Ile-de-France

# INSEE only exposes the current Filosofi edition through a statistics page
# whose direct file URL changes every year; the script scrapes it instead
# of hardcoding a link that will go stale.
INCOME_FILOSOFI_PAGE = "https://www.insee.fr/fr/statistiques/8229323"

EDUCATION_OPENDATASOFT_BASE = "https://data.education.gouv.fr"
SOCIAL_INDEX_SCHOOLS_DATASET_ID = "fr-en-ips-ecoles-ap2022"
SOCIAL_INDEX_MIDDLE_SCHOOLS_DATASET_ID = "fr-en-ips-colleges-ap2023"

ADEME_OPENDATASOFT_BASE = "https://data.ademe.fr"
ENERGY_PERFORMANCE_DATASET_ID = "dpe03existant"
ENERGY_PERFORMANCE_POOR_CLASSES = ("F", "G")

# Bulk export, no API key needed (the live Acceslibre API requires one;
# this static CSV mirror doesn't). ~524MB for all of France, filtered to
# MGP_DEP_CODES while reading in chunks.
ACCESSIBILITY_CSV_URL = (
    "https://static.data.gouv.fr/resources/"
    "accessibilite-des-etablissements-recevant-du-public-erp-pour-les-personnes-en-situation-de-handicap/"
    "20260710-231714/acceslibre.csv"
)

STREET_LIGHTING_DATASET_ID = "eclairage-public"  # opendata.paris.fr

QPV_OPENDATASOFT_BASE = "https://data.iledefrance.fr"
QPV_DATASET_ID = "qp-politiquedelaville-shp"

# Enedis' open data portal runs on data-fair too (like ADEME's DPE
# dataset) but at a different host than the old data.enedis.fr, which
# now redirects to a JS app rather than serving the API directly.
ENEDIS_OPENDATASOFT_BASE = "https://opendata.enedis.fr"
ENEDIS_THERMOSENSITIVITY_DATASET_ID = "consommation-electrique-par-secteur-dactivite-iris"
ENEDIS_MOST_RECENT_YEAR = "2024"

TREES_DATASET_ID = "les-arbres"  # opendata.paris.fr, titled "Arbres"
TREE_YOUNG_STAGE_LABEL = "Jeune (arbre)"

RNA_DATASET_ID = "repertoire-national-des-associations-ile-de-france"  # data.iledefrance.fr

# INSEE only exposes the current "base infra-communale" (population by
# IRIS) edition through a statistics page whose direct file URL changes
# every edition, same pattern as Filosofi above.
POPULATION_IRIS_PAGE = "https://www.insee.fr/fr/statistiques/8268806"

# IDF's own land-use survey (MOS), used as an artificialization proxy —
# see script 22's docstring for why this replaces IGN's OCS GE (no
# queryable vector API found for OCS GE, only WMTS/WMS tile services).
MOS_DATASET_ID = "mos-occupation-du-sol-2025-and-2021-en-79-postes-de-la-region-ile-de-france"
