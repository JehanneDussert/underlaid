"""Second calculation: neighbourhood travel times, first vs second
calculation (script 36 outputs: routes_*_<slot>.json vs routes_*_v2_<slot>.json).
For each set, slot, profile and place type, over inhabited neighbourhoods
(>= 50 residents): median of the neighbourhood times (first, second),
share of neighbourhoods whose time changes, mean change, share shorter /
longer, share of neighbourhoods where the wheelchair time is shorter than
the unconstrained one. Descriptive; no verdict.
Writes data/interim/analysis/v2_compare.txt.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

P = config.DATA_PROCESSED
OUT = config.DATA_INTERIM / "analysis" / "v2_compare.txt"
SETS = {"key": ("routes_iris", ["tue10", "tue21", "tue01", "sun10"]), "neighbourhood": ("routes_neighbourhood", ["tue10"]),
        "paris": ("routes_paris", ["tue10"])}
PROFILES = ["standard", "slow", "step_free_no", "step_free_yes"]
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def table(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    blocks, types = d["layout"]["blocks"], d["layout"]["types"]
    out = {}
    for code, row in d["iris"].items():
        out[code] = {(b.split(":", 1)[1], t): row[i * len(types) + j] for i, b in enumerate(blocks) if b.startswith("time:") for j, t in enumerate(types)}
    return out, types


def main():
    score = json.loads((P / "vulnerability_score_iris.geojson").read_text(encoding="utf-8"))
    inhabited = {f["properties"]["code_iris"] for f in score["features"] if (f["properties"].get("population") or 0) >= 50}
    say("Neighbourhood travel times: first calculation vs second (inhabited neighbourhoods)")
    say("=" * 88)
    say("'>90' = more than 90 min (counted as 91 for the medians and changes)")
    for name, (prefix, slots) in SETS.items():
        for slot in slots:
            f1, f2 = P / f"{prefix}_{slot}.json", P / f"{prefix}_v2_{slot}.json"
            if not (f1.exists() and f2.exists()):
                say(f"\n{name} {slot}: missing {f1.name if not f1.exists() else f2.name}")
                continue
            a, types = table(f1)
            b, types2 = table(f2)
            say(f"\n{name}, {slot}")
            say(f"  {'type':20}{'profile':15}{'median 1st':>11}{'median 2nd':>11}{'changed':>9}{'mean diff':>10}{'shorter':>9}{'longer':>8}")
            codes = sorted(inhabited & a.keys() & b.keys())
            for t in types:
                if t not in types2:
                    continue
                for p in PROFILES:
                    x = np.array([91 if a[c].get((p, t)) is None else a[c][(p, t)] for c in codes], dtype=float)
                    y = np.array([91 if b[c].get((p, t)) is None else b[c][(p, t)] for c in codes], dtype=float)
                    d = y - x
                    say(f"  {t:20}{p:15}{np.median(x):>11.0f}{np.median(y):>11.0f}{100 * (d != 0).mean():>8.1f}%{d.mean():>+10.2f}"
                        f"{100 * (d < 0).mean():>8.1f}%{100 * (d > 0).mean():>7.1f}%")
                for p in ["step_free_no", "step_free_yes"]:
                    for ver, tab in (("1st", a), ("2nd", b)):
                        n = sum(1 for c in codes if tab[c].get((p, t)) is not None and tab[c].get(("standard", t)) is not None
                                and tab[c][(p, t)] < tab[c][("standard", t)])
                        lines.append(f"    wheelchair ({p}) shorter than without constraint, {ver}: {n} of {len(codes)} ({100 * n / len(codes):.2f}%)")
                print("\n".join(lines[-4:]))
            new = [t for t in types2 if t not in types]
            if new:
                say(f"  new types in the second calculation: {', '.join(new)}")
                for t in new:
                    for p in PROFILES:
                        y = [b[c].get((p, t)) for c in codes]
                        v = np.array([91 if q is None else q for q in y], dtype=float)
                        say(f"  {t:20}{p:15}{'':>11}{np.median(v):>11.0f}   more than 90 min: {sum(q is None for q in y)}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
