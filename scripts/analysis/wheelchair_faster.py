"""Diagnostic (4 October 2026, asked by the project lead): durations shorter
in the wheelchair (step-free) profile than without constraint.

The step-free profile uses a subset of the standard networks (streets
without stairs, transit trips and stops flagged accessible), with the same
walking speed. For one departure minute, the best step-free journey can
therefore not be faster than the best standard one; the median over the
departure window, the minimum over destinations of a type and the
population-weighted median over cells all preserve that order. Any
inversion must come from elsewhere. This script measures them, changes
nothing, and writes data/interim/analysis/wheelchair_faster.txt.

Levels:
  1. cells (script 34 outputs): per type, time slot and variant, share of
     cells where step-free < standard, and by how many minutes;
  2. walking only (stations task): same comparison with no transit and no
     departure window, restricted to the stops kept in both profiles, to
     isolate the street network;
  3. neighbourhoods (published files): count of neighbourhood x place
     pairs where the wheelchair duration shown is below the "sans
     contrainte" one, and by how many minutes.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402

ACCESS = config.DATA_INTERIM / "access"
OUT = config.DATA_INTERIM / "analysis" / "wheelchair_faster.txt"
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def load(ttm_dir: Path, task: str) -> pd.DataFrame:
    files = sorted(ttm_dir.glob(f"{task}_[0-9][0-9].parquet"))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True) if files else pd.DataFrame()


def compare(ttm_dir: Path, slot: str, variant: str):
    std = load(ttm_dir, f"standard_{slot}")
    sf = load(ttm_dir, f"step_free_{variant}_{slot}")
    if std.empty or sf.empty:
        return None
    m = std.merge(sf, on=["cell_id", "type"], suffixes=("_std", "_sf"))
    m["diff"] = m.minutes_sf - m.minutes_std
    return m


def describe(m: pd.DataFrame, label: str):
    say(f"\n{label}: {len(m):,} cell x type pairs reached in both profiles")
    say(f"{'type':16} {'pairs':>8} {'faster %':>9} {'-1':>7} {'-2':>6} {'-3..-5':>7} {'< -5':>6} {'min':>5}")
    for t, g in m.groupby("type"):
        f = g[g["diff"] < 0]
        say(f"{t:16} {len(g):8,} {100 * len(f) / len(g):8.1f}% {(f['diff'] == -1).sum():7,} {(f['diff'] == -2).sum():6,} "
            f"{f['diff'].between(-5, -3).sum():7,} {(f['diff'] < -5).sum():6,} {int(f['diff'].min()) if len(f) else 0:5}")
    f = m[m["diff"] < 0]
    say(f"{'all':16} {len(m):8,} {100 * len(f) / len(m):8.1f}% {(f['diff'] == -1).sum():7,} {(f['diff'] == -2).sum():6,} "
        f"{f['diff'].between(-5, -3).sum():7,} {(f['diff'] < -5).sum():6,} {int(f['diff'].min()) if len(f) else 0:5}")


say("Durations shorter in the step-free (wheelchair) profile than without constraint")
say("=" * 78)

say("\n1. CELLS (200 m, script 34), Tuesday 10:00, step-free 'unknown = no' (published)")
for ttm_dir, name in [(ACCESS / "routes_ttm", "key places"), (ACCESS / "routes_ttm_neighbourhood", "everyday places"),
                      (ACCESS / "routes_ttm_paris", "Paris toilets and fountains")]:
    m = compare(ttm_dir, "tue10", "no")
    if m is not None:
        describe(m, f"{name}")

say("\nSame, other variant and other time slots (key places, all types together)")
for slot in ["tue10", "tue21", "tue01", "sun10"]:
    for variant in ["no", "yes"]:
        m = compare(ACCESS / "routes_ttm", slot, variant)
        f = m[m["diff"] < 0]
        say(f"  {slot} unknown={variant}: {100 * len(f) / len(m):.1f}% of pairs faster step-free "
            f"(1 min: {100 * (f['diff'] == -1).mean() if len(f) else 0:.0f}% of them; worst {int(f['diff'].min()) if len(f) else 0} min)")

say("\n2. WALKING ONLY (no transit, no departure window): nearest heavy-rail stop")
say("   Destinations differ between profiles (accessible stops only in step-free), so a")
say("   faster step-free walk to the nearest stop is possible only through the street")
say("   network itself. Cells where step-free < standard:")
for variant in ["no", "yes"]:
    std = load(ACCESS / "routes_ttm", "standard_stations_walk")
    sf = load(ACCESS / "routes_ttm", f"step_free_{variant}_stations_walk")
    m = std.merge(sf, on=["cell_id", "type"], suffixes=("_std", "_sf"))
    d = m.minutes_sf - m.minutes_std
    say(f"  unknown={variant}: {(d < 0).sum():,} of {len(m):,} cells ({100 * (d < 0).mean():.1f}%), "
        f"of which 1 min {(d == -1).sum():,}, worst {int(d.min())} min")

say("\n3. NEIGHBOURHOODS (published files, frontend/public/data/quartiers)")
qdir = ROOT / "frontend" / "public" / "data" / "quartiers"
rows = []
for f in sorted(qdir.glob("[0-9]*.json")):
    data = json.loads(f.read_text(encoding="utf-8"))
    for r in data["iris"]:
        for group in ("times", "places", "paris_places"):
            g = r.get(group) or {}
            for place, free in (g.get("free") or {}).items():
                wc = (g.get("wheelchair") or {}).get(place)
                if isinstance(free, (int, float)) and isinstance(wc, (int, float)):
                    rows.append((r["code"], r["name"], r.get("inhabited"), place, free, wc))
        for group in ("night_emergency", "station"):
            g = r.get(group) or {}
            if isinstance(g.get("free"), (int, float)) and isinstance(g.get("wheelchair"), (int, float)):
                rows.append((r["code"], r["name"], r.get("inhabited"), group, g["free"], g["wheelchair"]))
df = pd.DataFrame(rows, columns=["code", "name", "inhabited", "place", "free", "wheelchair"])
df["diff"] = df.wheelchair - df.free
inv = df[df["diff"] < 0]
say(f"neighbourhood x place pairs with both durations: {len(df):,}")
say(f"wheelchair shorter: {len(inv):,} pairs ({100 * len(inv) / len(df):.1f}%), in {inv.code.nunique():,} neighbourhoods "
    f"of {df.code.nunique():,} (inhabited: {inv[inv.inhabited == True].code.nunique():,})")
say(f"by how much: " + ", ".join(f"{-k} min: {v:,}" for k, v in inv['diff'].value_counts().sort_index(ascending=False).items()))
say("by place: " + ", ".join(f"{k} {v}" for k, v in inv.place.value_counts().items()))
say("\nlargest gaps:")
for _, r in inv.sort_values("diff").head(12).iterrows():
    say(f"  {r['name']} ({r.code}) {r.place}: free {r.free}, wheelchair {r.wheelchair}")
b = df[df.name == "Batignolles 14"]
say("\nBatignolles 14: " + ", ".join(f"{r.place} {r.free}/{r.wheelchair}" for _, r in b.iterrows()))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
