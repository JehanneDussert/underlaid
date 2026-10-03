"""Failure policy for scripts/run_all.py (decided 2026-10-01, "option 3").

Every pipeline script belongs to one family:

- "reference", "score", "means" — BLOCKING. If one fails, the run stops
  and nothing is published: the IRIS reference, the cumulative exposure
  score and the means-to-cope axis must never mix data from different
  runs.
- "context" — NOT BLOCKING, under guardrails. These layers are shown for
  information only (detail panel figures, context modal, QPV outline) and
  never enter the score. If one fails, its previous output is restored and
  kept, provided that:
    1. it exists and still has the expected schema (required columns,
       and for IRIS-grain layers exactly the current IRIS codes);
    2. it is not older than MAX_CONTEXT_AGE_DAYS (two quarters) — beyond
       that a stale layer would stay silently stale, so the failure blocks.
  The kept layer keeps its original date in last_updated.json["layers"]
  (displayed next to the figures on the site), and the failure is written
  to run_report.json so the workflow opens a GitHub issue.

Why: on 2026-10-01 two context-only sources (school IPS, Acceslibre)
broke upstream; under the old "everything blocks" rule they would have
held back the quarterly refresh of the whole score.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAX_CONTEXT_AGE_DAYS = 183  # two quarters
BLOCKING_FAMILIES = {"reference", "score", "means"}


@dataclass(frozen=True)
class Layer:
    filename: str
    required_columns: tuple[str, ...]
    iris_grain: bool = True


# script -> (family, layers it writes). Layers are only those the script
# WRITES; e.g. script 19 also reads street_lighting_iris.geojson (from 13).
SCRIPTS: dict[str, tuple[str, tuple[Layer, ...]]] = {
    "01_iris_contours.py": ("reference", (Layer("iris_mgp.geojson", ("code_iris",)),)),
    "21_population_iris.py": ("score", (Layer("population_iris.geojson", ("code_iris", "population")),)),
    "22_artificialization_mos.py": ("score", (Layer("artificialization_iris.geojson", ("code_iris", "pct_artificialized")),)),
    "24_secondary_residences.py": ("means", (Layer("secondary_residences_iris.geojson", ("code_iris", "pct_secondary_residences")),)),
    "25_overcrowding.py": ("means", (Layer("overcrowding_iris.geojson", ("code_iris", "pct_overcrowded")),)),
    "02_icu_sat4bdnb.py": ("score", (Layer("icu_iris.geojson", ("code_iris",)),)),
    "03_cool_spots_facilities.py": ("score", (Layer("cool_spots_facilities_iris.geojson", ("code_iris",)),)),
    "04_cool_spots_green_areas.py": ("score", (Layer("cool_spots_green_iris.geojson", ("code_iris", "pct_cool_green_area")),)),
    "05_air_noise.py": ("score", (Layer("air_noise_iris.geojson", ("code_iris", "air_noise_coexposure_class")),)),
    "06_bpe.py": ("context", (Layer("bpe_iris.geojson", ("code_iris",)),)),
    "07_equipment_access_200m.py": ("context", (Layer("equipment_access_iris.geojson", ("code_iris",)),)),
    "08_income_filosofi.py": ("means", (Layer("income_iris.geojson", ("code_iris", "median_income")),)),
    "09_social_index_schools.py": ("context", (Layer("social_index_iris.geojson", ("code_iris", "social_index_schools", "social_index_middle_schools")),)),
    "10_energy_performance.py": ("score", (Layer("energy_performance_iris.geojson", ("code_iris", "pct_dpe_fg")),)),
    "12_accessibility_erp.py": ("context", (Layer("accessibility_iris.geojson", ("code_iris", "pct_pmr_accessible")),)),
    "13_street_lighting.py": ("context", (Layer("street_lighting_iris.geojson", ("code_iris",)),)),
    "19_street_lighting_context.py": ("context", (Layer("street_lighting_context_arrondissement.geojson", ("insee_com",), iris_grain=False),)),
    "14_qpv_boundaries.py": ("context", (Layer("qpv_boundaries_mgp.geojson", (), iris_grain=False),)),
    "15_pedestrian_paths.py": ("context", (Layer("pedestrian_paths_iris.geojson", ("code_iris", "footway_density_m_per_km2")),)),
    "17_enedis_thermosensitivity.py": ("score", (Layer("enedis_thermosensitivity_iris.geojson", ("code_iris", "pct_thermosensitive")),)),
    "11_compute_vulnerability_score.py": ("score", (Layer("vulnerability_score_iris.geojson", ("code_iris", "cumulative_vulnerability_score")),)),
    "26_adaptive_capacity.py": ("means", (Layer("adaptive_capacity_iris.json", (), iris_grain=False),)),
    "35_key_figures.py": ("means", (Layer("key_figures.json", (), iris_grain=False),)),
    # Home-page travel times: medians of the routes files (script 36, run by
    # hand), recomputed each quarter because "inhabited" follows the score.
    "38_routes_summary.py": ("means", (Layer("routes_summary.json", (), iris_grain=False),)),
    "16_school_ac_context.py": ("context", (Layer("school_ac_context_arrondissement.geojson", ("insee_com",), iris_grain=False),)),
    "18_tree_age_context.py": ("context", (Layer("tree_age_context_arrondissement.geojson", ("insee_com",), iris_grain=False),)),
    "20_associational_density_context.py": ("context", (Layer("associational_density_context_commune.geojson", ("insee_com",), iris_grain=False),)),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def previous_layer_dates(metadata_path: Path) -> dict[str, str]:
    """Per-layer dates from the previous run. Older metadata files only
    carried a global "generated_at": every layer then dates from it."""
    if not metadata_path.exists():
        return {}
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    layers = dict(data.get("layers", {}))
    fallback = data.get("generated_at")
    if fallback:
        for _, (_, outputs) in SCRIPTS.items():
            for layer in outputs:
                layers.setdefault(layer.filename, fallback)
    return layers


def schema_problem(path: Path, layer: Layer, iris_codes: set[str] | None) -> str | None:
    """None if the kept file is usable, else a human-readable reason."""
    if not path.exists():
        return f"{layer.filename}: no previous version to keep"
    try:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            return None
        import geopandas as gpd

        gdf = gpd.read_file(path)
    except Exception as exc:  # noqa: BLE001 — any unreadable file is a schema failure
        return f"{layer.filename}: previous version unreadable ({exc})"
    missing = [c for c in layer.required_columns if c not in gdf.columns]
    if missing:
        return f"{layer.filename}: previous version lacks columns {missing}"
    if len(gdf) == 0:
        return f"{layer.filename}: previous version is empty"
    if layer.iris_grain and iris_codes is not None and set(gdf["code_iris"].astype(str)) != iris_codes:
        return f"{layer.filename}: previous version no longer matches the current IRIS codes"
    return None


def too_old(layer_date: str | None, now: datetime) -> bool:
    if not layer_date:
        return True
    return now - parse_iso(layer_date) > timedelta(days=MAX_CONTEXT_AGE_DAYS)
