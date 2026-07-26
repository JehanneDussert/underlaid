"""Spatial join helpers shared by every normalize script.

All functions expect/return GeoDataFrames already reprojected to a common
projected CRS (EPSG:2154, meters) when area or distance math is involved.
"""
import geopandas as gpd
import pandas as pd


def load_iris_reference(path, crs) -> gpd.GeoDataFrame:
    iris = gpd.read_file(path)
    return iris.to_crs(crs)


def join_points_to_iris(points: gpd.GeoDataFrame, iris: gpd.GeoDataFrame, iris_code_col: str = "code_iris") -> gpd.GeoDataFrame:
    """Attach the enclosing IRIS code to each point via point-in-polygon."""
    points = points.to_crs(iris.crs)
    joined = gpd.sjoin(points, iris[[iris_code_col, "geometry"]], how="left", predicate="within")
    return joined.drop(columns=["index_right"], errors="ignore")


def areal_weighted_aggregate(source: gpd.GeoDataFrame, iris: gpd.GeoDataFrame, value_cols: list[str], iris_code_col: str = "code_iris") -> pd.DataFrame:
    """Aggregate polygon values onto IRIS zones, weighting each source

    polygon's contribution by the share of its area that falls inside a
    given IRIS. Needed whenever the source layer's boundaries don't align
    with IRIS boundaries (e.g. a national heat-island grid, a noise zone).
    """
    source = source.to_crs(iris.crs)
    overlay = gpd.overlay(source, iris[[iris_code_col, "geometry"]], how="intersection")
    overlay["_intersection_area"] = overlay.geometry.area

    weighted = overlay.copy()
    for col in value_cols:
        weighted[col] = weighted[col] * weighted["_intersection_area"]

    grouped = weighted.groupby(iris_code_col).agg({**{c: "sum" for c in value_cols}, "_intersection_area": "sum"})
    for col in value_cols:
        grouped[col] = grouped[col] / grouped["_intersection_area"]
    return grouped.drop(columns=["_intersection_area"]).reset_index()


def area_share_per_iris(source: gpd.GeoDataFrame, iris: gpd.GeoDataFrame, iris_code_col: str = "code_iris", out_col: str = "pct_area_covered") -> pd.DataFrame:
    """Compute, for each IRIS, the share of its surface covered by source polygons."""
    source = source.to_crs(iris.crs)
    iris_area = iris[[iris_code_col, "geometry"]].copy()
    iris_area["_iris_area"] = iris_area.geometry.area

    overlay = gpd.overlay(source[["geometry"]], iris_area, how="intersection")
    overlay["_covered_area"] = overlay.geometry.area

    grouped = overlay.groupby(iris_code_col)["_covered_area"].sum().reset_index()
    result = iris_area[[iris_code_col, "_iris_area"]].merge(grouped, on=iris_code_col, how="left")
    result["_covered_area"] = result["_covered_area"].fillna(0)
    result[out_col] = result["_covered_area"] / result["_iris_area"]
    return result[[iris_code_col, out_col]]


def check_unmatched_codes(df: pd.DataFrame, iris: gpd.GeoDataFrame, code_col: str = "code_iris") -> None:
    """Log code_iris values that don't line up between a source dataset and

    the IRIS reference, instead of silently dropping them. A mismatch
    usually means the source uses a different IRIS vintage (zonages are
    revised periodically) and needs a manual code-crosswalk.
    """
    reference_codes = set(iris[code_col])
    source_codes = set(df[code_col].dropna())

    missing_from_reference = source_codes - reference_codes
    missing_from_source = reference_codes - source_codes

    if missing_from_reference:
        print(f"[WARN] {len(missing_from_reference)} code_iris in source but not in IRIS reference "
              f"(possible vintage mismatch): {sorted(missing_from_reference)[:10]}...")
    if missing_from_source:
        print(f"[WARN] {len(missing_from_source)} IRIS zones have no data in this source: "
              f"{sorted(missing_from_source)[:10]}...")
