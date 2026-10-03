"""Run every download/normalize script in order.

Uses subprocess rather than import because the scripts are numbered
(01_..., 02_...) and are meant to be run standalone, not imported as
modules. 01_iris_contours must succeed first since every other script
joins against its output (data/processed/iris_mgp.geojson, Phase 5's
Metropole du Grand Paris extent).

Note the order isn't strictly numeric: 11_compute_vulnerability_score.py
reads the outputs of 12, 15, 17, 21, 22 and 24 (added after it, but
merged in as either a scored sub-score input or unscored context), so
those must run first despite the lower number. 16/18_*_context.py are
context-only layers with no scoring dependency and can run anywhere;
19_street_lighting_context.py depends on 13's output specifically, so
it's listed right after it. 21_population_iris.py must run before both
11 (population-normalized thermal indicator) and 20 (per-1,000-resident
RNA rate), and 22_artificialization_mos.py must run before 11 (3rd
thermal indicator) — both listed early, right after the IRIS reference.
24_secondary_residences.py has no dependency on any other script's
output (just the IRIS reference), so it can run anywhere before 11;
listed alongside 21/22 since all three are the same
"context/normalization layer needed by 11" category.
25_overcrowding.py re-reads the INSEE file script 24 downloads, so it
runs right after it. 26_adaptive_capacity.py (Phase 8's separate
adaptive-capacity axis) reads 11's output and 25's, so it runs last among
the scoring steps — its output is a separate file, never an input to 11.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import config
import pipeline_policy as policy

METADATA_PATH = config.DATA_PROCESSED / "last_updated.json"
REPORT_PATH = config.DATA_PROCESSED / "run_report.json"

SCRIPT_ORDER = [
    "01_iris_contours.py",
    "21_population_iris.py",
    "22_artificialization_mos.py",
    "24_secondary_residences.py",
    "25_overcrowding.py",
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
    "26_adaptive_capacity.py",
    "35_key_figures.py",
    "38_routes_summary.py",
    "39_neighbourhood_files.py",
    "16_school_ac_context.py",
    "18_tree_age_context.py",
    "20_associational_density_context.py",
]


def run_script(script_name: str) -> tuple[int, str]:
    """Run one script, streaming its output; return (exit code, last lines)."""
    tail = deque(maxlen=40)
    proc = subprocess.Popen(
        [sys.executable, "-u", str(SCRIPTS_DIR / script_name)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    for line in proc.stdout:
        print(line, end="")
        tail.append(line)
    return proc.wait(), "".join(tail)


def iris_codes() -> set[str] | None:
    import geopandas as gpd

    if not config.IRIS_REFERENCE_PATH.exists():
        return None
    return set(gpd.read_file(config.IRIS_REFERENCE_PATH)["code_iris"].astype(str))


def write_run_metadata(generated_at: str, layer_dates: dict[str, str], context_failures: list[dict]) -> None:
    """last_updated.json: when the run finished ("generated_at", shown in
    every page footer) and when each layer was last successfully rebuilt
    ("layers") — a context layer kept from a previous run keeps its old
    date, which the site shows next to its figures. run_report.json lists
    the context failures for the workflow to open an issue.
    """
    metadata = {"generated_at": generated_at, "layers": dict(sorted(layer_dates.items()))}
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps({"generated_at": generated_at, "context_failures": context_failures}, indent=2), encoding="utf-8")
    print(f"\nWrote {METADATA_PATH.name} and {REPORT_PATH.name} ({len(context_failures)} context failure(s))")


def main():
    missing = [s for s in SCRIPT_ORDER if s not in policy.SCRIPTS]
    if missing:
        sys.exit(f"Scripts without a failure-policy family in pipeline_policy.SCRIPTS: {missing}")

    started = policy.now_iso()
    now = policy.parse_iso(started)
    layer_dates = policy.previous_layer_dates(METADATA_PATH)
    context_failures = []
    snapshot_dir = Path(tempfile.mkdtemp(prefix="underlaid-previous-layers-"))

    try:
        for script_name in SCRIPT_ORDER:
            family, layers = policy.SCRIPTS[script_name]
            print(f"\n=== Running {script_name} ({family}) ===")
            if family == "context":
                for layer in layers:
                    current = config.DATA_PROCESSED / layer.filename
                    if current.exists():
                        shutil.copy2(current, snapshot_dir / layer.filename)

            code, tail = run_script(script_name)
            if code == 0:
                for layer in layers:
                    layer_dates[layer.filename] = started
                continue

            if family in policy.BLOCKING_FAMILIES:
                print(f"\n{script_name} failed (exit code {code}) — {family} layer, blocking; stopping.")
                sys.exit(code)

            # Context layer: restore and keep the previous version if it is
            # still valid and recent enough; otherwise block like the others.
            reasons = []
            for layer in layers:
                kept = snapshot_dir / layer.filename
                target = config.DATA_PROCESSED / layer.filename
                if kept.exists():
                    shutil.copy2(kept, target)
                problem = policy.schema_problem(target, layer, iris_codes())
                if problem:
                    reasons.append(problem)
                elif policy.too_old(layer_dates.get(layer.filename), now):
                    reasons.append(
                        f"{layer.filename}: previous version from {layer_dates.get(layer.filename)} is older than "
                        f"{policy.MAX_CONTEXT_AGE_DAYS} days"
                    )
            if reasons:
                print(f"\n{script_name} failed and its previous output can't be kept: {reasons}; stopping.")
                sys.exit(code)

            print(f"\n{script_name} failed (exit code {code}) — context layer, previous version kept; continuing.")
            context_failures.append({
                "script": script_name,
                "exit_code": code,
                "layers_kept": {layer.filename: layer_dates.get(layer.filename) for layer in layers},
                "log_tail": tail,
            })
    finally:
        shutil.rmtree(snapshot_dir, ignore_errors=True)

    write_run_metadata(started, layer_dates, context_failures)


if __name__ == "__main__":
    main()
