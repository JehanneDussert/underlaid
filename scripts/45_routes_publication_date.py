"""Records the date of the travel-time files in last_updated.json.

Travel times (scripts 34, 36, 38, 39) are computed outside the quarterly
run (scripts/run_all.py), so "generated_at" (the date of that run, also the
reference used to flag stale context layers) does not move when they are
published. This script adds their date to "layers" and writes
"published_at": the latest date among all layers, which the site footer
shows as the date of the latest published data.

Usage (after publishing new travel times):
    python scripts/45_routes_publication_date.py --at 2026-10-07T02:11:00Z
Without --at, the current time is used. Updates data/processed/ and
frontend/public/data/.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROUTE_FILES = [
    "routes_iris_tue10.json", "routes_iris_tue21.json", "routes_iris_tue01.json", "routes_iris_sun10.json",
    "routes_neighbourhood_tue10.json", "routes_paris_tue10.json", "routes_stations_iris.json",
    "routes_summary.json", "quartiers",
]
TARGETS = [config.DATA_PROCESSED / "last_updated.json", config.PROJECT_ROOT / "frontend" / "public" / "data" / "last_updated.json"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", help="ISO date (UTC) of the travel-time publication")
    at = ap.parse_args().at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for path in TARGETS:
        if not path.exists():
            continue
        meta = json.loads(path.read_text(encoding="utf-8"))
        layers = meta.setdefault("layers", {})
        for name in ROUTE_FILES:
            layers[name] = at
        meta["layers"] = dict(sorted(layers.items()))
        meta["published_at"] = max([meta["generated_at"], *layers.values()])
        path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(f"{path}: published_at {meta['published_at']}")


if __name__ == "__main__":
    main()
