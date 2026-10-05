#!/usr/bin/env bash
# Relaunch the grand calculation (version 2) after a restart of the computer
# or of Docker. Finished chunks are kept and skipped: the calculation picks
# up where it stopped. Run from Git Bash:
#
#   bash /c/Users/jehan/Documents/underlaid/scripts/grand_calc_relaunch.sh
#
# Progress:
#   cat /c/Users/jehan/Documents/underlaid/data/interim/access/routes_progress_v2.txt
ROOT="C:/Users/jehan/Documents/underlaid"
for name in underlaid-orchestrator underlaid-v2-w0 underlaid-v2-w1 underlaid-v2-w2 underlaid-v2b-w0 underlaid-v2b-w1 underlaid-v2b-w2; do
  docker rm -f "$name" >/dev/null 2>&1
done
for w in 0 1 2; do
  MSYS_NO_PATHCONV=1 docker run -d --name "underlaid-v2b-w$w" -w /app \
    -v "$ROOT/data:/app/data" -v "$ROOT/scripts:/app/scripts" \
    -v "$ROOT/data/interim/access/r5py_cache:/root/.cache/r5py" \
    -e WORKER=$w -e WORKERS=3 -e R5_MAX_MEMORY=9G -e ROUTES_VERSION=2 \
    underlaid-access sh -c "ROUTES_SET=routes python scripts/34_route_travel_times.py && ROUTES_SET=neighbourhood python scripts/34_route_travel_times.py && ROUTES_SET=paris python scripts/34_route_travel_times.py"
done
docker ps --filter name=underlaid
