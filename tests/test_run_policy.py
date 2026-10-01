"""Failure policy of scripts/run_all.py (scripts/pipeline_policy.py).

Runs without network or pipeline data: the pipeline scripts are replaced
by fakes, and data/processed by a temporary directory.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pipeline_policy as policy
import run_all


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_every_script_has_a_family():
    assert set(run_all.SCRIPT_ORDER) == set(policy.SCRIPTS), "run_all.SCRIPT_ORDER and pipeline_policy.SCRIPTS disagree"
    assert {family for family, _ in policy.SCRIPTS.values()} <= {"reference", "score", "means", "context"}


def test_score_and_means_inputs_are_blocking():
    """The scored categories and the means axis must never mix runs."""
    for script in ["01_iris_contours.py", "05_air_noise.py", "11_compute_vulnerability_score.py",
                   "08_income_filosofi.py", "25_overcrowding.py", "26_adaptive_capacity.py"]:
        assert policy.SCRIPTS[script][0] in policy.BLOCKING_FAMILIES


def test_legacy_metadata_dates_every_layer_from_generated_at(tmp_path):
    path = tmp_path / "last_updated.json"
    path.write_text(json.dumps({"generated_at": "2026-07-26T20:15:50Z"}), encoding="utf-8")
    dates = policy.previous_layer_dates(path)
    assert dates["social_index_iris.geojson"] == "2026-07-26T20:15:50Z"


def test_two_quarter_cap():
    now = datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert not policy.too_old(iso(now - timedelta(days=90)), now)
    assert policy.too_old(iso(now - timedelta(days=200)), now)
    assert policy.too_old(None, now)


def test_schema_problem_detects_missing_file_and_columns(tmp_path):
    layer = policy.Layer("x_iris.geojson", ("code_iris", "value"))
    assert "no previous version" in policy.schema_problem(tmp_path / "x_iris.geojson", layer, None)
    (tmp_path / "x_iris.geojson").write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"code_iris": "751010101"}, "geometry": {"type": "Point", "coordinates": [2.3, 48.8]}}],
    }), encoding="utf-8")
    assert "lacks columns ['value']" in policy.schema_problem(tmp_path / "x_iris.geojson", layer, None)
    ok_layer = policy.Layer("x_iris.geojson", ("code_iris",))
    assert policy.schema_problem(tmp_path / "x_iris.geojson", ok_layer, {"751010101"}) is None
    assert "IRIS codes" in policy.schema_problem(tmp_path / "x_iris.geojson", ok_layer, {"751010101", "751010102"})


@pytest.fixture
def fake_pipeline(tmp_path, monkeypatch):
    """Two fake scripts: one blocking (score), one context. Their outputs are
    plain JSON files so the schema check doesn't need geopandas."""
    processed = tmp_path / "processed"
    processed.mkdir()
    monkeypatch.setattr(policy, "SCRIPTS", {
        "a_score.py": ("score", (policy.Layer("score.json", ()),)),
        "b_context.py": ("context", (policy.Layer("context.json", (), iris_grain=False),)),
    })
    monkeypatch.setattr(run_all, "SCRIPT_ORDER", ["a_score.py", "b_context.py"])
    monkeypatch.setattr(run_all.config, "DATA_PROCESSED", processed)
    monkeypatch.setattr(run_all, "METADATA_PATH", processed / "last_updated.json")
    monkeypatch.setattr(run_all, "REPORT_PATH", processed / "run_report.json")
    monkeypatch.setattr(run_all, "iris_codes", lambda: None)
    return processed


def set_outcomes(monkeypatch, processed, outcomes):
    def fake_run(script):
        code = outcomes[script]
        if code == 0:
            out = "score.json" if script == "a_score.py" else "context.json"
            (processed / out).write_text('{"fresh": true}', encoding="utf-8")
        else:
            (processed / "context.json").write_text("corrupted by a half-finished run", encoding="utf-8")
        return code, f"{script} log tail"
    monkeypatch.setattr(run_all, "run_script", fake_run)


def test_context_failure_keeps_previous_version_and_is_reported(fake_pipeline, monkeypatch):
    processed = fake_pipeline
    previous = iso(datetime.now(timezone.utc) - timedelta(days=60))
    (processed / "context.json").write_text('{"previous": true}', encoding="utf-8")
    (processed / "last_updated.json").write_text(json.dumps({"generated_at": previous, "layers": {"context.json": previous}}), encoding="utf-8")
    set_outcomes(monkeypatch, processed, {"a_score.py": 0, "b_context.py": 1})

    run_all.main()

    assert json.loads((processed / "context.json").read_text(encoding="utf-8")) == {"previous": True}, "previous version not restored"
    meta = json.loads((processed / "last_updated.json").read_text(encoding="utf-8"))
    assert meta["layers"]["context.json"] == previous, "kept layer must keep its original date"
    assert meta["layers"]["score.json"] == meta["generated_at"]
    report = json.loads((processed / "run_report.json").read_text(encoding="utf-8"))
    assert [f["script"] for f in report["context_failures"]] == ["b_context.py"]


def test_blocking_failure_stops_the_run(fake_pipeline, monkeypatch):
    set_outcomes(monkeypatch, fake_pipeline, {"a_score.py": 1, "b_context.py": 0})
    with pytest.raises(SystemExit):
        run_all.main()
    assert not (fake_pipeline / "last_updated.json").exists()


def test_context_layer_older_than_two_quarters_blocks(fake_pipeline, monkeypatch):
    processed = fake_pipeline
    old = iso(datetime.now(timezone.utc) - timedelta(days=200))
    (processed / "context.json").write_text('{"previous": true}', encoding="utf-8")
    (processed / "last_updated.json").write_text(json.dumps({"generated_at": old, "layers": {"context.json": old}}), encoding="utf-8")
    set_outcomes(monkeypatch, processed, {"a_score.py": 0, "b_context.py": 1})
    with pytest.raises(SystemExit):
        run_all.main()


def test_context_failure_without_previous_version_blocks(fake_pipeline, monkeypatch):
    set_outcomes(monkeypatch, fake_pipeline, {"a_score.py": 0, "b_context.py": 1})
    (fake_pipeline / "context.json").unlink(missing_ok=True)
    with pytest.raises(SystemExit):
        run_all.main()
