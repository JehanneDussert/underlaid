"""Per-commune data files for the "Votre quartier" page (redesign D4).

The page used to load the whole published score (5 MB) to find one
neighbourhood. It now loads one small file: the commune of the address
(the address API gives its INSEE code; Paris by arrondissement), which
holds the outlines of its neighbourhoods (to find the one containing the
address) and everything the page shows about each of them:

- exposures: for heat, air and noise, housing and access to care, the
  quarter (4 = most affected), the status (insufficient data) and the rank
  share = share of inhabited neighbourhoods with a lower (more favourable)
  sub-score, for "Sur 10 quartiers, N sont moins exposés que le vôtre";
- residents' means (separate axis): third, median income, overcrowding,
  second homes;
- travel times (routes, script 36; Tuesday 10:00) for the three modes of
  the site: free (standard), slow, wheelchair (step-free, unknown = not
  accessible), plus the emergency department at night (1:00) and the
  nearest station on foot; the everyday places of the second routing run
  when it exists (else absent: "pas encore calculé"); for Paris
  neighbourhoods, public toilets (all, wheelchair-accessible, open 24 h)
  and drinking fountains (script 41).

Plus index.json: for part 3 of the page ("Les deux à la fois"), each
inhabited neighbourhood's number of exposures in the worst quarter (0-3)
and its access-to-care rank, and the count of neighbourhoods both highly
exposed (2 of the 3 exposures or more) and in the worst quarter for
access to care.

Inhabited = at least 50 residents (as everywhere). Output:
data/processed/quartiers/<insee_com>.json and index.json, copied to
frontend/public/data/quartiers/.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import config

MIN_POPULATION = 50
OUT = config.DATA_PROCESSED / "quartiers"
SUBSCORES = ["thermal", "pollution", "housing", "access_care"]
EXPOSURES = ["thermal", "pollution", "housing"]
MODES = {"free": "standard", "slow": "slow", "wheelchair": "step_free_no"}


def round_coords(obj, digits=6):
    """Coordinate precision of the published score (6 decimals, ~11 cm);
    shapes are never simplified (the address lookup needs exact outlines)."""
    if isinstance(obj, list):
        return [round_coords(x, digits) for x in obj]
    return round(obj, digits) if isinstance(obj, float) else obj


def load(name):
    path = config.DATA_PROCESSED / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def routes_by_iris(data, types=None):
    """{code: {mode: {type: minutes or None}}} from a routes slot file."""
    if data is None:
        return {}
    blocks, all_types = data["layout"]["blocks"], data["layout"]["types"]
    types = types or all_types
    out = {}
    for code, row in data["iris"].items():
        out[code] = {
            mode: {t: row[blocks.index(f"time:{profile}") * len(all_types) + all_types.index(t)] for t in types}
            for mode, profile in MODES.items()
        }
    return out


def main():
    score = load("vulnerability_score_iris.geojson")
    capacity = {r["code_iris"]: r for r in load("adaptive_capacity_iris.json")["iris"]}
    day = routes_by_iris(load("routes_iris_tue10.json"))
    night = routes_by_iris(load("routes_iris_tue01.json"), ["emergency"])
    stations_data = load("routes_stations_iris.json")
    places = routes_by_iris(load("routes_neighbourhood_tue10.json"))
    # Public toilets and drinking fountains, Paris only (script 41).
    paris_places = routes_by_iris(load("routes_paris_tue10.json"))

    props = {f["properties"]["code_iris"]: f["properties"] for f in score["features"]}
    inhabited = {c for c, p in props.items() if (p.get("population") or 0) >= MIN_POPULATION}
    # Ranks against inhabited neighbourhoods only (same reference as the
    # quartile thresholds); every neighbourhood gets a rank.
    ranks = {}
    for k in SUBSCORES:
        ref_values = {c: props[c].get(f"subscore_{k}") for c in inhabited}
        ref = np.sort(np.array([v for v in ref_values.values() if v is not None], dtype=float))
        ranks[k] = {
            c: (None if p.get(f"subscore_{k}") is None else round(float(np.searchsorted(ref, p[f"subscore_{k}"], side="left")) / len(ref), 3))
            for c, p in props.items()
        }

    by_commune = {}
    index_points = []
    both = 0
    for f in score["features"]:
        p = f["properties"]
        code = p["code_iris"]
        quarters = {k: p.get(f"subscore_{k}_quartile") for k in SUBSCORES}
        n_exp = sum(1 for k in EXPOSURES if quarters[k] == 4)
        rec = {
            "code": code,
            "name": p["nom_iris"],
            "commune": p["nom_com"],
            "population": None if p.get("population") is None else round(p["population"]),
            "inhabited": code in inhabited,
            "score": p.get("cumulative_vulnerability_score"),
            "exposures": {
                k: {"quarter": None if quarters[k] is None else int(quarters[k]), "rank": ranks[k][code], "status": p.get(f"subscore_{k}_status", "ok")} for k in SUBSCORES
            },
            "means": None,
            "geometry": {"type": f["geometry"]["type"], "coordinates": round_coords(f["geometry"]["coordinates"])},
        }
        cap = capacity.get(code)
        if cap and cap.get("capacity_class") is not None:
            rec["means"] = {
                "third": cap["capacity_class"],
                "median_income": p.get("median_income"),
                "pct_overcrowded": cap.get("pct_overcrowded"),
                "pct_secondary_residences": p.get("pct_secondary_residences"),
            }
        if code in day:
            rec["times"] = day[code]
        if code in night:
            rec["night_emergency"] = {m: v["emergency"] for m, v in night[code].items()}
        if stations_data and code in stations_data["iris"]:
            row = stations_data["iris"][code]
            rec["station"] = {m: row[stations_data["profiles"].index(prof)] for m, prof in MODES.items()}
        if code in places:
            rec["places"] = places[code]
        if code.startswith("75") and code in paris_places:
            rec["paris_places"] = paris_places[code]
        by_commune.setdefault(str(p["insee_com"]), []).append(rec)

        if code in inhabited and ranks["access_care"][code] is not None and all(quarters[k] is not None for k in EXPOSURES):
            index_points.append([code, n_exp, ranks["access_care"][code]])
            if n_exp >= 2 and quarters["access_care"] == 4:
                both += 1

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for com, recs in by_commune.items():
        (OUT / f"{com}.json").write_text(json.dumps({"commune": com, "iris": recs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    index = {
        "n_iris": len(props),
        "n_inhabited": len(inhabited),
        "highly_exposed_and_worst_care": both,
        "points": index_points,
        "places_computed": bool(places),
    }
    (OUT / "index.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    sizes = [f.stat().st_size for f in OUT.glob("*.json")]
    print(f"{len(by_commune)} commune files, {sum(sizes) / 1e6:.1f} MB in all, largest {max(sizes) / 1e3:.0f} kB; "
          f"{both} neighbourhoods highly exposed and in the worst quarter for care; places computed: {bool(places)}")


if __name__ == "__main__":
    main()
