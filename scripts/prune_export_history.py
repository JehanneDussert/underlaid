"""Snapshot the current score output into a dated history folder, and
keep only the most recent few.

Not part of scripts/run_all.py's numbered pipeline: this is a publishing
concern (called by the GitHub Actions workflow right before a run's
output is accepted and copied to frontend/public/data), not a data
transformation step. Kept as its own script rather than inline shell in
the workflow so it's testable and runnable locally the same way.

Runs with: python scripts/prune_export_history.py --keep 4
"""
import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

DEFAULT_KEEP = 4
# Snapshotting the scored output plus its own metadata is enough to
# answer "what did the site show on date X" and to roll back a bad
# automated run — the ~20 intermediate per-indicator layers are
# reproducible by re-running the pipeline against the same raw sources
# and aren't needed to explain a past published state.
FILES_TO_SNAPSHOT = ["vulnerability_score_iris.geojson", "last_updated.json"]


def snapshot(processed_dir: Path, history_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest = history_dir / stamp
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES_TO_SNAPSHOT:
        src = processed_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)
    print(f"Snapshotted {FILES_TO_SNAPSHOT} to {dest}")
    return dest


def prune(history_dir: Path, keep: int) -> list[Path]:
    if not history_dir.exists():
        return []
    dated_dirs = sorted((p for p in history_dir.iterdir() if p.is_dir()), key=lambda p: p.name)
    to_remove = dated_dirs[:-keep] if keep > 0 else dated_dirs
    for old_dir in to_remove:
        shutil.rmtree(old_dir)
        print(f"Removed old history snapshot {old_dir}")
    return to_remove


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=config.DATA_PROCESSED)
    parser.add_argument("--history-dir", type=Path, default=config.PROJECT_ROOT / "data" / "history")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="How many dated snapshots to retain")
    args = parser.parse_args()

    snapshot(args.processed_dir, args.history_dir)
    prune(args.history_dir, args.keep)


if __name__ == "__main__":
    main()
