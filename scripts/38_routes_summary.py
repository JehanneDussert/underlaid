"""Figures quoted on the home page from the routes results (script 36).

The home page shows a handful of travel times in sentences and on the
network illustration ("Mairie 14 min", "11 minutes to an accessible stop
in Paris, against 3"). They are computed here from the published routes
files, never typed by hand, like key_figures.json (script 35).

Definitions (pre-registration of the routes, CLAUDE.md):
- inhabited neighbourhood: IRIS with at least 50 residents;
- metropolis median = median of the neighbourhood values (each one a
  population-weighted median of its 200 m cells), Tuesday 13 October
  2026, 10:00; a neighbourhood "more than 90 min" (null) counts as +inf;
- profiles shown: standard ("Sans contrainte"), slow ("Marche lente"),
  step-free, unknown = not accessible ("Fauteuil roulant");
- stations: nearest heavy-network stop point on foot (metro, RER, train,
  tram), and for the wheelchair profile the nearest accessible one;
- night: Tuesday 1:00, on foot and by public transport, emergency
  departments only (display rule of 3 October 2026);
- everyday places (script 37) added to the day medians when published;
  Paris toilets and fountains (script 41) as medians of Paris
  neighbourhoods only (paris_median).

Output: data/processed/routes_summary.json, copied to frontend/public/data/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import config

MIN_POPULATION = 50
DEPARTMENTS = ["75", "92", "93", "94"]
MODES = {"free": "standard", "slow": "slow", "wheelchair": "step_free_no"}
OUT = config.DATA_PROCESSED / "routes_summary.json"


def median(values) -> int | None:
    v = np.array([np.inf if x is None else x for x in values], dtype=float)
    if len(v) == 0:
        return None
    m = float(np.median(v))
    return None if not np.isfinite(m) else int(round(m))


def share_above(values, minutes: int) -> float:
    v = np.array([np.inf if x is None else x for x in values], dtype=float)
    return round(100 * float((v > minutes).mean()), 1)


def main():
    score = json.loads((config.DATA_PROCESSED / "vulnerability_score_iris.geojson").read_text(encoding="utf-8"))
    population = {f["properties"]["code_iris"]: f["properties"].get("population") or 0 for f in score["features"]}
    inhabited = lambda code: population.get(code, 0) >= MIN_POPULATION

    def slot_file(slot, prefix="routes_iris"):
        d = json.loads((config.DATA_PROCESSED / f"{prefix}_{slot}.json").read_text(encoding="utf-8"))
        blocks, types = d["layout"]["blocks"], d["layout"]["types"]
        def value(row, profile, type_):
            return row[blocks.index(f"time:{profile}") * len(types) + types.index(type_)]
        return {c: r for c, r in d["iris"].items() if inhabited(c)}, types, value

    rows, types, value = slot_file("tue10")
    day = {mode: {t: median(value(r, profile, t) for r in rows.values()) for t in types} for mode, profile in MODES.items()}
    # Everyday places of the second run (script 37), when published.
    if (config.DATA_PROCESSED / "routes_neighbourhood_tue10.json").exists():
        prow, ptypes, pvalue = slot_file("tue10", "routes_neighbourhood")
        for mode, profile in MODES.items():
            day[mode].update({t: median(pvalue(r, profile, t) for r in prow.values()) for t in ptypes})
    # Paris toilets and fountains (script 41): medians of Paris
    # neighbourhoods only (no data elsewhere).
    paris = None
    if (config.DATA_PROCESSED / "routes_paris_tue10.json").exists():
        qrow, qtypes, qvalue = slot_file("tue10", "routes_paris")
        qrow = {c: r for c, r in qrow.items() if c.startswith("75")}
        paris = {mode: {t: median(qvalue(r, profile, t) for r in qrow.values()) for t in qtypes} for mode, profile in MODES.items()}

    st = json.loads((config.DATA_PROCESSED / "routes_stations_iris.json").read_text(encoding="utf-8"))
    st_rows = {c: r for c, r in st["iris"].items() if inhabited(c)}
    stations = {
        mode: {d: median(r[st["profiles"].index(profile)] for c, r in st_rows.items() if c[:2] == d) for d in DEPARTMENTS}
        for mode, profile in MODES.items()
    }

    night_rows, _, night_value = slot_file("tue01")
    night = {}
    for mode, profile in MODES.items():
        groups = {"75": [], "inner_suburbs": []}
        for c, r in night_rows.items():
            groups["75" if c[:2] == "75" else "inner_suburbs"].append(night_value(r, profile, "emergency"))
        night[mode] = {
            g: {"median": median(v), "over30_pct": share_above(v, 30), "over45_pct": share_above(v, 45), "n": len(v)}
            for g, v in groups.items()
        }

    out = {
        "reference": "Tuesday 13 October 2026, 10:00 (night: 1:00)",
        "day_metropolis_median": day,
        "station_median_by_department": stations,
        "night_emergency": night,
        "paris_median": paris,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
