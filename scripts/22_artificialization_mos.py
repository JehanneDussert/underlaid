"""Download and normalize % artificialized/impermeable surface per IRIS.

Third thermal sub-score indicator (Phase 5), alongside the ICU heat
index and cool spots: artificialized/sealed ground is a structural
cause of heat retention, not just another temperature measurement, so
it enriches the thermal sub-score rather than duplicating it.

Source: originally scoped as IGN's OCS GE "Artificialisation" product,
but that turned out to be distributed only as WMTS/WMS map tiles (no
vector data to compute a per-IRIS share from), and the underlying
vector OCS GE product requires large per-department bulk downloads via
a JS-rendered portal with no discoverable direct-download URL or WFS
API — unlike every other source in this pipeline. Decided with the user
to use data.iledefrance.fr's own land-use survey instead ("MOS",
Mode d'Occupation du Sol, 79-category legend, 2021 vintage — kept
consistent with Filosofi/population's 2021 vintage rather than using
the newer 2025 edition also present in this dataset).

Classification into "artificialized" vs. not (documented here since
there's no single official crosswalk from this specific 79-category
legend to the legal artificialisation nomenclature — this is a
judgment call modeled closely on the decret n. 2022-767 definition, not
a certified reproduction of it):

- Built/sealed (artificialized): all housing (28-35), all economic/
  industrial/utility land (36-54), covered or built sports facilities
  (55-59), all institutional equipment (60-72), all transport
  infrastructure and construction sites (73-79), plus open-air tennis
  courts (18, hard-surfaced) and esplanades/squares (24, paved).
- Not artificialized: forests/natural/agricultural land (1-12), parks,
  gardens and other green/grassed spaces (13-17, 26), water-adjacent
  and leisure-with-vegetation categories (19-23), cemeteries (25 — per
  the official nomenclature's own carve-out) and vacant land reverted
  to vegetation (27).

Only artificialized-category polygons are actually downloaded (the
`where` filter combines the department range with the category list),
since the area share is all that's needed here, not a full land-use
breakdown.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd

import config
from utils.geo import area_share_per_iris, load_iris_reference
from utils.io import save_geojson
from utils.opendatasoft import export_dataset

RAW_PATH = config.DATA_RAW / "artificialization_mos" / "artificialization_mos_raw.geojson"

ARTIFICIALIZED_MOS_CODES = [18, 24] + list(range(28, 80))


def dept_range_clause() -> str:
    ranges = {"75": (75000, 75999), "92": (92000, 92999), "93": (93000, 93999), "94": (94000, 94999)}
    clauses = [f"(insee >= {lo} and insee <= {hi})" for lo, hi in (ranges[d] for d in config.MGP_DEP_CODES)]
    return " or ".join(clauses)


def download() -> Path:
    codes = ",".join(str(c) for c in ARTIFICIALIZED_MOS_CODES)
    where = f"({dept_range_clause()}) and mos2021 in ({codes})"
    return export_dataset(
        base_url=config.IDF_OPENDATASOFT_BASE,
        dataset_id=config.MOS_DATASET_ID,
        dest_path=RAW_PATH,
        fmt="geojson",
        where=where,
    )


def normalize(raw_path: Path) -> gpd.GeoDataFrame:
    polygons = gpd.read_file(raw_path)
    iris = load_iris_reference(config.IRIS_REFERENCE_PATH, config.CRS_PROJECTED)

    shares = area_share_per_iris(polygons, iris, config.IRIS_JOIN_COLUMN, out_col="pct_artificialized")
    result = iris[[config.IRIS_JOIN_COLUMN, "geometry"]].merge(shares, on=config.IRIS_JOIN_COLUMN, how="left")
    # Overlay area sums can overshoot 1.0 by a hair (floating-point
    # precision on adjacent polygon boundaries) — clip rather than let a
    # "100.0000000002%" artifact show up anywhere downstream.
    result["pct_artificialized"] = result["pct_artificialized"].fillna(0).clip(upper=1.0)

    return result.to_crs(config.CRS_LATLON)


def main():
    raw_path = download()
    result = normalize(raw_path)
    save_geojson(result, config.DATA_PROCESSED / "artificialization_iris.geojson", required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
