#!/bin/sh
# Grand calculation, phase 2 (5 October 2026). Runs in a docker:cli
# container that drives the host's Docker, so it keeps going without any
# terminal or Claude session:
#
#   docker run -d --name underlaid-orchestrator -v //var/run/docker.sock:/var/run/docker.sock \
#     -v C:/Users/jehan/Documents/underlaid/scripts:/s docker:cli sh /s/grand_calc_phase2.sh
#
# 1. waits until the phase-1 workers (underlaid-v2-w0..2: profiles without
#    constraint and slow walk) have all stopped;
# 2. starts three workers on every profile of version 2 (the finished chunks
#    are skipped, so any chunk a stopped phase-1 worker left undone is done
#    too, then the wheelchair profiles and the sensitivity runs), for the
#    three sets of places one after the other.
# Progress: data/interim/access/routes_progress_v2.txt, then
# routes_neighbourhood_progress_v2.txt, routes_paris_progress_v2.txt.
H=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid
while docker ps --format '{{.Names}}' | grep -q '^underlaid-v2-w'; do
  sleep 120
done
echo "phase 1 finished $(date)"
for w in 0 1 2; do
  docker rm -f "underlaid-v2b-w$w" >/dev/null 2>&1
  docker run -d --name "underlaid-v2b-w$w" -w /app \
    -v "$H/data:/app/data" -v "$H/scripts:/app/scripts" \
    -v "$H/data/interim/access/r5py_cache:/root/.cache/r5py" \
    -e WORKER=$w -e WORKERS=3 -e R5_MAX_MEMORY=9G -e ROUTES_VERSION=2 \
    underlaid-access sh -c "ROUTES_SET=routes python scripts/34_route_travel_times.py && ROUTES_SET=neighbourhood python scripts/34_route_travel_times.py && ROUTES_SET=paris python scripts/34_route_travel_times.py"
done
echo "phase 2 started $(date)"
