"""Archive of the IDFM "État des ascenseurs" feed (decided on 2026-10-04,
roadmap: availability rate per station after the launch).

The feed (990 lifts of the rail stations of Île-de-France, Licence
Mobilités: reuse and archiving allowed with the source cited) is published
three times a day by IDFM from the RATP and SNCF station staff rounds. This
script asks every hour and keeps a snapshot only when the content changed,
so that each publication is caught once. The token (PRIM_DATASET_TOKEN)
comes from the environment (.env at the repository root, never versioned).

Output: data/raw/elevators/YYYY-MM-DD/HHMM.json.gz (raw records), plus
data/raw/elevators/log.csv (every hourly attempt: time, number of lifts,
number available, hash, saved or not, error if any) and
data/raw/elevators/gaps.csv: every period without a successful check, made
explicit (the archive runs on a personal computer, so it has holes when the
computer is off or Docker is stopped; a failed request is a hole too).
A gap is recorded when two successful checks are more than 90 minutes
apart: from the last success to the next one.
Empty responses (the API answers with no lift at all, seen on 8 October
2026 at 04:15 UTC) are not checks: they are listed in
data/raw/elevators/empty_responses.csv, logged with the error "empty
response", and neither saved nor counted as a success (same rule as the
GitHub Actions archive, decision of 8 October 2026).
Runs as a long-lived container:
  docker run -d --name underlaid-elevators --restart unless-stopped --env-file .env \
    -v <repo>/data:/app/data -v <repo>/scripts:/app/scripts -w /app underlaid-access python scripts/archive_elevators.py
"""
import datetime as dt
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

import requests

URL = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/etat-des-ascenseurs/exports/json"
OUT = Path("/app/data/raw/elevators") if Path("/app/data").exists() else Path(__file__).resolve().parents[1] / "data" / "raw" / "elevators"
EVERY_S = 3600
GAP_S = 90 * 60


def fetch():
    token = os.environ["PRIM_DATASET_TOKEN"]
    r = requests.get(URL, headers={"Authorization": f"Apikey {token}"}, timeout=120)
    r.raise_for_status()
    return r.json()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / "log.csv"
    gaps = OUT / "gaps.csv"
    if not log.exists():
        log.write_text("fetched_utc,lifts,available,sha256,saved,error\n", encoding="utf-8")
    if not gaps.exists():
        gaps.write_text("from_utc,to_utc,hours_without_check\n", encoding="utf-8")
    last, last_ok = None, None
    lines = log.read_text(encoding="utf-8").strip().splitlines()[1:]
    for line in reversed(lines):
        cols = line.split(",")
        if last_ok is None and cols[1] not in ("", "-", "0"):
            last_ok = dt.datetime.strptime(cols[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        if last is None and len(cols) > 4 and cols[4] == "1":
            last = cols[3]
        if last and last_ok:
            break
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        try:
            records = fetch()
            if not records:
                empty = OUT / "empty_responses.csv"
                new = not empty.exists()
                with empty.open("a", encoding="utf-8") as f:
                    if new:
                        f.write("checked_utc,note\n")
                    f.write(f"{now:%Y-%m-%dT%H:%M:%SZ},empty response from the API (no lift); not a check\n")
                with log.open("a", encoding="utf-8") as f:
                    f.write(f"{now:%Y-%m-%dT%H:%M:%SZ},0,0,-,0,empty response\n")
                print(f"{now:%Y-%m-%d %H:%M} UTC: empty response, not counted", flush=True)
                time.sleep(EVERY_S)
                continue
            body = json.dumps(sorted(records, key=lambda r: str(r.get("liftid"))), ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha256(body.encode()).hexdigest()
            available = sum(1 for r in records if r.get("liftstatus") == "available")
            saved = digest != last
            if saved:
                day = OUT / now.strftime("%Y-%m-%d")
                day.mkdir(exist_ok=True)
                with gzip.open(day / f"{now:%H%M}.json.gz", "wt", encoding="utf-8") as f:
                    f.write(body)
                last = digest
            with log.open("a", encoding="utf-8") as f:
                f.write(f"{now:%Y-%m-%dT%H:%M:%SZ},{len(records)},{available},{digest[:16]},{int(saved)},\n")
            if last_ok is not None and (now - last_ok).total_seconds() > GAP_S:
                with gaps.open("a", encoding="utf-8") as f:
                    f.write(f"{last_ok:%Y-%m-%dT%H:%M:%SZ},{now:%Y-%m-%dT%H:%M:%SZ},{(now - last_ok).total_seconds() / 3600:.1f}\n")
            last_ok = now
            print(f"{now:%Y-%m-%d %H:%M} UTC: {len(records)} lifts, {available} available, {'saved' if saved else 'unchanged'}", flush=True)
        except Exception as e:  # keep going: a failed hour is retried the next hour
            with log.open("a", encoding="utf-8") as f:
                f.write(f"{now:%Y-%m-%dT%H:%M:%SZ},-,-,-,0,{str(e)[:120].replace(',', ';')}\n")
            print(f"{now:%Y-%m-%d %H:%M} UTC: error {e}", flush=True)
        time.sleep(EVERY_S)


if __name__ == "__main__":
    main()
