"""Controls of the emergency curve, before publication (part 5 of
docs/preregistrations/2026-10-22-courbe-urgences-heure-depart.md), and the
neighbourhood curve file read by the page.

Reads the per-cell times of script 34 (ROUTES_SET=curve, ROUTES_VERSION=2,
data/interim/access/routes_ttm_curve_v2) and the published neighbourhood
times (data/processed/routes_iris_<slot>.json). Neighbourhood values use the
rules of script 36 (population-weighted median of the inhabited cells,
+inf beyond 90 min, "more than 90 min" if more than half of the population
does not reach an emergency department).

1. 10:00 slot: share of neighbourhoods whose value differs from the
   published one (without constraint and wheelchair). Above 1 %: nothing is
   published before an explanation.
2. Inversions: share of cell x slot pairs where the wheelchair time is
   shorter than the time without constraint.
3. Completeness: share of the population beyond 90 min, by slot, profile
   and department.
4. Coherence with the published 21:00 and 1:00 values: share of
   neighbourhoods whose published value lies between the curve values just
   before and just after (described, never corrected).
Night sensitivity (unknown accessibility counted as accessible, 0:00, 2:00,
4:00) and the Method table (median of the neighbourhoods, share of the
population beyond 45 and 90 min, by slot and department) are reported too.

Writes data/interim/analysis/curve_controls.txt (full report),
data/interim/analysis/curve_controls_summary.txt (one paragraph, sent by
phone) and data/processed/routes_curve_v2.json (per neighbourhood: 12
values without constraint, 12 wheelchair, 3 wheelchair with unknown =
accessible at night; null = more than 90 min).
Usage (project Docker image): python scripts/analysis/curve_controls.py
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("ROUTES_VERSION", "2")

import numpy as np
import pandas as pd

import config

spec = importlib.util.spec_from_file_location("s36", ROOT / "36_route_aggregate.py")
s36 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s36)

TTM = config.DATA_INTERIM / "access" / "routes_ttm_curve_v2"
OUT = config.DATA_INTERIM / "analysis"
HOURS = list(range(0, 24, 2))
NIGHT = [0, 2, 4]
N_CHUNKS = 46
PROFILES = {"standard": HOURS, "step_free_no": HOURS, "step_free_yes": NIGHT}
# CURVE_TEST=1: only the tasks already finished (code test during the run;
# never for the real controls).
TEST = os.environ.get("CURVE_TEST") == "1"
TAG = "_test" if TEST else ""
LABEL = {"standard": "sans contrainte", "step_free_no": "fauteuil roulant (inconnu = non)", "step_free_yes": "fauteuil roulant (inconnu = oui)"}
DEPTS = ["75", "92", "93", "94"]
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def load(name):
    files = sorted(TTM.glob(f"{name}_*.parquet"))
    if len(files) != N_CHUNKS:
        if TEST:
            return None
        raise SystemExit(f"{name}: {len(files)} chunks of {N_CHUNKS}, run not finished")
    t = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    return t[t["type"] == "emergency"].set_index("cell_id")["minutes"]


cells = s36.cells_by_iris()
pop_iris = cells.groupby("code_iris")["pop"].sum()
inhabited = pop_iris[pop_iris >= 50].index
grid = cells.drop_duplicates("cell_id").set_index("cell_id")
grid["dept"] = grid["code_iris"].astype(str).str[:2]

times = {}
for p, hours in PROFILES.items():
    for h in hours:
        t = load(f"{p}_tue{h:02d}")
        if t is not None:
            times[(p, h)] = t
PROFILES = {p: [h for h in hours if (p, h) in times] for p, hours in PROFILES.items()}


def per_iris(series):
    """{code_iris: minutes or None}, script 36 rules."""
    df = cells.copy()
    df["m"] = df["cell_id"].map(series).astype(float).fillna(np.inf)
    out = {}
    for code, g in df.groupby("code_iris"):
        m = s36.weighted_median(g["m"].to_numpy(), g["pop"].to_numpy(dtype=float))
        out[code] = None if not np.isfinite(m) else int(round(m))
    return out


iris_vals = {k: per_iris(v) for k, v in times.items()}


def published(slot, profile):
    d = json.loads((config.DATA_PROCESSED / f"routes_iris_{slot}.json").read_text(encoding="utf-8"))
    blocks, types = d["layout"]["blocks"], d["layout"]["types"]
    i = blocks.index(f"time:{profile}") * len(types) + types.index("emergency")
    return {code: v[i] for code, v in d["iris"].items()}


say("Courbe des urgences : contrôles avant publication")
say(f"Neighbourhoods with cells: {len(pop_iris)}; inhabited (>= 50 residents): {len(inhabited)}")

# 1. 10:00 slot against the published values
say("\n1. Créneau de 10 h comparé aux durées publiées (quartiers habités)")
control1 = []
for p in ("standard", "step_free_no"):
    if (p, 10) not in iris_vals:
        continue
    pub = published("tue10", p)
    new = iris_vals[(p, 10)]
    diff = [c for c in inhabited if pub.get(c) != new.get(c)]
    share = 100 * len(diff) / len(inhabited)
    control1.append(share)
    say(f"   {LABEL[p]} : {len(diff)} quartiers différents sur {len(inhabited)} ({share:.2f} %)" + (f" ; exemples {diff[:5]}" if diff else ""))
ok1 = len(control1) == 2 and max(control1) <= 1.0
say(f"   -> {'OK (au plus 1 %)' if ok1 else 'ÉCART (plus de 1 %) : rien n est publié avant explication'}")

# 2. Inversions
say("\n2. Inversions (fauteuil roulant plus rapide que sans contrainte), couples carreau x créneau")
inv = tot = 0
for h in HOURS:
    if ("standard", h) not in times or ("step_free_no", h) not in times:
        continue
    s, w = times[("standard", h)], times[("step_free_no", h)]
    both = s.index.intersection(w.index)
    inv += int((w[both] < s[both]).sum())
    tot += len(both)
say(f"   {inv} sur {tot} ({100 * inv / max(tot, 1):.3f} %)")

# 3. Completeness and the Method table
say("\n3. Part de la population au-delà de 90 min, et tableau de la Méthode")
say("   profil | heure | médiane des quartiers (MGP / 75 / 92 / 93 / 94) | population > 45 min | population > 90 min (MGP / 75 / 92 / 93 / 94)")
total_pop = grid["pop"].sum()
for p, hours in PROFILES.items():
    for h in hours:
        m = grid["pop"].index.map(times[(p, h)]).astype(float)
        mins = pd.Series(np.where(np.isnan(m), np.inf, m), index=grid.index)
        v = pd.Series(iris_vals[(p, h)]).reindex(inhabited).astype(float).fillna(np.inf)
        meds = [np.median(v)] + [np.median(v[v.index.astype(str).str[:2] == d]) for d in DEPTS]
        over45 = 100 * grid["pop"][mins > 45].sum() / total_pop
        over90 = [100 * grid["pop"][mins > 90].sum() / total_pop] + [100 * grid["pop"][(mins > 90) & (grid.dept == d)].sum() / grid["pop"][grid.dept == d].sum() for d in DEPTS]
        fmt = lambda x: "> 90" if not np.isfinite(x) else f"{x:.0f}"
        say(f"   {LABEL[p]} | {h:02d} h | {' / '.join(fmt(x) for x in meds)} | {over45:.1f} % | {' / '.join(f'{x:.1f}' for x in over90)} %")

# 4. Coherence with the published 21:00 and 1:00
say("\n4. Cohérence avec les créneaux publiés (quartiers habités dont la valeur publiée est comprise entre les deux points voisins de la courbe)")
for slot, (a, b) in (("tue21", (20, 22)), ("tue01", (0, 2))):
    for p in ("standard", "step_free_no", "step_free_yes"):
        if (p, a) not in iris_vals or (p, b) not in iris_vals:
            continue
        pub = published(slot, p)
        inside = n = 0
        for c in inhabited:
            x, lo, hi = pub.get(c), iris_vals[(p, a)].get(c), iris_vals[(p, b)].get(c)
            x, lo, hi = [np.inf if y is None else y for y in (x, lo, hi)]
            n += 1
            inside += min(lo, hi) <= x <= max(lo, hi)
        say(f"   {slot} {LABEL[p]} : {inside} sur {n} ({100 * inside / n:.1f} %)")

# Night sensitivity
say("\nSensibilité de nuit : fauteuil roulant, inconnu = oui comparé à inconnu = non")
for h in PROFILES["step_free_yes"]:
    no = pd.Series(iris_vals[("step_free_no", h)]).reindex(inhabited).astype(float).fillna(np.inf)
    yes = pd.Series(iris_vals[("step_free_yes", h)]).reindex(inhabited).astype(float).fillna(np.inf)
    rho = no.rank().corr(yes.rank())
    say(f"   {h:02d} h : médiane des quartiers {np.median(no):.0f} -> {np.median(yes):.0f} min ; quartiers à plus de 90 min {int(np.isinf(no).sum())} -> {int(np.isinf(yes).sum())} ; Spearman {rho:.3f}")

# Curve file for the page
curve = {}
for code in sorted(pop_iris.index):
    curve[code] = [iris_vals[(p, h)].get(code) for p, hours in PROFILES.items() for h in hours]
layout = {"blocks": [f"{p}:{','.join(f'{h:02d}' for h in hours)}" for p, hours in PROFILES.items()], "day": "2026-10-13"}
(config.DATA_PROCESSED / f"routes_curve_v2{TAG}.json").write_text(json.dumps({"max_minutes": 90, "layout": layout, "iris": curve}, separators=(",", ":")), encoding="utf-8")
say(f"\nwrote routes_curve_v2{TAG}.json ({(config.DATA_PROCESSED / f'routes_curve_v2{TAG}.json').stat().st_size / 1e6:.2f} MB)")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / f"curve_controls{TAG}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
summary = (f"Contrôle du créneau de 10 h : {'OK' if ok1 else 'ÉCART'} ({' ; '.join(f'{x:.2f} %' for x in control1)} de quartiers différents, sans contrainte puis fauteuil roulant ; seuil 1 %). "
           f"Inversions : {100 * inv / max(tot, 1):.3f} % des couples carreau x créneau. Rapport complet : data/interim/analysis/curve_controls.txt")
(OUT / f"curve_controls_summary{TAG}.txt").write_text(summary + "\n", encoding="utf-8")
print(summary)
