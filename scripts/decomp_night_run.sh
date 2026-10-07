#!/bin/sh
# Night run of the wheelchair-time decomposition (pre-registered on
# 2026-10-07). Runs in a docker:cli container driving the host's Docker:
#
#   docker run -d --name underlaid-decomp-orchestrator -v //var/run/docker.sock:/var/run/docker.sock \
#     -v C:/Users/jehan/Documents/underlaid-runs/decomp-2026-10-07/scripts:/s docker:cli sh /s/decomp_night_run.sh
#
# Scripts come from a frozen copy (underlaid-runs/decomp-2026-10-07), data
# from the main folder. Waits until 20:00 UTC (22:00 in Paris) and until no
# other routing container runs, then three workers (key places, then
# everyday places), then the analysis. Log:
# data/interim/analysis/wheelchair_decomposition.log (main folder).
H=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid
S=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid-runs/decomp-2026-10-07/scripts
busy() { docker ps --format '{{.Names}}' | grep -qE '^underlaid-(v2b?-w|pairs-run|after-calc-run|islands|clichy|pair-route)'; }
until [ "$(date -u +%H)" -ge 20 ] && ! busy; do sleep 300; done
echo "start $(date)"
for w in 0 1 2; do
  docker rm -f "underlaid-decomp-w$w" >/dev/null 2>&1
  docker run -d --name "underlaid-decomp-w$w" -w /app \
    -v "$H/data:/app/data" -v "$S:/app/scripts" \
    -v "$H/data/interim/access/r5py_cache:/root/.cache/r5py" \
    -e WORKER=$w -e WORKERS=3 -e R5_MAX_MEMORY=9G -e ROUTES_VERSION=2 -e ROUTES_DECOMP=1 \
    underlaid-access sh -c "ROUTES_SET=key python scripts/34_route_travel_times.py && ROUTES_SET=neighbourhood python scripts/34_route_travel_times.py"
  sleep 60
done
while docker ps --format '{{.Names}}' | grep -q '^underlaid-decomp-w'; do sleep 120; done
echo "workers finished $(date)"
docker rm -f underlaid-decomp-analysis >/dev/null 2>&1
docker run --name underlaid-decomp-analysis --memory 12g -w /app -v "$H/data:/app/data" -v "$S:/app/scripts" \
  -e ROUTES_VERSION=2 --entrypoint sh underlaid-access -c \
  'python scripts/analysis/wheelchair_decomposition.py > data/interim/analysis/wheelchair_decomposition.log 2>&1 && echo DONE >> data/interim/analysis/wheelchair_decomposition.log || echo FAILED >> data/interim/analysis/wheelchair_decomposition.log'
echo "analysis finished $(date)"
