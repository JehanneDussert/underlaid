"""Unit tests for scripts/23_diff_report.py's comparison logic.

Uses synthetic code_iris -> score dicts rather than real GeoJSON files —
the thing worth testing here is the turnover/threshold arithmetic itself,
not the pipeline's actual output, which the rest of tests/ already covers.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
diff_report = importlib.import_module("23_diff_report")


def test_identical_distributions_have_zero_turnover():
    scores = {f"iris_{i}": i % 5 for i in range(100)}
    report = diff_report.build_report(scores, scores)
    assert report["turnover_pct"] == 0.0
    assert report["max_category_shift_pp"] == 0.0
    assert diff_report.verdict(report, 15.0, 5.0) is True


def test_small_shift_passes_default_thresholds():
    baseline = {f"iris_{i}": 3 for i in range(20)}
    baseline.update({f"iris_{i}": 0 for i in range(20, 100)})
    new = dict(baseline)
    # Move 2 of the 20 score->=3 IRIS down to 0 — 10% turnover on a
    # baseline of 20, well under the 15% default threshold.
    new["iris_0"] = 0
    new["iris_1"] = 0
    report = diff_report.build_report(baseline, new)
    assert report["turnover_pct"] == 10.0
    assert diff_report.verdict(report, diff_report.DEFAULT_TURNOVER_THRESHOLD_PCT, diff_report.DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP) is True


def test_large_turnover_fails_verdict():
    baseline = {f"iris_{i}": 3 for i in range(20)}
    baseline.update({f"iris_{i}": 0 for i in range(20, 100)})
    new = dict(baseline)
    # Drop 6 of the 20 score->=3 IRIS to 0 -- 30% turnover, over the 15% default.
    for i in range(6):
        new[f"iris_{i}"] = 0
    report = diff_report.build_report(baseline, new)
    assert report["turnover_pct"] == 30.0
    assert diff_report.verdict(report, diff_report.DEFAULT_TURNOVER_THRESHOLD_PCT, diff_report.DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP) is False


def test_category_shift_alone_can_fail_verdict_even_with_no_turnover():
    # No IRIS crosses the >=3 boundary, but a systematic shift moves many
    # IRIS between categories 1 and 2 -- should still be caught.
    baseline = {}
    for i in range(50):
        baseline[f"a_{i}"] = 1
    for i in range(50):
        baseline[f"b_{i}"] = 2
    new = dict(baseline)
    for i in range(40):
        new[f"a_{i}"] = 2
    report = diff_report.build_report(baseline, new)
    assert report["turnover_pct"] == 0.0
    assert report["max_category_shift_pp"] > diff_report.DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP
    assert diff_report.verdict(report, diff_report.DEFAULT_TURNOVER_THRESHOLD_PCT, diff_report.DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP) is False


def test_entered_and_left_lists_are_correct():
    baseline = {"a": 3, "b": 3, "c": 0}
    new = {"a": 3, "b": 0, "c": 3}
    report = diff_report.build_report(baseline, new)
    assert report["entered_high"] == ["c"]
    assert report["left_high"] == ["b"]
