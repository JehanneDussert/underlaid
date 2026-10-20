"""How often does the IDFM lift-status feed really change? (local archive)

A. Status changes between consecutive hourly checks (at most 90 min apart),
   by hour of the check (Paris time): when do lifts change status?
B. The source's own date of each state (liftstateupdate): number of distinct
   update times per day and their hour of day — rounds three times a day, or
   continuous updates?
C. For status changes seen between two checks, is the source date inside
   that interval (fresh update) or older?
D. Source update times by mode (liftmode): hours with the most updates.
E. Status changes between 7:00 and 23:59 (Paris) by mode and hour, and the
   share seen at the checks that follow 11:00, 15:00 and 20:00 (6 of 17 hours,
   35 % if changes were spread evenly).

Descriptive only: no availability rate is computed. Run on 19 October 2026
on the local archive (6 to 19 October); results quoted in the amendment of
the lift pre-registration (docs/preregistrations/).
Usage: python scripts/analysis/lift_update_frequency.py data/raw/elevators
(sections D uses every snapshot saved up to the end of the period)
"""
import collections
import csv
import datetime as dt
import gzip
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

D = Path(sys.argv[1])
# Fixed period for reproducibility: up to 19 October 2026 at 19:00 UTC,
# the last hourly check before the archive moved to one check every 15 min.
END = dt.datetime(2026, 10, 19, 19, 0, tzinfo=dt.timezone.utc)
PARIS = ZoneInfo("Europe/Paris")
files = {(f.parent.name, f.name[:4]): f for f in D.glob("2026-*/*.json.gz")}
checks = []
current = None
with (D / "log.csv").open(encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if not r["lifts"].isdigit() or int(r["lifts"]) == 0 or r["error"]:
            continue
        t = dt.datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        key = (r["fetched_utc"][:10], r["fetched_utc"][11:13] + r["fetched_utc"][14:16])
        if key in files:
            with gzip.open(files[key], "rt", encoding="utf-8") as g:
                current = {x["liftid"]: (x["liftstatus"], x.get("liftstateupdate")) for x in json.load(g)}
        if current is not None and t <= END:
            checks.append((t, current))
print(f"{len(checks)} successful checks, {checks[0][0]:%d/%m %H:%M} to {checks[-1][0]:%d/%m %H:%M} UTC")

# A. status changes between consecutive checks, by Paris hour of the later check
by_hour = collections.Counter()
pairs_by_hour = collections.Counter()
fresh = stale = 0
lags = []
for (t0, s0), (t1, s1) in zip(checks, checks[1:]):
    if (t1 - t0).total_seconds() > 90 * 60:
        continue
    h = t1.astimezone(PARIS).hour
    pairs_by_hour[h] += 1
    for lid, (st1, up1) in s1.items():
        st0 = s0.get(lid, (None, None))[0]
        if st0 is not None and st0 != st1:
            by_hour[h] += 1
            if up1:
                u = dt.datetime.fromisoformat(up1)
                u = u.replace(tzinfo=PARIS) if u.tzinfo is None else u
                lags.append((t1 - u).total_seconds() / 60)
                if t0 - dt.timedelta(minutes=5) <= u <= t1 + dt.timedelta(minutes=5):
                    fresh += 1
                else:
                    stale += 1
print("\nA. Status changes between consecutive checks, mean per check, by Paris hour of the check:")
for h in range(24):
    if pairs_by_hour[h]:
        print(f"  {h:02d}h  {by_hour[h] / pairs_by_hour[h]:6.1f}  ({pairs_by_hour[h]} check pairs)")

# B. distinct source update times
ups = set()
for _, s in checks:
    for lid, (_, up) in s.items():
        if up:
            ups.add((lid, up))
per_day = collections.Counter()
times_per_day = collections.defaultdict(set)
hours = collections.Counter()
for lid, up in ups:
    u = dt.datetime.fromisoformat(up)
    if u.date() < checks[0][0].date():
        continue
    per_day[u.date()] += 1
    times_per_day[u.date()].add(u.strftime("%H:%M"))
    hours[u.hour] += 1
print("\nB. Distinct state updates dated by the source (liftstateupdate), per day:")
for d in sorted(per_day):
    print(f"  {d}: {per_day[d]} lift updates at {len(times_per_day[d])} distinct times of day")
print("  by hour of the source date:", " ".join(f"{h:02d}h:{hours[h]}" for h in range(24)))
print("\nC. Status changes whose source date falls between the two checks:", fresh, "| older:", stale)
if lags:
    lags.sort()
    print(f"   delay between the source date and the check that saw it (min): median {lags[len(lags) // 2]:.0f}, p90 {lags[9 * len(lags) // 10]:.0f}")

# D. source update times by mode
seen = {}
for f in sorted(D.glob("2026-*/*.json.gz")):
    with gzip.open(f, "rt", encoding="utf-8") as g:
        for x in json.load(g):
            if f.parent.name > "2026-10-19" or (f.parent.name == "2026-10-19" and f.name[:4] > "1900"):
                break
            if x.get("liftstateupdate"):
                seen[(x["liftid"], x["liftstateupdate"])] = x.get("liftmode")
print()
print("D. Source updates by mode, hours with the most updates:")
for mode in sorted({m for m in seen.values() if m}):
    hrs = collections.Counter(dt.datetime.fromisoformat(u).hour for (lid, u), m in seen.items() if m == mode and dt.datetime.fromisoformat(u) >= dt.datetime(2026, 10, 6))
    print(f"  {mode}: {sum(hrs.values())} updates; top hours {sorted(hrs.items(), key=lambda x: -x[1])[:6]}")

# E. status changes 7:00-23:59 by mode and hour
modes = {}
for f in sorted(D.glob("2026-*/*.json.gz")):
    with gzip.open(f, "rt", encoding="utf-8") as g:
        for x in json.load(g):
            modes[x["liftid"]] = x.get("liftmode")
ROUND = {11, 12, 15, 16, 20, 21}
c = collections.defaultdict(collections.Counter)
for (t0, s0), (t1, s1) in zip(checks, checks[1:]):
    if (t1 - t0).total_seconds() > 90 * 60:
        continue
    h = t1.astimezone(PARIS).hour
    if not 7 <= h <= 23:
        continue
    for lid, (st1, _) in s1.items():
        st0 = s0.get(lid, (None, None))[0]
        if st0 is not None and st0 != st1 and "unknown" not in (st0, st1):
            c[modes.get(lid)]["round" if h in ROUND else "other"] += 1
print()
print("E. Status changes 7:00-23:59 (Paris), share at the checks after 11:00, 15:00, 20:00 (even spread: 35 %):")
for m, k in c.items():
    tot = sum(k.values())
    print(f"  {m}: {tot} changes, {100 * k['round'] / tot:.0f} %")
