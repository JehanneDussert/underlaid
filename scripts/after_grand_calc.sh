#!/bin/sh
# After the grand calculation (second routing run, pre-registered on
# 4 October 2026). Runs in a docker:cli container that drives the host's
# Docker, so it keeps going without a terminal or a Claude session:
#
#   docker run -d --name underlaid-after-calc -v //var/run/docker.sock:/var/run/docker.sock \
#     -v C:/Users/jehan/Documents/underlaid-worktree/scripts:/s docker:cli sh /s/after_grand_calc.sh
#
# 1. waits until the workers (underlaid-v2b-w0..2) have all stopped and the
#    three progress files say 100 %;
# 2. in one container (worktree scripts and processed data; the main
#    folder's raw and interim data, where the travel-time matrices are):
#    script 36 (version 2) for the three sets of places; controls:
#    remaining inversions, first vs second calculation, speed and slope
#    sensitivity, pre-registered controls, the public-services crossing redone
#    as a check (routes_means_v2.txt; the published verdicts stay the
#    reference);
# 3. regenerates the site files from the second calculation: the version-2
#    outputs replace the published route files in the worktree's
#    data/processed (the first-calculation files are kept in
#    data/interim/routes_v1_published/ of the main folder), then scripts
#    38, 39, 43 and 35. Nothing is committed or pushed.
# Log: data/interim/analysis/after_grand_calc.log (main folder); the last
# line is "DONE" or "FAILED at <step>".
MAIN=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid
WT=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid-worktree
done_all() {
  for f in routes_progress_v2.txt routes_neighbourhood_progress_v2.txt routes_paris_progress_v2.txt; do
    head -1 "/progress/$f" 2>/dev/null | grep -q "100%" || return 1
  done
  ! docker ps --format '{{.Names}}' | grep -q '^underlaid-v2b-w'
}
until done_all; do sleep 120; done
echo "grand calculation finished $(date)"
docker rm -f underlaid-after-calc-run >/dev/null 2>&1
docker run --name underlaid-after-calc-run --memory 14g -w /app \
  -v "$WT/data:/app/data" -v "$WT/scripts:/app/scripts" \
  -v "$MAIN/data/raw:/app/data/raw" -v "$MAIN/data/interim:/app/data/interim" \
  -v "$MAIN/data/processed/access:/app/data/processed/access" \
  -e ROUTES_VERSION=2 --entrypoint sh underlaid-access -c '
LOG=data/interim/analysis/after_grand_calc.log
step() { echo "== $1 $(date +%H:%M:%S)" >> $LOG; shift; "$@" >> $LOG 2>&1 || { echo "FAILED at: $*" >> $LOG; exit 1; }; }
echo "start $(date)" > $LOG
for S in key neighbourhood paris; do step "aggregate $S" env ROUTES_SET=$S python scripts/36_route_aggregate.py; done
step "inversions (cells)" python scripts/analysis/v2_inversions.py
step "first vs second" python scripts/analysis/v2_compare.py
for S in key neighbourhood paris; do step "sensitivity $S" env ROUTES_SET=$S python scripts/analysis/v2_speed_sensitivity.py; done
for S in key neighbourhood paris; do step "controls $S" env ROUTES_SET=$S python scripts/analysis/routes_controls.py; done
step "public services crossing (check)" python scripts/analysis/routes_means.py
# Site files from the second calculation.
mkdir -p data/interim/routes_v1_published
cd data/processed
for f in routes_iris_tue10 routes_iris_tue21 routes_iris_tue01 routes_iris_sun10 routes_neighbourhood_tue10 routes_paris_tue10; do
  cp -n $f.json ../interim/routes_v1_published/ 2>/dev/null
  v=$(echo $f | sed "s/_\(tue10\|tue21\|tue01\|sun10\)$/_v2_\1/")
  cp $v.json $f.json
done
cp -n routes_stations_iris.json ../interim/routes_v1_published/ 2>/dev/null
cp routes_stations_iris_v2.json routes_stations_iris.json
cd /app
for s in 38_routes_summary 39_neighbourhood_files 43_question_pairs 35_key_figures; do step "$s" env ROUTES_VERSION=1 python scripts/$s.py; done
echo DONE >> $LOG
'
echo "after-calc finished $(date)"
