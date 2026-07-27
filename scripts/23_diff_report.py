"""Compare a freshly computed score output against the currently
published baseline, and decide whether the change is small enough to
publish automatically.

Standalone rather than folded into 11_compute_vulnerability_score.py:
this script's job is "is this new run safe to publish," which needs to
run *after* the score is computed and needs its own pass/fail exit code
for scripts/CI to branch on — mixing that into the scoring script itself
would make a routine re-score also responsible for a publishing
decision it has no context to make (it doesn't know what's currently
live in frontend/public/data).

This mirrors, in an automated form, the manual audits already done twice
in this project's history for access_time and cool_facility_deficit
(see SCORING.md): a distribution shift this large has, in both prior
cases, turned out to be a real bug rather than a real change in the
world. A quarterly automated re-run has no human in the loop to catch
that the way those two were caught, so a large shift here must stop and
ask for one instead of publishing on its own.
"""
import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd

SCORE_COL = "cumulative_vulnerability_score"
SCORE_CATEGORIES = [0, 1, 2, 3, 4]
# Score >= 3 is the metric already tracked by hand throughout this
# project's docs (SCORING.md's "Current distribution") — note this is
# NOT the same count as the public /ranking page, which lists only
# score == 3 (58 IRIS) and excludes the 4 already at 4/4 by design (that
# sample is still too small and recent for a public ranking — see
# SCORING.md). This script tracks >=3 (62 IRIS) because a score-4 IRIS's
# existence is itself part of what a large shift would reveal.
PUBLIC_THRESHOLD_SCORE = 3

# The turnover threshold the user picked as a starting point ("par
# exemple >15%") — how much of the current score->=3 population may
# enter/exit before this counts as a large-enough shift to require
# manual review. Deliberately a named constant, not a magic number
# buried in the CLI default, so a future adjustment has one obvious
# place to change and reason about.
DEFAULT_TURNOVER_THRESHOLD_PCT = 15.0
# Secondary check: the categories 0-4 breakdown shouldn't swing hard
# even if the >=3 turnover looks fine (e.g. a systematic re-standardization
# could move many IRIS between 1 and 2 without touching the >=3 boundary
# at all) — flagged if any single category's share of the total moves by
# more than this many percentage points.
DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP = 5.0


def load_scores(path: Path) -> dict[str, int]:
    gdf = gpd.read_file(path)
    return {
        row["code_iris"]: int(row[SCORE_COL])
        for _, row in gdf.iterrows()
        if row[SCORE_COL] is not None
    }


def category_shares(scores: dict[str, int]) -> dict[int, float]:
    total = len(scores) or 1
    counts = {c: 0 for c in SCORE_CATEGORIES}
    for v in scores.values():
        counts[v] = counts.get(v, 0) + 1
    return {c: 100.0 * n / total for c, n in counts.items()}


def build_report(baseline: dict[str, int], new: dict[str, int]) -> dict:
    baseline_high = {k for k, v in baseline.items() if v >= PUBLIC_THRESHOLD_SCORE}
    new_high = {k for k, v in new.items() if v >= PUBLIC_THRESHOLD_SCORE}
    entered = sorted(new_high - baseline_high)
    left = sorted(baseline_high - new_high)
    turnover_pct = 100.0 * (len(entered) + len(left)) / max(len(baseline_high), 1)

    baseline_shares = category_shares(baseline)
    new_shares = category_shares(new)
    max_category_shift_pp = max(
        abs(new_shares[c] - baseline_shares.get(c, 0.0)) for c in SCORE_CATEGORIES
    )

    common = set(baseline) & set(new)
    changed_score = sum(1 for k in common if baseline[k] != new[k])

    return {
        "baseline_iris_count": len(baseline),
        "new_iris_count": len(new),
        "baseline_high_count": len(baseline_high),
        "new_high_count": len(new_high),
        "entered_high": entered,
        "left_high": left,
        "turnover_pct": round(turnover_pct, 2),
        "baseline_category_shares": {c: round(v, 2) for c, v in baseline_shares.items()},
        "new_category_shares": {c: round(v, 2) for c, v in new_shares.items()},
        "max_category_shift_pp": round(max_category_shift_pp, 2),
        "iris_with_changed_score": changed_score,
    }


def verdict(report: dict, turnover_threshold: float, category_shift_threshold: float) -> bool:
    """True if the change is small enough to publish automatically."""
    return (
        report["turnover_pct"] <= turnover_threshold
        and report["max_category_shift_pp"] <= category_shift_threshold
    )


def render_markdown(report: dict, ok: bool, turnover_threshold: float, category_shift_threshold: float) -> str:
    lines = [
        "# Pipeline update — distribution diff report",
        "",
        f"**Verdict: {'within normal range, safe to auto-publish' if ok else 'LARGE SHIFT — needs manual review before publishing'}**",
        "",
        f"- IRIS count: {report['baseline_iris_count']} (baseline) -> {report['new_iris_count']} (new)",
        f"- Score >= {PUBLIC_THRESHOLD_SCORE} (tracked distribution metric, not the "
        f"/ranking page's own count — see SCORING.md): "
        f"{report['baseline_high_count']} -> {report['new_high_count']}",
        f"- Entered score >= {PUBLIC_THRESHOLD_SCORE}: {len(report['entered_high'])}",
        f"- Left score >= {PUBLIC_THRESHOLD_SCORE}: {len(report['left_high'])}",
        f"- Turnover on score >= {PUBLIC_THRESHOLD_SCORE}: **{report['turnover_pct']}%** "
        f"(threshold: {turnover_threshold}%)",
        f"- Largest single-category share shift (0-4 breakdown): "
        f"**{report['max_category_shift_pp']} pp** (threshold: {category_shift_threshold} pp)",
        f"- IRIS whose score category changed at all (any category, not just >=3): "
        f"{report['iris_with_changed_score']}",
        "",
        "## Category breakdown (share of all IRIS)",
        "",
        "| Score | Baseline | New |",
        "|---|---|---|",
    ]
    for c in SCORE_CATEGORIES:
        lines.append(
            f"| {c} | {report['baseline_category_shares'].get(c, 0)}% | {report['new_category_shares'].get(c, 0)}% |"
        )
    if report["entered_high"]:
        lines += ["", f"## Entered score >= {PUBLIC_THRESHOLD_SCORE} ({len(report['entered_high'])})", ""]
        lines += [f"- {code}" for code in report["entered_high"][:50]]
        if len(report["entered_high"]) > 50:
            lines.append(f"- ... and {len(report['entered_high']) - 50} more")
    if report["left_high"]:
        lines += ["", f"## Left score >= {PUBLIC_THRESHOLD_SCORE} ({len(report['left_high'])})", ""]
        lines += [f"- {code}" for code in report["left_high"][:50]]
        if len(report["left_high"]) > 50:
            lines.append(f"- ... and {len(report['left_high']) - 50} more")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True, help="Currently published GeoJSON")
    parser.add_argument("--new", type=Path, required=True, help="Freshly computed GeoJSON")
    parser.add_argument("--markdown-out", type=Path, default=None, help="Where to write the markdown report")
    parser.add_argument("--json-out", type=Path, default=None, help="Where to write the machine-readable summary")
    parser.add_argument("--turnover-threshold", type=float, default=DEFAULT_TURNOVER_THRESHOLD_PCT)
    parser.add_argument("--category-shift-threshold", type=float, default=DEFAULT_CATEGORY_SHIFT_THRESHOLD_PP)
    args = parser.parse_args()

    baseline = load_scores(args.baseline)
    new = load_scores(args.new)
    report = build_report(baseline, new)
    ok = verdict(report, args.turnover_threshold, args.category_shift_threshold)
    markdown = render_markdown(report, ok, args.turnover_threshold, args.category_shift_threshold)

    print(markdown)

    if args.markdown_out:
        args.markdown_out.write_text(markdown, encoding="utf-8")
    if args.json_out:
        args.json_out.write_text(json.dumps({**report, "ok": ok}, indent=2), encoding="utf-8")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
