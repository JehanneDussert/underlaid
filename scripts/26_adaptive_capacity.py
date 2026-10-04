"""Adaptive-capacity index and the exposure x capacity bivariate class.

Phase 8. Deliberately a SEPARATE axis, written to a SEPARATE file
(adaptive_capacity_iris.json) — never merged into the cumulative exposure
score, which stays a pure count of worst-quartile exposure categories
(see SCORING.md, "Adaptive capacity"). Crossing the two is what answers
"are we really equal in the face of heat?" without making the exposure
score itself harder to read or defend: two neighborhoods with the same
exposure can have very different means to cope with it.

Index = mean of the percentile ranks (0-1, higher = more capacity) of
three indicators, all INSEE, all at IRIS level (income: Filosofi 2021;
housing: 2022 census):
  - median disposable income (Filosofi) — financial means;
  - housing overcrowding rate (RP logement), reversed — room to get away
    from the heat inside one's own home;
  - secondary-residence rate (RP logement) — the option of leaving
    during a heatwave.
Percentile ranks rather than raw values or z-scores: overcrowding and
secondary residences are both heavily skewed (skew 1.7 and 4.1, max
|z| 11 and 14 on the 2,752 IRIS), the same sparse-data pattern that
distorted access_time and cool_facility_deficit before — ranks make a
single extreme value unable to drag the index.

Computed only where median income is known (the anchor indicator) and at
least 2 of the 3 indicators are present. INSEE masks income for small
IRIS (statistical secrecy); those IRIS get no index and no bivariate
class (np.nan / null), shown as "masked" on the map — never imputed.
This also drops the non-standard IRIS (worker hostels, business parks)
that produce the extreme overcrowding rates, since INSEE masks their
income too.

Candidates measured and rejected (see SCORING.md): poverty rate
(Spearman -0.91 with median income, masked on the same IRIS — a
duplicate that would double-weight income), social-housing share
(ambiguous: the landlord can act on the building), households without a
car (an urban lifestyle in Paris, not a lack of means).

Bivariate class: exposure in 3 classes — 0, 1, 2+ (score 3 and 4 are
only 2.2% of IRIS together, too few for a class of their own) — crossed
with capacity tertiles computed over the IRIS that have an index.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd

import config

# (column, True if a higher value means MORE capacity)
CAPACITY_INDICATORS = [
    ("median_income", True),
    ("pct_overcrowded", False),
    ("pct_secondary_residences", True),
]
ANCHOR_INDICATOR = "median_income"
MIN_INDICATORS = 2

EXPOSURE_CLASS_BINS = [-1, 0, 1, 4]  # -> 0, 1, 2 (meaning "2 or more")
CAPACITY_CLASSES = 3

OUTPUT_PATH = config.DATA_PROCESSED / "adaptive_capacity_iris.json"


def percentile_rank(series: pd.Series, higher_is_more_capacity: bool) -> pd.Series:
    ranks = (series if higher_is_more_capacity else -series).rank(pct=True, method="average")
    return ranks.where(series.notna())


def compute(df: pd.DataFrame) -> tuple[pd.DataFrame, list[float]]:
    ranks = pd.concat(
        [percentile_rank(df[col], higher) for col, higher in CAPACITY_INDICATORS], axis=1
    )
    has_index = df[ANCHOR_INDICATOR].notna() & (ranks.notna().sum(axis=1) >= MIN_INDICATORS)
    df = df.copy()
    df["capacity_index"] = ranks.mean(axis=1).where(has_index)

    classes, cutoffs = pd.qcut(df["capacity_index"], CAPACITY_CLASSES, labels=False, retbins=True)
    df["capacity_class"] = classes  # 0 = lowest third, 2 = highest; NaN where masked

    score = df["cumulative_vulnerability_score"]
    df["exposure_class"] = pd.cut(score, EXPOSURE_CLASS_BINS, labels=False)
    df.loc[score.isna(), "exposure_class"] = np.nan
    return df, [float(c) for c in cutoffs]


def main():
    score = gpd.read_file(config.DATA_PROCESSED / "vulnerability_score_iris.geojson")
    overcrowding = gpd.read_file(config.DATA_PROCESSED / "overcrowding_iris.geojson")
    df = pd.DataFrame(score.drop(columns="geometry")).merge(
        pd.DataFrame(overcrowding[[config.IRIS_JOIN_COLUMN, "pct_overcrowded"]]),
        on=config.IRIS_JOIN_COLUMN,
        how="left",
    )
    df, cutoffs = compute(df)

    def clean(value, digits=None):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        return round(float(value), digits) if digits is not None else int(value)

    records = [
        {
            "code_iris": row.code_iris,
            "pct_overcrowded": clean(row.pct_overcrowded, 4),
            "capacity_index": clean(row.capacity_index, 4),
            "capacity_class": clean(row.capacity_class),
            "exposure_class": clean(row.exposure_class),
        }
        for row in df.itertuples()
    ]
    medians = {col: clean(df[col].median(), 4) for col, _ in CAPACITY_INDICATORS}
    payload = {
        "description": (
            "Adaptive-capacity index per IRIS (mean percentile rank of median income, "
            "reversed overcrowding rate, secondary-residence rate; INSEE Filosofi 2021 and 2022 census) and its "
            "tertile class, plus the exposure class (0, 1, 2+) of the cumulative exposure "
            "score. Separate axis: never part of the exposure score. See SCORING.md."
        ),
        "indicators": [col for col, _ in CAPACITY_INDICATORS],
        "capacity_tertile_cutoffs": [round(c, 4) for c in cutoffs],
        "mgp_medians": medians,
        "iris": records,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    with_index = df["capacity_index"].notna()
    print(f"Saved {len(records)} IRIS to {OUTPUT_PATH} — index for {with_index.sum()} "
          f"({100 * with_index.mean():.1f}%), masked {(~with_index).sum()}")
    grid = pd.crosstab(df["exposure_class"], df["capacity_class"])
    grid.index = ["exposure 0", "exposure 1", "exposure 2+"]
    grid.columns = ["capacity low", "capacity mid", "capacity high"]
    print(grid.to_string())
    print("Spearman(capacity index, exposure score) = %.3f"
          % df[["capacity_index", "cumulative_vulnerability_score"]].corr(method="spearman").iloc[0, 1])


if __name__ == "__main__":
    main()
