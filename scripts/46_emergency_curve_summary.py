"""Method table of the emergency curve (typical Tuesday, every 2 hours).

Reads data/processed/routes_emergency_curve.json (per-neighbourhood curve,
scripts/analysis/curve_controls.py) and the published score for the
population, and writes, for each departure time and the inhabited
neighbourhoods (at least 50 residents, as everywhere on the site):
- the median of the neighbourhood values, without constraint and in a
  wheelchair ("more than 90 min" counted as the longest);
- the number of neighbourhoods at more than 90 min; at 0:00, 2:00 and 4:00,
  for the wheelchair, under both assumptions on stops and trips of unknown
  accessibility (not accessible / accessible), shown as a range.
Output: data/processed/emergency_curve_summary.json, copied to
frontend/public/data/ (read by the Method page).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import config

HOURS = list(range(0, 24, 2))
NIGHT = [0, 2, 4]
MIN_POPULATION = 50


def main():
    curve = json.loads((config.DATA_PROCESSED / "routes_emergency_curve.json").read_text(encoding="utf-8"))
    score = json.loads((config.DATA_PROCESSED / "vulnerability_score_iris.geojson").read_text(encoding="utf-8"))
    inhabited = {f["properties"]["code_iris"] for f in score["features"] if (f["properties"].get("population") or 0) >= MIN_POPULATION}
    rows = {code: v for code, v in curve["iris"].items() if code in inhabited}

    def column(offset, n):
        return np.array([[np.inf if v[offset + i] is None else v[offset + i] for i in range(n)] for v in rows.values()], dtype=float)

    free, wc, wc_yes = column(0, 12), column(12, 12), column(24, 3)

    def med(a):
        m = float(np.median(a))
        return None if not np.isfinite(m) else int(round(m))

    out = []
    for i, h in enumerate(HOURS):
        row = {
            "hour": h,
            "median_free": med(free[:, i]),
            "median_wheelchair": med(wc[:, i]),
            "over90_free": int(np.isinf(free[:, i]).sum()),
            "over90_wheelchair": int(np.isinf(wc[:, i]).sum()),
        }
        if h in NIGHT:
            j = NIGHT.index(h)
            row["median_wheelchair_unknown_yes"] = med(wc_yes[:, j])
            row["over90_wheelchair_unknown_yes"] = int(np.isinf(wc_yes[:, j]).sum())
        out.append(row)
    result = {"day": curve["layout"]["day"], "neighbourhoods": len(rows), "rows": out}
    path = config.DATA_PROCESSED / "emergency_curve_summary.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copy(path, config.PROJECT_ROOT / "frontend" / "public" / "data" / path.name)
    for r in out:
        print(r)
    print(f"{len(rows)} inhabited neighbourhoods")


if __name__ == "__main__":
    main()
