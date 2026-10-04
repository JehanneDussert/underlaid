"""Material for two proposals to the project lead (4 October 2026), nothing
published:

A. one position bar per need on "Votre quartier": combine the places of a
   need by the mean of the minutes, or by the mean of each place's rank
   among inhabited neighbourhoods? Compares the two on the published
   durations (GP and pharmacy excluded, crushed at the floor).
B. "Lequel de ces quartiers ?" questions: candidate pairs for two rules
   (close but different; far apart but alike), from the published
   neighbourhood files. Names are printed here for the review only.
Writes data/interim/analysis/block2_proposals.txt.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

QDIR = ROOT / "frontend" / "public" / "data" / "quartiers"
OUT = config.DATA_INTERIM / "analysis" / "block2_proposals.txt"
NEEDS = {
    "care": ["emergency"],
    "admin": ["town_hall", "france_services", "caf", "cpam", "employment"],
    "food": ["food_store"],
    "children": ["creche", "nursery_school"],
    "post": ["post_office"],
    "police": ["police"],
    "social": ["social_centre", "library"],
    "cool": ["park", "drinking_water"],
    "toilets": ["toilets", "toilets_24h"],
}
EXPO = ["thermal", "pollution", "housing"]
lines = []


def say(s=""):
    print(s)
    lines.append(s)


rows = []
for f in sorted(QDIR.glob("[0-9]*.json")):
    for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
        rec = {"code": r["code"], "name": r["name"], "commune": r["commune"], "inhabited": r.get("inhabited"),
               "pop": r.get("population")}
        for group in ("times", "places", "paris_places"):
            for place, v in ((r.get(group) or {}).get("free") or {}).items():
                rec[place] = v
        ex = r.get("exposures") or {}
        rec["n_exp"] = sum(1 for k in EXPO if (ex.get(k) or {}).get("quarter") == 4)
        rec["exp_set"] = "+".join(k for k in EXPO if (ex.get(k) or {}).get("quarter") == 4)
        rec["exp_ok"] = all((ex.get(k) or {}).get("status", "ok") != "insufficient_data" for k in EXPO)
        rec["care_worst"] = (ex.get("access_care") or {}).get("quarter") == 4
        rec["means_third"] = (r.get("means") or {}).get("third")
        g = shape(r["geometry"])
        rec["x"], rec["y"] = g.representative_point().x, g.representative_point().y
        rows.append(rec)
df = pd.DataFrame(rows)
hab = df[df.inhabited == True].copy()  # noqa: E712

say("A. ONE BAR PER NEED: mean of minutes vs mean of ranks (sans contrainte, inhabited neighbourhoods)")
say("=" * 88)
for need, places in NEEDS.items():
    cols = [p for p in places if p in hab]
    sub = hab[cols].apply(pd.to_numeric, errors="coerce")
    ok = sub.notna().all(axis=1)
    if not ok.any():
        continue
    sub = sub[ok]
    minutes = sub.mean(axis=1)
    ranks = sub.rank(pct=True).mean(axis=1)
    dec_m = np.ceil(minutes.rank(pct=True) * 10)
    dec_r = np.ceil(ranks.rank(pct=True) * 10)
    rho = minutes.corr(ranks, method="spearman")
    share = sub.div(sub.sum(axis=1), axis=0).mean()
    say(f"{need:9} places {', '.join(cols)} | n {ok.sum():,} | Spearman {rho:.3f} | "
        f"decile differs {100 * (dec_m != dec_r).mean():.0f}%, by 2+ {100 * ((dec_m - dec_r).abs() >= 2).mean():.0f}% | "
        f"weight in the minute mean: " + ", ".join(f"{c} {100 * share[c]:.0f}%" for c in cols))

say("\nB. 'LEQUEL DE CES QUARTIERS ?' — candidate pairs (names for review only)")
say("=" * 88)
ok = hab[hab.exp_ok & hab.means_third.notna()].copy()
ok["dep"] = ok.code.str[:2]
pts = ok[["x", "y"]].to_numpy()
# metres, rough (lat 48.85)
kx, ky = 111_320 * np.cos(np.radians(48.85)), 110_540
dx = (pts[:, None, 0] - pts[None, :, 0]) * kx
dy = (pts[:, None, 1] - pts[None, :, 1]) * ky
dist = np.hypot(dx, dy)
iu = np.triu_indices(len(ok), 1)
pairs = pd.DataFrame({"i": iu[0], "j": iu[1], "d": dist[iu]})
a = ok.reset_index(drop=True)

close = pairs[pairs.d <= 800].copy()
close["gap"] = (a.n_exp.to_numpy()[close.i] - a.n_exp.to_numpy()[close.j])
close = close[close.gap.abs() >= 2]
say(f"\nRule 1 — close but different: representative points <= 800 m apart, exposure counts differing by 2 or 3 "
    f"(0 vs 2-3, or 1 vs 3): {len(close):,} pairs, {pd.unique(close[['i', 'j']].values.ravel()).size:,} neighbourhoods")
for _, p in close.sort_values("d").groupby(close.i.map(a.commune)).head(1).sample(frac=1, random_state=3).head(8).iterrows():
    A, B = a.loc[p.i], a.loc[p.j]
    say(f"  {A['name']} ({A.commune}) {A.n_exp}/3 [{A.exp_set or '-'}] vs {B['name']} ({B.commune}) {B.n_exp}/3 [{B.exp_set or '-'}], {p.d:.0f} m")

far = pairs[pairs.d >= 10_000].copy()
far = far[(a.exp_set.to_numpy()[far.i] == a.exp_set.to_numpy()[far.j]) & (a.n_exp.to_numpy()[far.i] >= 2)]
far = far[a.dep.to_numpy()[far.i] != a.dep.to_numpy()[far.j]]
far["thirds"] = a.means_third.to_numpy()[far.i].astype(int).astype(str) + "-" + a.means_third.to_numpy()[far.j].astype(int).astype(str)
far = far[far.thirds.isin(["0-2", "2-0"])]
say(f"\nRule 2 — far apart but alike: >= 10 km, different departments, same exposures (2 or 3 of 3, same ones), "
    f"opposite resources thirds (lowest vs highest): {len(far):,} pairs")
for _, p in far.sample(frac=1, random_state=5).drop_duplicates("i").head(8).iterrows():
    A, B = a.loc[p.i], a.loc[p.j]
    say(f"  {A['name']} ({A.commune}) [{A.exp_set}] third {A.means_third} vs {B['name']} ({B.commune}) [{B.exp_set}] third {B.means_third}, {p.d / 1000:.0f} km")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
