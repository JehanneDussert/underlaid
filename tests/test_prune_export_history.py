"""Unit tests for scripts/prune_export_history.py's retention logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import prune_export_history as mod


def make_dated_dirs(base: Path, names: list[str]) -> None:
    for name in names:
        (base / name).mkdir(parents=True)


def test_prune_keeps_only_the_most_recent_n(tmp_path):
    history = tmp_path / "history"
    make_dated_dirs(history, ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01"])

    removed = mod.prune(history, keep=4)

    remaining = sorted(p.name for p in history.iterdir())
    assert remaining == ["2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01"]
    assert [p.name for p in removed] == ["2026-01-01"]


def test_prune_no_op_when_under_the_limit(tmp_path):
    history = tmp_path / "history"
    make_dated_dirs(history, ["2026-01-01", "2026-02-01"])

    removed = mod.prune(history, keep=4)

    assert removed == []
    assert sorted(p.name for p in history.iterdir()) == ["2026-01-01", "2026-02-01"]


def test_prune_missing_history_dir_is_a_no_op(tmp_path):
    history = tmp_path / "does-not-exist"
    assert mod.prune(history, keep=4) == []


def test_snapshot_copies_expected_files_into_a_dated_folder(tmp_path):
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "vulnerability_score_iris.geojson").write_text("{}", encoding="utf-8")
    (processed / "last_updated.json").write_text("{}", encoding="utf-8")
    (processed / "some_other_layer.geojson").write_text("{}", encoding="utf-8")
    history = tmp_path / "history"

    dest = mod.snapshot(processed, history)

    assert (dest / "vulnerability_score_iris.geojson").exists()
    assert (dest / "last_updated.json").exists()
    assert not (dest / "some_other_layer.geojson").exists()
