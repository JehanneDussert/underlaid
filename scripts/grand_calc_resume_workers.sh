#!/bin/sh
# Grand calculation (6 October 2026): two phase-2 workers stopped when the
# three of them built the same new network at the same time (shared r5py
# cache file corrupted). The remaining networks are built once by the
# container underlaid-prebuild; this script waits for it, then restarts
# workers 1 and 2 (finished chunks are skipped). Runs in docker:cli:
#   docker run -d --name underlaid-orchestrator2 -v //var/run/docker.sock:/var/run/docker.sock \
#     -v C:/Users/jehan/Documents/underlaid/scripts:/s docker:cli sh /s/grand_calc_resume_workers.sh
H=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid
while docker ps --format '{{.Names}}' | grep -q '^underlaid-prebuild$'; do sleep 60; done
echo "networks built $(date)"
for w in 1 2; do
  docker rm -f "underlaid-v2b-w$w" >/dev/null 2>&1
  docker run -d --name "underlaid-v2b-w$w" -w /app \
    -v "$H/data:/app/data" -v "$H/scripts:/app/scripts" \
    -v "$H/data/interim/access/r5py_cache:/root/.cache/r5py" \
    -e WORKER=$w -e WORKERS=3 -e R5_MAX_MEMORY=9G -e ROUTES_VERSION=2 \
    underlaid-access sh -c "ROUTES_SET=routes python scripts/34_route_travel_times.py && ROUTES_SET=neighbourhood python scripts/34_route_travel_times.py && ROUTES_SET=paris python scripts/34_route_travel_times.py"
done
echo "workers 1 and 2 restarted $(date)"
