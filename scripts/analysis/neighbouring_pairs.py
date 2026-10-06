"""Neighbouring neighbourhoods whose living conditions differ the most (rule
written and committed on 2026-10-06 22:17, before any calculation:
docs/checks/2026-10-06-neighbouring-pairs-rule.md). For the launch post;
not a method result, nothing published on the site.

Eligible: >= 500 residents, INSEE type H (housing), less than half of the
area in open green spaces, cemeteries (OSM landuse=cemetery /
amenity=grave_yard) or activity zones (MOS 2025 posts 37-54, 78), the four
themes known. Neighbours: shared boundary (more than a single point) or a
walk of 15 min or less between the inhabited centres (population-weighted
centre of the inhabited 200 m cells, snapped as in script 42; R5 on the full
street network, 4.5 km/h). Gap = sum over the 4 themes of rank(A) - rank(B),
A being the neighbourhood with the higher sum; each neighbourhood used once.

Heavy (loads the full street network, ~9 GB): run after the grand
calculation (durations by way of getting around are shown for each pair,
from the published neighbourhood files). Writes
data/interim/analysis/neighbouring_pairs/.
"""
import datetime as dt
import importlib
import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmium
import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

snap42 = importlib.import_module("42_snap_points")
OUT = config.DATA_INTERIM / "analysis" / "neighbouring_pairs"
THEMES = ["thermal", "pollution", "housing", "access_care"]
THEME_FR = {"thermal": "Chaleur", "pollution": "Air et bruit", "housing": "Performance énergétique des logements", "access_care": "Accès aux soins"}
ACTIVITY_MOS = {str(c) for c in list(range(37, 55)) + [78]}
GENERIC = re.compile(r"^(iris|quartier|zone)\s*\d+$", re.IGNORECASE)
MIN_POP, WALK_MAX, CANDIDATE_M = 500, 15, 1500
MODES = ["free", "slow", "wheelchair"]
# Durations shown for information (addendum of 2026-10-06 to the rule; never in the gap).
DURATIONS = [("times", "emergency", "Urgences"), ("times", "town_hall", "Mairie"), ("times", "caf", "CAF"),
             ("places", "food_store", "Supérette ou supermarché"), ("places", "creche", "Crèche"),
             ("places", "elementary_public", "École élémentaire publique"), ("station", None, "Arrêt du réseau lourd à pied")]


class Cemeteries(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.wkb = osmium.geom.WKBFactory()
        self.polys = []

    def area(self, a):
        t = a.tags
        if t.get("landuse") == "cemetery" or t.get("amenity") == "grave_yard":
            try:
                from shapely import wkb
                self.polys.append(wkb.loads(self.wkb.create_multipolygon(a), hex=True))
            except Exception:
                pass


def readable(rec):
    return f"un quartier de {rec['commune']}" if GENERIC.match(rec["name"].strip()) else rec["name"]


def sentence(theme, rank):
    n = min(9, max(0, round(rank * 10)))
    if theme == "access_care":
        return "Sur 10 quartiers, aucun n'a un accès aux soins plus facile" if n == 0 else f"Sur 10 quartiers, {n} {'a' if n == 1 else 'ont'} un accès aux soins plus facile"
    return "Sur 10 quartiers, aucun n'est moins exposé" if n == 0 else f"Sur 10 quartiers, {n} {'est moins exposé' if n == 1 else 'sont moins exposés'}"


def main():
    import r5py

    OUT.mkdir(parents=True, exist_ok=True)
    recs = {}
    for f in (config.DATA_PROCESSED / "quartiers").glob("[0-9]*.json"):
        for r in json.loads(f.read_text(encoding="utf-8"))["iris"]:
            recs[r["code"]] = r
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED).set_index("code_iris")

    # Land use: green spaces, cemeteries, activity zones.
    green = gpd.read_file(config.DATA_RAW / "cool_spots_green_areas" / "cool_spots_green_areas_raw.geojson").to_crs(config.CRS_PROJECTED)
    mos = gpd.read_file(config.DATA_RAW / "artificialization_mos" / "artificialization_mos_raw.geojson")
    mos = mos[mos["mos2025"].astype(str).isin(ACTIVITY_MOS)].to_crs(config.CRS_PROJECTED)
    h = Cemeteries()
    h.apply_file(str(config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"), locations=True, idx="flex_mem")
    cem = gpd.GeoDataFrame(geometry=h.polys, crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED)
    print(f"{len(green)} green spaces, {len(cem)} cemeteries, {len(mos)} activity polygons", flush=True)
    covers = gpd.GeoDataFrame(geometry=pd.concat([green.geometry, cem.geometry, mos.geometry], ignore_index=True), crs=config.CRS_PROJECTED)
    covers = covers[covers.is_valid | covers.buffer(0).is_valid]
    covers["geometry"] = covers.buffer(0)

    rows = []
    for code, r in recs.items():
        if code not in iris.index:
            continue
        reasons = []
        pop = r.get("population") or 0
        if pop < MIN_POP:
            reasons.append("population")
        if iris.at[code, "typ_iris"] != "H":
            reasons.append(f"type {iris.at[code, 'typ_iris']}")
        if any(r["exposures"][k]["rank"] is None for k in THEMES):
            reasons.append("theme missing")
        rows.append({"code": code, "pop": pop, "reasons": reasons})
    cand = pd.DataFrame(rows).set_index("code")
    keep = cand[cand.reasons.str.len() == 0].index
    poly = iris.loc[keep, "geometry"]
    hits = gpd.sjoin(gpd.GeoDataFrame(geometry=poly, crs=iris.crs), covers, predicate="intersects", how="inner")
    share = {}
    for code, grp in hits.groupby(level=0):
        u = unary_union(covers.geometry.iloc[grp["index_right"].to_numpy()].to_numpy())
        share[code] = poly[code].intersection(u).area / poly[code].area
    eligible = [c for c in keep if share.get(c, 0) <= 0.5]
    excluded_land = sorted((c for c in keep if share.get(c, 0) > 0.5), key=lambda c: -share[c])
    print(f"eligible {len(eligible)}; excluded: population {sum('population' in x for x in cand.reasons)}, "
          f"type {sum(any(y.startswith('type') for y in x) for x in cand.reasons)}, land use {len(excluded_land)}", flush=True)

    # Inhabited centres: population-weighted centre of the inhabited cells, snapped as in script 42.
    cells = gpd.read_file(config.DATA_PROCESSED / "access" / "demand_grid_idf.geojson")[["cell_id", "pop", "geometry"]].to_crs(config.CRS_PROJECTED)
    cells = cells[cells["pop"] > 0].copy()
    cells["geometry"] = cells.geometry.centroid
    inside = gpd.sjoin(cells, gpd.GeoDataFrame(geometry=iris.loc[eligible, "geometry"], crs=iris.crs), predicate="within", how="inner")
    cen = {}
    for code, g in inside.groupby("code_iris" if "code_iris" in inside else "index_right"):
        w = g["pop"].to_numpy()
        cen[code] = Point((g.geometry.x * w).sum() / w.sum(), (g.geometry.y * w).sum() / w.sum())
    for c in eligible:
        cen.setdefault(c, iris.at[c, "geometry"].representative_point())
    centres = gpd.GeoSeries([cen[c] for c in eligible], index=eligible, crs=config.CRS_PROJECTED)
    sh = snap42.Streets()
    sh.apply_file(str(snap42.PBF), locations=True, idx="flex_mem")
    nets = []
    for lines in (sh.streets, sh.walkable):
        arr = gpd.GeoSeries(lines, crs=config.CRS_LATLON).to_crs(config.CRS_PROJECTED).to_numpy()
        nets.append((arr, snap42.STRtree(arr)))
    sn = snap42.snap(centres.to_crs(config.CRS_LATLON), nets)
    pts = gpd.GeoDataFrame({"id": eligible}, geometry=gpd.points_from_xy(sn.lon, sn.lat), crs=config.CRS_LATLON)

    # Candidate pairs: shared boundary, or centres within 1.5 km.
    g = iris.loc[eligible, "geometry"]
    sj = gpd.sjoin(gpd.GeoDataFrame({"a": eligible}, geometry=g.buffer(1).to_numpy(), crs=iris.crs),
                   gpd.GeoDataFrame({"b": eligible}, geometry=g.to_numpy(), crs=iris.crs), predicate="intersects")
    touching = set()
    for a, b in zip(sj["a"], sj["b"]):
        if a < b and g[a].buffer(1).intersection(g[b].boundary).length > 5:
            touching.add((a, b))
    xy = np.c_[centres.x.to_numpy(), centres.y.to_numpy()]
    near = set()
    for i, a in enumerate(eligible):
        d = np.hypot(xy[:, 0] - xy[i, 0], xy[:, 1] - xy[i, 1])
        for j in np.nonzero(d <= CANDIDATE_M)[0]:
            if eligible[j] > a:
                near.add((a, eligible[j]))
    pairs = touching | near
    print(f"{len(touching)} touching pairs, {len(pairs)} candidate pairs", flush=True)

    osm, gtfs = config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf", config.DATA_RAW / "gtfs" / "IDFM-gtfs.zip"
    network = r5py.TransportNetwork(str(osm), [str(gtfs)])
    ttm = pd.DataFrame(r5py.TravelTimeMatrix(network, origins=pts, destinations=pts, departure=dt.datetime(2026, 10, 13, 10, 0),
                                             transport_modes=[r5py.TransportMode.WALK], speed_walking=4.5,
                                             max_time=dt.timedelta(minutes=40), snap_to_network=False))
    walk = {(a, b): t for a, b, t in ttm[["from_id", "to_id", "travel_time"]].itertuples(index=False)}

    out = []
    for a, b in pairs:
        ta, tb = walk.get((a, b)), walk.get((b, a))
        t = np.nanmin([np.nan if ta is None else ta, np.nan if tb is None else tb]) if (ta is not None or tb is not None) else np.nan
        is_touch = (a, b) in touching
        if not (is_touch or (t == t and t <= WALK_MAX)):
            continue
        ra = np.array([recs[a]["exposures"][k]["rank"] for k in THEMES])
        rb = np.array([recs[b]["exposures"][k]["rank"] for k in THEMES])
        hi, lo, rh, rl = (a, b, ra, rb) if ra.sum() >= rb.sum() else (b, a, rb, ra)
        out.append({"a": hi, "b": lo, "gap": float((rh - rl).sum()), "themes_worse": int((rh > rl).sum()), "touching": is_touch,
                    "walk_min": None if t != t else int(t), "same_commune": recs[hi]["commune"] == recs[lo]["commune"]})
    df = pd.DataFrame(out).sort_values(["gap", "themes_worse"], ascending=False)
    df.to_csv(OUT / "neighbouring_pairs_all.csv", index=False)
    used, top = set(), []
    for r in df.itertuples(index=False):
        if r.a in used or r.b in used:
            continue
        top.append(r)
        used |= {r.a, r.b}
        if len(top) == 20:  # 10 + spares for the imagery check
            break

    lines = ["Paires de quartiers voisins au cadre de vie le plus différent (règle du 06/10/2026 22 h 17)", "=" * 90,
             f"quartiers retenus : {len(eligible)} ; paires voisines : {len(df)} (dont qui se touchent : {int(df.touching.sum())})",
             f"écartés pour l'occupation du sol (> 50 % espaces verts, cimetières, activité) : {len(excluded_land)}",
             "20 premières paires (chaque quartier une fois) ; les 10 premières après vérification à l'imagerie sont rendues", ""]
    for i, r in enumerate(top, 1):
        same = " — MÊME COMMUNE" if r.same_commune else ""
        lines.append(f"{i}. écart {r.gap:.2f} (plus exposé sur {r.themes_worse}/4 thèmes){same}")
        lines.append(f"   {'se touchent' if r.touching else 'ne se touchent pas'} ; à pied entre les centres habités : "
                     f"{'plus de 40 min' if r.walk_min is None else f'{r.walk_min} min'}")
        for code in (r.a, r.b):
            q = recs[code]
            lines.append(f"   - {readable(q)} ({q['name']}, {code}), {q['commune']}, {q['population']:,} habitants".replace(",", " "))
            for k in THEMES:
                lines.append(f"       {THEME_FR[k]} : {sentence(k, q['exposures'][k]['rank'])} (rang {q['exposures'][k]['rank']:.3f})")
            for group, place, label in DURATIONS:
                v = {m: ((q.get(group) or {}).get(m) or {}).get(place) if place else (q.get(group) or {}).get(m) for m in MODES}
                fmt = lambda x: "> 90 min" if x is None else f"{x} min"
                gap = "" if v["free"] is None or v["wheelchair"] is None else f" (fauteuil roulant {v['wheelchair'] - v['free']:+d} min)"
                lines.append(f"       {label} : sans contrainte {fmt(v['free'])}, marche lente {fmt(v['slow'])}, fauteuil roulant {fmt(v['wheelchair'])}{gap}")
        lines.append("")
    (OUT / "neighbouring_pairs.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame([r._asdict() for r in top]).to_csv(OUT / "neighbouring_pairs_top20.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
