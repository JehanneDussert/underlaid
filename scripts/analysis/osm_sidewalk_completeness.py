"""Audit: are OpenStreetMap sidewalks mapped evenly enough across the MGP?

One-off analysis, not part of the pipeline (run_all.py doesn't call it)
and nothing here feeds the score. It answers one question before access
to services is rebuilt: can a sidewalk indicator from OSM be compared
across departments? Result (2026-10-01, Geofabrik extract of 2026-09-30):
no — see docs/LESSONS.md and /methodology#osm-sidewalks.

What it counts:
- streets: highway in STREETS (trunk, motorway and service roads left out);
- drawn sidewalks: highway=footway|path with footway=sidewalk;
- sidewalks recorded on the street: sidewalk, sidewalk:both|left|right
  (yes/both/left/right, times the number of sides);
- no double counting: a street whose drawn sidewalks cover >= 50% of its
  length within 20 m counts only through the drawn lines;
- "sidewalk information" for a street = any sidewalk tag (including
  no/separate) or drawn sidewalks along it. Unknown is not absent.

Criterion fixed before computing: completeness is "markedly unequal" if,
within a population-density quintile holding >= 20 IRIS of each compared
department, street-length-weighted completeness differs by more than 15
percentage points between two departments.

Also reports, per department, how often attributes useful in a
wheelchair are recorded (width, surface, smoothness, incline on sidewalks;
kerb nodes per 100 pedestrian crossings).

Usage: python scripts/analysis/osm_sidewalk_completeness.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

import config
from utils.download import download_file

GEOFABRIK_URL = "https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf"
PBF_PATH = config.DATA_RAW / "osm" / "ile-de-france-latest.osm.pbf"
OUT_DIR = config.DATA_INTERIM / "analysis"

STREETS = {"primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link",
           "residential", "living_street", "unclassified"}
SIDE_KEYS = ("sidewalk", "sidewalk:both", "sidewalk:left", "sidewalk:right")
DRAWN_COVERAGE_BUFFER_M = 20
DRAWN_COVERAGE_MIN = 0.5
MAX_GAP_PP = 15
MIN_IRIS_PER_DEP_IN_BAND = 20
# Same floor as scripts/11 (MIN_POPULATION_FOR_RATE): density means little below it.
MIN_POPULATION = 50
WHEELCHAIR_ATTRS = {
    "width": ("width", "sidewalk:{s}:width", "sidewalk:width"),
    "surface": ("surface", "sidewalk:{s}:surface", "sidewalk:surface"),
    "smoothness": ("smoothness", "sidewalk:{s}:smoothness", "sidewalk:smoothness"),
    "incline": ("incline", "sidewalk:{s}:incline", "sidewalk:incline"),
}
TAG_RE = re.compile(r'"((?:[^"\\]|\\.)*)"=>"((?:[^"\\]|\\.)*)"')


def parse_tags(other_tags) -> dict:
    """GDAL's OSM driver packs non-default tags into an hstore string."""
    return dict(TAG_RE.findall(other_tags)) if isinstance(other_tags, str) else {}


def side_info(tags: dict) -> tuple[int, bool]:
    """(sides with a sidewalk recorded on the street, any sidewalk tag present)."""
    left = right = None
    value = tags.get("sidewalk")
    if value in ("both", "yes"):
        left = right = "yes"
    elif value == "left":
        left, right = "yes", "no"
    elif value == "right":
        left, right = "no", "yes"
    elif value in ("no", "none", "separate"):
        left = right = value
    if "sidewalk:both" in tags:
        left = right = tags["sidewalk:both"]
    left = tags.get("sidewalk:left", left)
    right = tags.get("sidewalk:right", right)
    return (left == "yes") + (right == "yes"), any(k in tags for k in SIDE_KEYS)


def has_attr(tags: dict, keys: tuple, on_street: bool) -> bool:
    if not on_street:
        return keys[0] in tags
    return keys[2] in tags or any(keys[1].format(s=side) in tags for side in ("both", "left", "right"))


def load_iris() -> gpd.GeoDataFrame:
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH)[["code_iris", "nom_iris", "nom_com", "geometry"]]
    pop = gpd.read_file(config.DATA_PROCESSED / "population_iris.geojson")[["code_iris", "population"]]
    iris = iris.merge(pop, on="code_iris", how="left").to_crs(config.CRS_PROJECTED)
    iris["dep"] = iris.code_iris.str[:2]
    iris["area_km2"] = iris.area / 1e6
    return iris


def load_osm(iris: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    bbox = tuple(iris.to_crs(config.CRS_LATLON).total_bounds)
    lines = pyogrio.read_dataframe(PBF_PATH, layer="lines", where="highway IS NOT NULL", bbox=bbox)
    lines["tags"] = lines.other_tags.map(parse_tags)
    streets = lines[lines.highway.isin(STREETS)].copy()
    drawn = lines[lines.highway.isin({"footway", "path"}) & lines.tags.map(lambda t: t.get("footway") == "sidewalk")].copy()
    points = pyogrio.read_dataframe(
        PBF_PATH, layer="points", bbox=bbox,
        where="highway = 'crossing' OR other_tags LIKE '%\"kerb\"%' OR barrier = 'kerb'",
    )
    points["kerb"] = points.other_tags.map(lambda s: parse_tags(s).get("kerb"))
    return (streets.to_crs(config.CRS_PROJECTED), drawn.to_crs(config.CRS_PROJECTED),
            points.to_crs(config.CRS_PROJECTED))


def classify_streets(streets: gpd.GeoDataFrame, drawn: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    info = streets.tags.map(side_info)
    streets["attr_sides"] = [i[0] for i in info]
    streets["tagged"] = [i[1] for i in info]
    streets["len"] = streets.length
    buffers = gpd.GeoDataFrame({"sid": np.arange(len(streets))},
                               geometry=streets.buffer(DRAWN_COVERAGE_BUFFER_M, cap_style=2).values, crs=streets.crs)
    pairs = gpd.overlay(drawn[["geometry"]], buffers, how="intersection", keep_geom_type=True)
    covered_len = pairs.assign(l=pairs.length).groupby("sid").l.sum()
    streets["covered"] = pd.Series(np.arange(len(streets))).map(covered_len).fillna(0).values / streets["len"].values >= DRAWN_COVERAGE_MIN
    streets["known"] = streets.tagged | streets.covered
    streets["attr_sides_net"] = np.where(streets.covered, 0, streets.attr_sides)
    streets["double_count_avoided"] = streets.covered & (streets.attr_sides > 0)
    return streets


def per_iris(streets, drawn, iris) -> pd.DataFrame:
    def split(gdf, cols):
        x = gpd.overlay(gdf[cols + ["geometry"]], iris[["code_iris", "geometry"]], how="intersection", keep_geom_type=True)
        x["l"] = x.length
        return x

    s = split(streets, ["tagged", "covered", "known", "attr_sides_net", "double_count_avoided"])
    d = split(drawn, [])
    sums = s.assign(
        street_len=s.l, known_len=s.l * s.known, tagged_len=s.l * s.tagged, covered_len=s.l * s.covered,
        attr_sw_len=s.l * s.attr_sides_net, dbl_len=s.l * s.double_count_avoided,
    ).groupby("code_iris")[["street_len", "known_len", "tagged_len", "covered_len", "attr_sw_len", "dbl_len"]].sum()
    sums["drawn_sw_len"] = d.groupby("code_iris").l.sum()
    g = iris.drop(columns="geometry").merge(sums, left_on="code_iris", right_index=True, how="left")
    length_cols = ["street_len", "known_len", "tagged_len", "covered_len", "attr_sw_len", "dbl_len", "drawn_sw_len"]
    g[length_cols] = g[length_cols].fillna(0)
    g["completeness"] = g.known_len / g.street_len.replace(0, np.nan)
    g["sidewalk_m_per_street_m"] = (g.drawn_sw_len + g.attr_sw_len) / g.street_len.replace(0, np.nan)
    g["density"] = g.population / g.area_km2
    return g


def wheelchair_attributes(streets, drawn, points, iris) -> pd.DataFrame:
    for name, keys in WHEELCHAIR_ATTRS.items():
        drawn[name] = drawn.tags.map(lambda t: has_attr(t, keys, False))
        streets[name] = streets.tags.map(lambda t: has_attr(t, keys, True))
    deps = iris[["dep", "geometry"]]
    dsw = gpd.sjoin(drawn.assign(swlen=drawn.length), deps, predicate="intersects").drop_duplicates(subset="osm_id")
    ssw = streets[streets.attr_sides_net > 0].assign(swlen=lambda x: x.len * x.attr_sides_net)
    ssw = gpd.sjoin(ssw, deps, predicate="intersects").drop_duplicates(subset="osm_id")
    pts = gpd.sjoin(points, deps, predicate="within")
    rows = []
    for dep in sorted(iris.dep.unique()):
        a, b, p = dsw[dsw.dep == dep], ssw[ssw.dep == dep], pts[pts.dep == dep]
        total = a.swlen.sum() + b.swlen.sum()
        row = {"dep": dep, "sidewalk_km": round(total / 1000)}
        for name in WHEELCHAIR_ATTRS:
            row[f"{name}_%"] = round(100 * (a.swlen[a[name]].sum() + b.swlen[b[name]].sum()) / total, 1)
        crossings, kerbs = (p.highway == "crossing").sum(), p.kerb.notna().sum()
        row["crossings"] = int(crossings)
        row["kerb_per_100_crossings"] = round(100 * kerbs / max(crossings, 1), 1)
        row["kerb_lowered_or_flush_%"] = round(100 * p.kerb.isin(["lowered", "flush"]).sum() / max(kerbs, 1), 1)
        rows.append(row)
    return pd.DataFrame(rows)


def report(g: pd.DataFrame, wheelchair: pd.DataFrame) -> None:
    dep = g.groupby("dep")[["street_len", "known_len", "drawn_sw_len", "attr_sw_len", "dbl_len"]].sum()
    dep["completeness_%"] = 100 * dep.known_len / dep.street_len
    dep["sidewalk_m_per_street_m"] = (dep.drawn_sw_len + dep.attr_sw_len) / dep.street_len
    dep["double_count_avoided_km"] = dep.dbl_len / 1000
    print("== Per department\n", dep[["completeness_%", "sidewalk_m_per_street_m", "double_count_avoided_km"]].round(2).to_string())

    ok = g[(g.population >= MIN_POPULATION) & (g.street_len >= 500)].copy()
    ok["band"] = pd.qcut(ok.density, 5, labels=["Q1 least dense", "Q2", "Q3", "Q4", "Q5 densest"])
    t = ok.groupby(["band", "dep"], observed=True).apply(
        lambda x: pd.Series({"n": len(x), "completeness_%": 100 * x.known_len.sum() / x.street_len.sum()}),
        include_groups=False,
    ).reset_index()
    print("\n== Completeness % at equal density (quintiles of residents per km2)")
    print(t.pivot(index="band", columns="dep", values="completeness_%").round(1).to_string())
    print(t.pivot(index="band", columns="dep", values="n").to_string())
    worst = 0.0
    for band, b in t.groupby("band", observed=True):
        eligible = b[b.n >= MIN_IRIS_PER_DEP_IN_BAND]
        if len(eligible) >= 2:
            worst = max(worst, eligible["completeness_%"].max() - eligible["completeness_%"].min())
    verdict = "markedly unequal" if worst > MAX_GAP_PP else "even enough"
    print(f"\nLargest gap at equal density: {worst:.1f} pp (threshold {MAX_GAP_PP}) -> {verdict}")
    print("\n== Wheelchair-relevant attributes\n", wheelchair.to_string(index=False))


def main():
    if not PBF_PATH.exists():
        download_file(GEOFABRIK_URL, PBF_PATH)
    iris = load_iris()
    streets, drawn, points = load_osm(iris)
    streets = classify_streets(streets, drawn)
    g = per_iris(streets, drawn, iris)
    wheelchair = wheelchair_attributes(streets, drawn, points, iris)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT_DIR / "osm_sidewalks_iris.csv", index=False)
    wheelchair.to_csv(OUT_DIR / "osm_wheelchair_attributes_dep.csv", index=False)
    report(g, wheelchair)


if __name__ == "__main__":
    main()
