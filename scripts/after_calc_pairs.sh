#!/bin/sh
# Runs the neighbouring-pairs search (scripts/analysis/neighbouring_pairs.py)
# once the after-calculation chain (after_grand_calc.sh) has written DONE.
# Started in a docker:cli container like after_grand_calc.sh, with the main
# folder's data/interim/analysis mounted on /analysis.
MAIN=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid
WT=/run/desktop/mnt/host/c/Users/jehan/Documents/underlaid-worktree
until tail -1 /analysis/after_grand_calc.log 2>/dev/null | grep -qE '^DONE|FAILED'; do sleep 120; done
tail -1 /analysis/after_grand_calc.log | grep -q '^DONE' || { echo "after-calc chain failed, pairs not run"; exit 1; }
docker rm -f underlaid-pairs-run >/dev/null 2>&1
docker run --name underlaid-pairs-run --memory 14g -w /app \
  -v "$WT/data:/app/data" -v "$WT/scripts:/app/scripts" \
  -v "$MAIN/data/raw:/app/data/raw" -v "$MAIN/data/interim:/app/data/interim" \
  -v "$MAIN/data/processed/access:/app/data/processed/access" \
  -v "$MAIN/data/interim/access/r5py_cache:/root/.cache/r5py" \
  -e R5_MAX_MEMORY=10G --entrypoint sh underlaid-access -c \
  'python scripts/analysis/neighbouring_pairs.py > data/interim/analysis/neighbouring_pairs.log 2>&1 && echo DONE >> data/interim/analysis/neighbouring_pairs.log || echo FAILED >> data/interim/analysis/neighbouring_pairs.log'
echo "pairs finished $(date)"
