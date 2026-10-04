"""Stock of pairs for the "Lequel de ces quartiers ?" questions of the home
page (rules validated by the project lead on 2026-10-04).

Among inhabited neighbourhoods with complete exposure data and a resources
third (published neighbourhood files, script 39):
- close but different: representative points at most 800 m apart, number
  of exposures in the most affected quarter (heat, air and noise, housing)
  differing by 2 or 3;
- far apart but alike: at least 10 km apart, different départements, the
  same exposures (2 or 3 of 3, the same ones), opposite resources thirds
  (lowest and highest).
The page draws one pair at random from the whole stock. Names stay out of
the question; the answer gives readable names (a generic INSEE name such
as "Iris 10" becomes "un quartier du Blanc-Mesnil" on the page) and links
to the neighbourhood pages. To be rebuilt after each travel-time or score
update.

Output: data/processed/question_pairs.json, copied to frontend/public/data/.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from shapely.geometry import shape

import config

QDIR = config.DATA_PROCESSED / "quartiers"
OUT = config.DATA_PROCESSED / "question_pairs.json"
EXPO = ["thermal", "pollution", "housing"]
CLOSE_M = 800
FAR_M = 10_000
GENERIC = re.compile(r"^(iris|quartier|zone)\s*\d+$", re.IGNORECASE)


def main():
    recs = []
    for f in sorted(QDIR.glob("[0-9]*.json")):
        for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
            ex = r.get("exposures") or {}
            if not r.get("inhabited") or not r.get("means") or r["means"].get("third") is None:
                continue
            if any((ex.get(k) or {}).get("status", "ok") != "ok" or (ex.get(k) or {}).get("quarter") is None for k in EXPO):
                continue
            pt = shape(r["geometry"]).representative_point()
            recs.append({
                "code": r["code"], "name": r["name"], "commune": r["commune"],
                "generic": bool(GENERIC.match(r["name"].strip())),
                "exp": [k for k in EXPO if ex[k]["quarter"] == 4],
                "third": int(r["means"]["third"]), "x": pt.x, "y": pt.y,
            })
    n = len(recs)
    xy = np.array([[r["x"], r["y"]] for r in recs])
    kx, ky = 111_320 * np.cos(np.radians(48.85)), 110_540
    dist = np.hypot((xy[:, None, 0] - xy[None, :, 0]) * kx, (xy[:, None, 1] - xy[None, :, 1]) * ky)
    nexp = np.array([len(r["exp"]) for r in recs])
    dep = np.array([r["code"][:2] for r in recs])
    sets = np.array(["+".join(r["exp"]) for r in recs])
    third = np.array([r["third"] for r in recs])
    i, j = np.triu_indices(n, 1)
    d = dist[i, j]

    close = (d <= CLOSE_M) & (np.abs(nexp[i] - nexp[j]) >= 2)
    far = (d >= FAR_M) & (dep[i] != dep[j]) & (sets[i] == sets[j]) & (nexp[i] >= 2) & (np.abs(third[i] - third[j]) == 2)

    # Compact: the neighbourhoods once, then the pairs as indices.
    used = sorted(set(i[close | far]) | set(j[close | far]))
    index = {k: n_ for n_, k in enumerate(used)}
    hoods = [[recs[k]["code"], recs[k]["name"], recs[k]["commune"], int(recs[k]["generic"]),
              "".join(e[0] for e in recs[k]["exp"]), recs[k]["third"]] for k in used]
    pairs = []
    for kind, mask in (("c", close), ("f", far)):
        for a, b, dd in zip(i[mask], j[mask], d[mask]):
            pairs.append([kind, int(round(dd / 10) * 10), index[a], index[b]])
    payload = {
        "layout": {"hood": ["code", "name", "commune", "generic", "exposures (t heat, p air and noise, h housing)", "third (0 lowest)"],
                   "pair": ["kind (c close, f far)", "distance_m", "hood a", "hood b"]},
        "rules": {"close_max_m": CLOSE_M, "far_min_m": FAR_M},
        "hoods": hoods,
        "pairs": pairs,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{n} neighbourhoods; pairs: close {int(close.sum()):,}, far {int(far.sum()):,}; {OUT.stat().st_size / 1e3:.0f} kB")


if __name__ == "__main__":
    main()
