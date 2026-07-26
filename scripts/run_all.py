"""Run every download/normalize script in order.

Uses subprocess rather than import because the scripts are numbered
(01_..., 02_...) and are meant to be run standalone, not imported as
modules. 01_iris_contours must succeed first since every other script
joins against its output (data/processed/iris_mgp.geojson, Phase 5's
Metropole du Grand Paris extent).

Note the order isn't strictly numeric: 11_compute_vulnerability_score.py
reads the outputs of 12, 15, 17, 21 and 22 (added after it, but wired
into the "thermal"/"access"/"housing" sub-scores), so those must run
first despite the lower number. 16/18_*_context.py are context-only
layers with no scoring dependency and can run anywhere;
19_street_lighting_context.py depends on 13's output specifically, so
it's listed right after it. 21_population_iris.py must run before both
11 (population-normalized thermal indicator) and 20 (per-1,000-resident
RNA rate), and 22_artificialization_mos.py must run before 11 (3rd
thermal indicator) — both listed early, right after the IRIS reference.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import config

SCRIPT_ORDER = [
    "01_iris_contours.py",
    "21_population_iris.py",
    "22_artificialization_mos.py",
    "02_icu_sat4bdnb.py",
    "03_cool_spots_facilities.py",
    "04_cool_spots_green_areas.py",
    "05_air_noise.py",
    "06_bpe.py",
    "07_equipment_access_200m.py",
    "08_income_filosofi.py",
    "09_social_index_schools.py",
    "10_energy_performance.py",
    "12_accessibility_erp.py",
    "13_street_lighting.py",
    "19_street_lighting_context.py",
    "14_qpv_boundaries.py",
    "15_pedestrian_paths.py",
    "17_enedis_thermosensitivity.py",
    "11_compute_vulnerability_score.py",
    "16_school_ac_context.py",
    "18_tree_age_context.py",
    "20_associational_density_context.py",
]


def write_run_metadata():
    """Records when this run finished — the only way anyone citing a
    specific IRIS by example (Drancy, etc.) can know which snapshot of
    the score they're looking at, since the score itself is explicitly
    not a fixed, final number (see CLAUDE.md/SCORING.md). Written here
    rather than inside 11_compute_vulnerability_score.py because it
    describes the whole run, not just the scoring step.
    """
    metadata = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    path = config.DATA_PROCESSED / "last_updated.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"\nWrote run metadata to {path}: {metadata}")


def main():
    for script_name in SCRIPT_ORDER:
        print(f"\n=== Running {script_name} ===")
        result = subprocess.run([sys.executable, str(SCRIPTS_DIR / script_name)])
        if result.returncode != 0:
            print(f"\n{script_name} failed (exit code {result.returncode}); stopping.")
            sys.exit(result.returncode)
    write_run_metadata()


if __name__ == "__main__":
    main()
