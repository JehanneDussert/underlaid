"""Lift archive: how many daytime outages a sparser archive would miss.

The local archive (container underlaid-elevators) checks the IDFM
"État des ascenseurs" feed every hour. The GitHub Actions archive
(private repository underlaid-ascenseurs) is scheduled every hour too,
but GitHub runs only part of the scheduled jobs. This check measures, on
the hourly local archive, the share of daytime outages that an archive
checking only every k-th hour would still see.

Rules (written before running):
- only the longest run of checks with no gap of more than 90 minutes;
- daytime checks only: UTC hours 04 to 22. Between about 23:00 and 04:00
  UTC some 270 lifts are reported unavailable together: the network is
  closed, these are not breakdowns;
- outage start = a lift reported "available" at one daytime check and
  "notavailable" at the next one ("unknown" is ignored);
- every k-th daytime check is kept, for each of the k possible offsets;
  the share of the outage starts of the hourly series that the sparser
  series still sees is reported (minimum, mean, maximum over offsets).

With the GitHub archive's gaps.csv, also reports its spacing of checks.

Usage: python scripts/analysis/lift_archive_sampling.py LOCAL_DIR [GITHUB_GAPS_CSV]
"""
import csv
import gzip
import json
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def hourly_series(local_dir):
    """(checked_utc, {liftid: status}) for every successful check."""
    files = {}
    for f in local_dir.glob("2026-*/*.json.gz"):
        files[(f.parent.name, f.name[:4])] = f
    series, current = [], None
    with open(local_dir / "log.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["error"] or row["lifts"] in ("", "0"):
                continue
            t = row["fetched_utc"]
            key = (t[:10], t[11:13] + t[14:16])
            if key in files:  # a snapshot is kept only when the feed changed
                with gzip.open(files[key], "rt", encoding="utf-8") as g:
                    current = {x["liftid"]: x["liftstatus"] for x in json.load(g)}
            if current is not None:
                series.append((t, current))
    return series


def longest_run(series):
    """Longest stretch of checks with no gap of more than 90 minutes."""
    when = lambda t: datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
    runs, run = [], [series[0]]
    for item in series[1:]:
        if (when(item[0]) - when(run[-1][0])).total_seconds() > 90 * 60:
            runs.append(run)
            run = []
        run.append(item)
    runs.append(run)
    return max(runs, key=len)


def outage_starts(series):
    n, prev = 0, series[0][1]
    for _, status in series[1:]:
        n += sum(1 for k, v in status.items() if v == "notavailable" and prev.get(k) == "available")
        prev = status
    return n


def outage_lengths(series):
    """Length, in daytime checks, of the outages that end within the series."""
    lengths, start, prev = [], {}, series[0][1]
    for i, (_, status) in enumerate(series[1:], 1):
        for k, v in status.items():
            if v == "notavailable" and prev.get(k) == "available":
                start[k] = i
            elif v == "available" and k in start:
                lengths.append(i - start.pop(k))
        prev = status
    return lengths


def main():
    local_dir = Path(sys.argv[1])
    series = longest_run(hourly_series(local_dir))
    day = [(t, s) for t, s in series if 4 <= int(t[11:13]) <= 22]
    print(f"Local archive: {len(series)} checks, {series[0][0]} to {series[-1][0]}; daytime checks: {len(day)}")
    full = outage_starts(day)
    lengths = outage_lengths(day)
    one = sum(1 for x in lengths if x == 1)
    print(f"Daytime outage starts (hourly): {full}")
    print(f"Outages that end within the period: {len(lengths)}; over after one check (about 1 h): {one} ({100 * one / len(lengths):.0f} %)")
    print("Length in checks:", sorted(Counter(lengths).items()))
    print()
    print("Share of daytime outage starts still seen with one check every k hours (min / mean / max over offsets):")
    for k in range(2, 9):
        seen = [outage_starts(day[o::k]) for o in range(k)]
        pct = [100 * s / full for s in seen]
        print(f"  k = {k}: {min(pct):.0f} % / {statistics.mean(pct):.0f} % / {max(pct):.0f} %")

    if len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as fh:
            gaps = [float(r["hours_without_check"]) for r in csv.DictReader(fh)]
        print()
        print(f"GitHub archive: {len(gaps)} gaps of more than 90 min; hours between checks: "
              f"median {statistics.median(gaps):.1f}, min {min(gaps):.1f}, max {max(gaps):.1f}, "
              f"total {sum(gaps):.1f} h for {len(gaps) + 1} checks")


if __name__ == "__main__":
    main()
