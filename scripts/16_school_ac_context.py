"""Build the "air-conditioned schools" context layer, by arrondissement.

Unlike every other script in this project, there is no open dataset or
API for this: the figures below were manually compiled from press
articles covering arrondissement mayors' communications during the June
2026 heatwave (searched 2026-07-11). This is a CONTEXT layer only, at
arrondissement granularity — never joined to code_iris or fed into the
cumulative score, for the same reason median life expectancy and heatwave
excess-mortality data are kept out of it: the grain is too coarse for
IRIS-level comparison.

Coverage is incomplete by construction — only the arrondissements whose
mayor's office or local press explicitly published a number are filled
in; the rest are null rather than guessed. Re-running this script does
nothing (there's nothing to download); update SCHOOL_AC_DATA by hand as
better/newer figures surface, and update the source citations with them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.io import save_geojson

# code_insee: (schools with AC/coolers as of source date, total schools if
# known, free-text note in English and French, source).
# "coolers" = rafraichisseurs (evaporative, weaker than true AC) reported
# separately from climatiseurs where the source distinguished them.
# note_fr is not a translation exercise — the source articles were
# originally in French, so it's written back to match them closely,
# while note (English) is its own rendering; the UI picks whichever
# matches the active locale.
SCHOOL_AC_DATA = {
    "75108": {
        "ac_schools": 2,
        "total_schools": 9,
        "note": (
            "Only 2 city-supplied air conditioners for 9 schools as of the "
            "article date; the arrondissement mairie separately ordered "
            "40 portable units (~EUR20,000) to cover the shortfall."
        ),
        "note_fr": (
            "Seulement 2 climatiseurs fournis par la Ville pour 9 écoles à la "
            "date de l'article ; la mairie d'arrondissement a commandé "
            "séparément 40 unités mobiles (~20 000€) pour combler le manque."
        ),
        "source": "https://www.catherinelecuyer.fr/post/canicule-à-paris-la-mairie-du-8-e-agit",
    },
    "75111": {
        "ac_schools": None,
        "total_schools": None,
        "note": "All schools in the arrondissement reported as equipped (no exact count published).",
        "note_fr": "Toutes les écoles de l'arrondissement déclarées équipées (aucun chiffre exact publié).",
        "source": "https://mairie11.paris.fr/pages/canicule-bons-reflexes-et-ilots-de-fraicheur-35569",
    },
    "75119": {
        "ac_schools": 36,
        "total_schools": None,
        "note": "36 schools equipped with air conditioners, plus 10 more with evaporative coolers, as of 2026-06-25.",
        "note_fr": "36 écoles équipées de climatiseurs, plus 10 équipées de rafraîchisseurs, au 25/06/2026.",
        "source": "https://mairie19.paris.fr/pages/canicule-vigilance-orange-35618",
    },
}

# Reported as a single aggregate across 6 arrondissements, not broken out
# individually by the source — kept as a citywide note rather than forced
# into per-arrondissement rows.
WEST_BLOC_NOTE = (
    "Reported as a group (6e, 7e, 8e, 15e, 16e, 17e): only 36 city-supplied "
    "air conditioners shared across these 6 arrondissements' 168 schools "
    "combined, as of the article date."
)
WEST_BLOC_NOTE_FR = (
    "Signalé en groupe (6e, 7e, 8e, 15e, 16e, 17e) : seulement 36 climatiseurs "
    "fournis par la Ville partagés entre les 168 écoles de ces 6 "
    "arrondissements réunis, à la date de l'article."
)
WEST_BLOC_SOURCE = "https://info.fr/paris-gregoire-ouvre-parcs-24h24-climatiseurs-ecoles-canicule/"

CITYWIDE_NOTE = (
    "Citywide plan: 620 schools, 1,200+ portable air conditioners ordered, "
    "150 delivered first (prioritizing the hottest nursery schools), "
    "announced 2026-06-20. Portable units only — explicitly described by "
    "the mayor as not a structural building-renovation response."
)
CITYWIDE_NOTE_FR = (
    "Plan municipal : 620 écoles, plus de 1 200 climatiseurs d'appoint "
    "commandés, 150 livrés en premier (priorité aux maternelles les plus "
    "chaudes), annoncé le 20/06/2026. Unités mobiles uniquement — "
    "explicitement décrites par le maire comme n'étant pas une réponse "
    "structurelle de rénovation du bâti."
)
CITYWIDE_SOURCE = "https://www.cnews.fr/france/2026-06-20/un-climatiseur-sera-livre-dans-chaque-ecole-de-paris-dici-la-fin-de-la-semaine"


def dissolve_arrondissements() -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)
    iris["insee_com"] = iris["insee_com"].astype(str)  # comes in as int32; SCHOOL_AC_DATA keys are strings
    arrondissements = iris.dissolve(by="insee_com", as_index=False).rename(columns={"nom_com": "nom_arrondissement"})
    return arrondissements[["insee_com", "nom_arrondissement", "geometry"]]


def attach_context(arrondissements: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    arrondissements["ac_schools_reported"] = arrondissements["insee_com"].map(
        lambda code: SCHOOL_AC_DATA.get(code, {}).get("ac_schools")
    )
    arrondissements["total_schools_reported"] = arrondissements["insee_com"].map(
        lambda code: SCHOOL_AC_DATA.get(code, {}).get("total_schools")
    )
    arrondissements["note"] = arrondissements["insee_com"].map(
        lambda code: SCHOOL_AC_DATA.get(code, {}).get("note")
    )
    arrondissements["note_fr"] = arrondissements["insee_com"].map(
        lambda code: SCHOOL_AC_DATA.get(code, {}).get("note_fr")
    )
    arrondissements["source_url"] = arrondissements["insee_com"].map(
        lambda code: SCHOOL_AC_DATA.get(code, {}).get("source")
    )

    west_bloc = {"75106", "75107", "75108", "75115", "75116", "75117"}
    in_west_bloc = arrondissements["insee_com"].isin(west_bloc) & arrondissements["note"].isna()
    arrondissements.loc[in_west_bloc, "note"] = WEST_BLOC_NOTE
    arrondissements.loc[in_west_bloc, "note_fr"] = WEST_BLOC_NOTE_FR
    arrondissements.loc[in_west_bloc, "source_url"] = WEST_BLOC_SOURCE

    arrondissements["citywide_note"] = CITYWIDE_NOTE
    arrondissements["citywide_note_fr"] = CITYWIDE_NOTE_FR
    arrondissements["citywide_source_url"] = CITYWIDE_SOURCE
    return arrondissements


def main():
    arrondissements = dissolve_arrondissements()
    result = attach_context(arrondissements)
    save_geojson(
        result,
        config.DATA_PROCESSED / "school_ac_context_arrondissement.geojson",
        required_cols=["insee_com", "geometry"],
    )
    n_documented = result["note"].notna().sum()
    print(f"{n_documented}/20 arrondissements have at least a qualitative note; see column 'note' for gaps.")


if __name__ == "__main__":
    main()
