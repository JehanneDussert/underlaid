"""Emergency departments by departure time: the table of the Method page.

For the nearest emergency department, at each departure time (Tuesday
10:00, Tuesday 21:00, Sunday 10:00, Tuesday 1:00), over the inhabited
neighbourhoods (>= 50 residents, as in script 39):
- median of the neighbourhood values, without constraint and in a
  wheelchair (published wheelchair profile: unknown accessibility counted
  as not accessible);
- share of neighbourhoods, then of residents, more than 45 minutes away in
  a wheelchair.
Also the figures quoted in the note under the table: share more than
45 minutes away without constraint (day and night), and at night in a
wheelchair with unknown accessibility counted as accessible.

A neighbourhood not reached within 90 minutes (no value) counts as more
than 45 minutes away and as +infinity in the medians, never as missing
(routes pre-registration of 2 October 2026, point 3).

Also, for the same note: the Noctilien trips running between 1:00 and 2:00
on the night of Monday 12 to Tuesday 13 October 2026, by declared
wheelchair accessibility (GTFS wheelchair_accessible: 1 yes, 2 no, 0 or
empty unknown), read from the raw IDFM GTFS if it is present.

Reads data/processed/routes_iris_{tue10,tue21,sun10,tue01}.json (script 36),
the population of data/processed/vulnerability_score_iris.geojson and
data/raw/gtfs/IDFM-gtfs.zip (optional; another path with IDFM_GTFS_ZIP).
Output printed and written to data/interim/analysis/emergency_time_slots.txt.
"""
import csv
import io
import json
import math
import os
import re
import zipfile
from collections import Counter
import statistics
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config

MIN_POPULATION = 50  # same inhabited threshold as script 39
OVER = 45
SLOTS = [("tue10", "Mardi 10 h"), ("tue21", "Mardi 21 h"), ("sun10", "Dimanche 10 h"), ("tue01", "Nuit (1 h)")]
FREE, WHEELCHAIR, WHEELCHAIR_YES = "time:standard", "time:step_free_no", "time:step_free_yes"
OUT = config.DATA_INTERIM / "analysis" / "emergency_time_slots.txt"


def load(name):
    with open(config.DATA_PROCESSED / name, encoding="utf-8") as fh:
        return json.load(fh)


def emergency_times(slot):
    """{code_iris: {block: minutes or None}} for the emergency department."""
    data = load(f"routes_iris_{slot}.json")
    blocks, types = data["layout"]["blocks"], data["layout"]["types"]
    e, n = types.index("emergency"), len(types)
    out = {}
    for code, row in data["iris"].items():
        out[code] = {b: row[i * n + e] for i, b in enumerate(blocks) if b.startswith("time:")}
    return out


def noctilien_accessibility():
    """Counter of wheelchair_accessible for Noctilien trips running 1:00-2:00."""
    path = Path(os.environ.get("IDFM_GTFS_ZIP", config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"))
    if not path.exists():
        return None
    gtfs = zipfile.ZipFile(path)

    def rows(name):
        return csv.DictReader(io.TextIOWrapper(gtfs.open(name), encoding="utf-8-sig"))

    noctilien = {r["route_id"] for r in rows("routes.txt") if re.match(r"^N\d", r.get("route_short_name") or "")}
    calendar, dates = list(rows("calendar.txt")), list(rows("calendar_dates.txt"))

    def services(date, weekday):
        s = {c["service_id"] for c in calendar if c[weekday] == "1" and c["start_date"] <= date <= c["end_date"]}
        s |= {c["service_id"] for c in dates if c["date"] == date and c["exception_type"] == "1"}
        return s - {c["service_id"] for c in dates if c["date"] == date and c["exception_type"] == "2"}

    monday, tuesday = services("20261012", "monday"), services("20261013", "tuesday")
    trips = {
        r["trip_id"]: (r["service_id"], r.get("wheelchair_accessible") or "0")
        for r in rows("trips.txt")
        if r["route_id"] in noctilien and (r["service_id"] in monday or r["service_id"] in tuesday)
    }
    running = set()
    for r in rows("stop_times.txt"):
        trip = trips.get(r["trip_id"])
        if trip is None:
            continue
        t = r["departure_time"]
        # Tuesday's service after midnight, or Monday's service written as 25:xx.
        if (trip[0] in tuesday and "01:00:00" <= t < "02:00:00") or (trip[0] in monday and "25:00:00" <= t < "26:00:00"):
            running.add(r["trip_id"])
    return Counter(trips[t][1] for t in running)


def fr_pct(x):
    return f"{x:.1f}".replace(".", ",") + " %"


def main():
    score = load("vulnerability_score_iris.geojson")
    population = {f["properties"]["code_iris"]: f["properties"].get("population") or 0 for f in score["features"]}
    inhabited = [c for c, p in population.items() if p >= MIN_POPULATION]
    total_pop = sum(population[c] for c in inhabited)
    print(f"Inhabited neighbourhoods: {len(inhabited)} ({total_pop:,.0f} residents)")

    def minutes(times, code, block):
        v = times.get(code, {}).get(block)
        return math.inf if v is None else v

    def median(times, block):
        m = statistics.median(minutes(times, c, block) for c in inhabited)
        return "plus de 90 min" if math.isinf(m) else f"{m:g} min"

    def share_over(times, block):
        far = [c for c in inhabited if minutes(times, c, block) > OVER]
        return 100 * len(far) / len(inhabited), 100 * sum(population[c] for c in far) / total_pop

    print()
    print("Table (Method, 'Urgences selon l'heure de départ'):")
    print("Départ | Sans contrainte | Fauteuil roulant | Plus de 45 min en fauteuil roulant (quartiers) | (habitants)")
    times = {}
    for slot, label in SLOTS:
        times[slot] = emergency_times(slot)
        t = times[slot]
        not_reached = sum(1 for c in inhabited if math.isinf(minutes(t, c, WHEELCHAIR)))
        q, h = share_over(t, WHEELCHAIR)
        print(f"{label} | {median(t, FREE)} | {median(t, WHEELCHAIR)} | {fr_pct(q)} | {fr_pct(h)}"
              f"   [not reached within 90 min in a wheelchair: {not_reached}]")

    print()
    print("Note under the table:")
    for slot in ("tue10", "tue01"):
        q, _ = share_over(times[slot], FREE)
        print(f"  {slot}, without constraint, more than {OVER} min: {fr_pct(q)} of neighbourhoods")
    q_no, _ = share_over(times["tue01"], WHEELCHAIR)
    q_yes, _ = share_over(times["tue01"], WHEELCHAIR_YES)
    print(f"  tue01, wheelchair, more than {OVER} min: unknown = not accessible {fr_pct(q_no)}; "
          f"unknown = accessible {fr_pct(q_yes)}")
    acc = noctilien_accessibility()
    if acc is None:
        print("  Noctilien accessibility: raw GTFS absent, not counted")
    else:
        n = sum(acc.values())
        unknown = acc.get("0", 0)
        print(f"  Noctilien trips running 1:00-2:00 (night of 12 to 13 October 2026): {n}; "
              f"accessible {acc.get('1', 0)}, not accessible {acc.get('2', 0)}, "
              f"unknown {unknown} ({fr_pct(100 * unknown / n)})")


if __name__ == "__main__":
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    text = buf.getvalue()
    print(text, end="")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
