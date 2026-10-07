"""Second routing run: the blocking thresholds written on 2026-10-06 at 22:17
before the results (docs/checks/2026-10-06-second-routing-run-blocking-thresholds.md),
applied as written. Inhabited neighbourhoods (>= 50 residents), Tuesday
10:00, the three sets of places (Paris places for Paris neighbourhoods).
Reads the second run (routes_*_v2_*.json) and the first run kept in
data/interim/routes_v1_published/. Writes
data/interim/analysis/v2_blocking_thresholds.txt.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

P, V1 = config.DATA_PROCESSED, config.DATA_INTERIM / "routes_v1_published"
OUT = config.DATA_INTERIM / "analysis" / "v2_blocking_thresholds.txt"
SETS = {"key": "routes_iris", "neighbourhood": "routes_neighbourhood", "paris": "routes_paris"}
lines, blocked = [], []


def say(s=""):
    print(s)
    lines.append(s)


def table(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    blocks, types = d["layout"]["blocks"], d["layout"]["types"]
    return {code: {(b.split(":", 1)[1], t): row[i * len(types) + j] for i, b in enumerate(blocks) if b.startswith("time:") for j, t in enumerate(types)}
            for code, row in d["iris"].items()}, types


def main():
    score = json.loads((P / "vulnerability_score_iris.geojson").read_text(encoding="utf-8"))
    inhabited = {f["properties"]["code_iris"] for f in score["features"] if (f["properties"].get("population") or 0) >= 50}
    say("Second routing run — blocking thresholds (written 2026-10-06 22:17, before the results)")
    say("=" * 88)

    # 1. Wheelchair shorter than without constraint.
    say("\n1. Wheelchair time shorter than without constraint (neighbourhood x place pairs, Tuesday 10:00); blocks above 0.5 %")
    for variant in ("step_free_no", "step_free_yes"):
        n = tot = 0
        detail = []
        for name, prefix in SETS.items():
            tab, types = table(P / f"{prefix}_v2_tue10.json")
            codes = [c for c in inhabited if c in tab and (name != "paris" or c.startswith("75"))]
            k = m = 0
            for c in codes:
                for t in types:
                    a, b = tab[c].get(("standard", t)), tab[c].get((variant, t))
                    if a is None or b is None:
                        continue
                    m += 1
                    k += b < a
            n, tot = n + k, tot + m
            detail.append(f"{name} {k}/{m}")
        share = 100 * n / tot
        say(f"   {variant}: {n} of {tot:,} ({share:.3f} %) — {', '.join(detail)}")
        if share > 0.5:
            blocked.append(f"1 ({variant} {share:.2f} %)")

    # 2. First vs second, without constraint.
    say("\n2. First vs second calculation, without constraint; blocks if |mean| > 1 min or > 5 % of neighbourhoods change by 5 min or more")
    for name, prefix in SETS.items():
        for f2 in sorted(P.glob(f"{prefix}_v2_*.json")):
            if "sensitivity" in f2.name:
                continue
            slot = f2.stem.rsplit("_", 1)[1]
            f1 = V1 / f"{prefix}_{slot}.json"
            if not f1.exists():
                continue
            a, types1 = table(f1)
            b, _ = table(f2)
            codes = [c for c in inhabited if c in a and c in b and (name != "paris" or c.startswith("75"))]
            for t in types1:
                x = np.array([91 if a[c].get(("standard", t)) is None else a[c][("standard", t)] for c in codes], float)
                y = np.array([91 if b[c].get(("standard", t)) is None else b[c][("standard", t)] for c in codes], float)
                d = y - x
                big = 100 * (np.abs(d) >= 5).mean()
                flag = abs(d.mean()) > 1 or big > 5
                say(f"   {name:13} {slot} {t:16} mean {d.mean():+.2f} min, change >= 5 min {big:.1f} %{'  BLOCKS' if flag else ''}")
                if flag:
                    blocked.append(f"2 ({name} {slot} {t})")

    # 3. Neighbourhoods without a duration.
    say("\n3. Neighbourhoods without a duration")
    for name, prefix in SETS.items():
        for f2 in sorted(P.glob(f"{prefix}_v2_*.json")):
            if "sensitivity" in f2.name:
                continue
            tab, types = table(f2)
            scope = {c for c in inhabited if name != "paris" or c.startswith("75")}
            missing = sorted(scope - set(tab))
            say(f"   {f2.name}: inhabited neighbourhoods without a record {len(missing)}{' ' + str(missing[:10]) if missing else ''}")
            if missing:
                blocked.append(f"3 (no record, {f2.name})")
            f1 = V1 / f2.name.replace("_v2", "")
            if f1.exists():
                a, _ = table(f1)
                for t in types:
                    for prof in ("standard", "slow"):
                        n1 = sum(1 for c in scope if c in a and a[c].get((prof, t)) is None)
                        n2 = sum(1 for c in scope if c in tab and tab[c].get((prof, t)) is None)
                        if n2 - n1 > 10:
                            blocked.append(f"3 (> 90 min +{n2 - n1}, {f2.name} {prof} {t})")
                            say(f"   {f2.name} {prof} {t}: neighbourhoods more than 90 min {n1} -> {n2}  BLOCKS")
    ctl = config.DATA_INTERIM / "analysis"
    say("   population not reached in 90 min (controls), blocks above 1 %:")
    for f in ("routes_controls_v2.txt", "routes_neighbourhood_controls_v2.txt", "routes_paris_controls_v2.txt"):
        text = (ctl / f).read_text(encoding="utf-8") if (ctl / f).exists() else ""
        vals = [float(v.replace(",", ".")) for v in re.findall(r"non atteinte[^\n]*?([0-9]+[.,][0-9]+)\s*%", text)]
        say(f"   {f}: {len(vals)} values read, max {max(vals) if vals else 'n/a'} %")

    # 4. Verdicts.
    say("\n4. Verdicts: compare routes_means_v2.txt with routes_means_rp2022.txt (read by hand; see the report)")
    say("\nBLOCKED: " + ("; ".join(blocked) if blocked else "no threshold crossed (points 1-3; point 4 checked by hand)"))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
