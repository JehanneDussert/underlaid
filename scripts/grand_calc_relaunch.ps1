# Relaunch the grand calculation (version 2) after a restart of the computer
# or of Docker. Finished chunks are kept and skipped: the calculation picks
# up where it stopped. Run from PowerShell:
#
#   powershell -ExecutionPolicy Bypass -File C:\Users\jehan\Documents\underlaid\scripts\grand_calc_relaunch.ps1
#
# Progress:
#   Get-Content C:\Users\jehan\Documents\underlaid\data\interim\access\routes_progress_v2.txt
$root = "C:/Users/jehan/Documents/underlaid"
foreach ($name in @("underlaid-orchestrator", "underlaid-v2-w0", "underlaid-v2-w1", "underlaid-v2-w2", "underlaid-v2b-w0", "underlaid-v2b-w1", "underlaid-v2b-w2")) {
  docker rm -f $name 2>$null | Out-Null
}
foreach ($w in 0, 1, 2) {
  docker run -d --name "underlaid-v2b-w$w" -w /app `
    -v "${root}/data:/app/data" -v "${root}/scripts:/app/scripts" `
    -v "${root}/data/interim/access/r5py_cache:/root/.cache/r5py" `
    -e WORKER=$w -e WORKERS=3 -e R5_MAX_MEMORY=9G -e ROUTES_VERSION=2 `
    underlaid-access sh -c "ROUTES_SET=routes python scripts/34_route_travel_times.py && ROUTES_SET=neighbourhood python scripts/34_route_travel_times.py && ROUTES_SET=paris python scripts/34_route_travel_times.py"
}
docker ps --filter name=underlaid
