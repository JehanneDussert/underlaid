"""Download and normalize residential electrical thermosensitivity per IRIS.

Source: Enedis' open data portal, dataset "Consommation et
thermosensibilite annuelles d'electricite par secteur d'activite a la
maille IRIS" — annual electricity consumption/thermosensitivity by IRIS
and activity sector, already at IRIS granularity (no spatial join
needed, just an attribute join on code_iris, like Filosofi in step 08).

The portal migrated from the old data.enedis.fr (which now just serves
the JS app, not the API) to opendata.enedis.fr, running the same
"data-fair" platform as ADEME's DPE dataset in step 10 — same query
style (`qs` Lucene filter, cursor-based pagination via the `next` link).

Indicator kept: part_thermosensible, the share of a zone's residential
electricity consumption that's temperature-sensitive (winter heating
load). High thermosensitivity means electricity use swings sharply with
temperature — a proxy for poorly-insulated, electric-heating-dependent
housing. Intended use: a second housing sub-score indicator alongside
DPE F/G share — poor insulation shows up in both directions (expensive
to heat in winter, hard to keep cool in summer without similarly
expensive air conditioning).

Enedis already enforces its own privacy floor (aggregates hidden below
10 active sites per zone) — confirmed by inspection, every Paris
residential row has nb_sites >= 10, so no additional sample-size
masking is needed here on top of what the source already does. Not
re-verified for 92/93/94 specifically, but the same source-side floor
applies uniformly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import requests

import config
from utils.download import DEFAULT_TIMEOUT
from utils.geo import check_unmatched_codes, load_iris_reference
from utils.io import save_geojson

LINES_URL = f"{config.ENEDIS_OPENDATASOFT_BASE}/data-fair/api/v1/datasets/{config.ENEDIS_THERMOSENSITIVITY_DATASET_ID}/lines"
PAGE_SIZE = 1_000
SELECT_FIELDS = "code_iris,nb_sites,part_thermosensible,taux_de_chauffage_electrique"


def fetch_mgp_residential_records() -> pd.DataFrame:
    dept_query = " OR ".join(f"code_departement:{d}" for d in config.MGP_DEP_CODES)
    params = {
        "qs": f"({dept_query}) AND annee:{config.ENEDIS_MOST_RECENT_YEAR} AND code_grand_secteur:RESIDENTIEL",
        "select": SELECT_FIELDS,
        "size": PAGE_SIZE,
    }
    url = LINES_URL
    rows = []
    while url:
        response = requests.get(url, params=params if url == LINES_URL else None, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload.get("results", []))
        url = payload.get("next")
        print(f"  fetched {len(rows)} Enedis IRIS records so far...")
    return pd.DataFrame(rows)


def normalize(df: pd.DataFrame):
    df = df.rename(columns={
        "nb_sites": "enedis_sample_sites",
        "part_thermosensible": "pct_thermosensitive",
        "taux_de_chauffage_electrique": "pct_electric_heating",
    })
    # part_thermosensible/taux_de_chauffage_electrique come through as a
    # 0-100 share; keep the same 0-100 convention as the DPE/PMR shares
    # elsewhere in this pipeline (frontend divides by 100 when needed) —
    # actually those are stored as 0-1 fractions (see pct_dpe_fg), so
    # convert here to stay consistent with the rest of the scoring input.
    for col in ("pct_thermosensitive", "pct_electric_heating"):
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0

    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_LATLON)
    check_unmatched_codes(df, iris, config.IRIS_JOIN_COLUMN)

    keep_cols = [config.IRIS_JOIN_COLUMN, "enedis_sample_sites", "pct_thermosensitive", "pct_electric_heating"]
    return iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(df[keep_cols], on=config.IRIS_JOIN_COLUMN, how="left")


def main():
    df = fetch_mgp_residential_records()
    result = normalize(df)
    save_geojson(result, config.DATA_PROCESSED / "enedis_thermosensitivity_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
