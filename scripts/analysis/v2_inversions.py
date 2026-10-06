"""Second calculation (version 2): share of cell x place pairs where the
wheelchair (step-free) time is shorter than the time without constraint,
over every inhabited cell of the metropolis, by time slot and variant, for
each set of places, compared with the first calculation. Changes nothing;
writes data/interim/analysis/v2_inversions.txt. Run while the calculation
is still going: incomplete tasks are reported as such and left out.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

AI = config.DATA_INTERIM / "access"
OUT = config.DATA_INTERIM / "analysis" / "v2_inversions.txt"
SETS = {"key": ("routes_ttm", 46, ["tue10", "tue21", "tue01", "sun10", "stations_walk"]),
        "neighbourhood": ("routes_ttm_neighbourhood", 92, ["tue10"]),
        "paris": ("routes_ttm_paris", 7, ["tue10"])}
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def load(d: Path, task: str, n: int):
    files = sorted(d.glob(f"{task}_[0-9][0-9].parquet"))
    if len(files) < n:
        return None, len(files)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True), len(files)


say("Wheelchair (step-free) faster than without constraint: share of cell x place pairs")
say("=" * 84)
for name, (folder, n, slots) in SETS.items():
    say(f"\n{name}")
    for slot in slots:
        for variant in ["no", "yes"]:
            row = f"  {slot:14} unknown={variant}:"
            for ver, sfx in [("first", ""), ("v2", "_v2")]:
                d = AI / (folder + sfx)
                std, k1 = load(d, f"standard_{slot}", n)
                sf, k2 = load(d, f"step_free_{variant}_{slot}", n)
                if std is None or sf is None:
                    row += f" | {ver}: incomplete ({k1 if std is None else n}/{n}, {k2 if sf is None else n}/{n})"
                    continue
                m = std.merge(sf, on=["cell_id", "type"], suffixes=("_s", "_f"))
                d_ = m.minutes_f - m.minutes_s
                f = d_ < 0
                row += f" | {ver}: {f.sum():,} of {len(m):,} ({100 * f.mean():.2f}%), 1 min {int((d_ == -1).sum()):,}, worst {int(d_.min())}"
            say(row)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
