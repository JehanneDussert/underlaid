"""Second calculation: sensitivity of the wheelchair profile to its speed
(pre-registered 2026-10-04: main 0.8 m/s, sensitivity 0.5 and 1.0 m/s;
Tuesday 10:00, unknown = not accessible), key places. Per neighbourhood,
population-weighted median of its cells (script 36 rules); then, over
inhabited neighbourhoods: median time per place type and speed, Spearman
correlation with the main speed, and share of neighbourhoods whose quarter
(farthest quarter of the metropolis) changes. Descriptive; no verdict.
Writes data/interim/analysis/v2_speed_sensitivity.txt.
"""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

os.environ.setdefault("ROUTES_VERSION", "2")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("s36", ROOT / "scripts" / "36_route_aggregate.py")
s36 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s36)
import config  # noqa: E402

OUT = config.DATA_INTERIM / "analysis" / "v2_speed_sensitivity.txt"
PROFILES = {"0.5 m/s": "sens_speed05", "0.8 m/s (main)": "step_free_no", "1.0 m/s": "sens_speed10", "without constraint": "standard"}


def main():
    cells = s36.cells_by_iris()
    tables = {}
    for label, p in PROFILES.items():
        d = s36.load_task(f"{p}_tue10")
        if d is None:
            print(f"{p}_tue10 incomplete")
            return
        summary = s36.summarise(d, cells, s36.TYPES)
        tables[label] = pd.DataFrame(summary).T.astype(float)
    pop = cells.groupby("code_iris")["pop"].sum()
    inhabited = pop[pop >= 50].index
    lines = ["Wheelchair profile, speed sensitivity (key places, Tuesday 10:00, unknown = not accessible)", "=" * 88,
             "median over inhabited neighbourhoods of the neighbourhood times (min); 'more than 90 min' counted as missing", ""]
    lines.append(f"{'place':16}" + "".join(f"{k:>22}" for k in PROFILES))
    for t in s36.TYPES:
        lines.append(f"{t:16}" + "".join(f"{tables[k].loc[tables[k].index.isin(inhabited), t].median():>22.0f}" for k in PROFILES))
    lines.append("")
    main_t = tables["0.8 m/s (main)"]
    for k in ["0.5 m/s", "1.0 m/s"]:
        rows = []
        for t in s36.TYPES:
            a = main_t.loc[main_t.index.isin(inhabited), t]
            b = tables[k].loc[tables[k].index.isin(inhabited), t]
            ok = a.notna() & b.notna()
            rho = a[ok].rank().corr(b[ok].rank())
            qa = a[ok] >= a[ok].quantile(0.75)
            qb = b[ok] >= b[ok].quantile(0.75)
            rows.append(f"{t} rho {rho:.3f}, farthest quarter changes {100 * (qa != qb).mean():.1f}%")
        lines.append(f"{k} vs 0.8 m/s: " + "; ".join(rows))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
