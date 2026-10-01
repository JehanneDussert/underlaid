"""Unit tests for scripts/utils/download.py's extracted-file lookup.

Regression guard for the 2026-10-01 workflow failure: INSEE ships
"base-ic-evol-struct-pop-2021.CSV" (uppercase extension); `rglob("*.csv")`
found it on Windows but not on the Linux runner. Runs without any pipeline
output, unlike tests/test_pipeline.py.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from utils.download import find_extracted_file


def touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    return path


def test_uppercase_extension_is_found(tmp_path):
    data = touch(tmp_path / "base-ic-evol-struct-pop-2021.CSV")
    assert find_extracted_file(tmp_path, r"base-ic-evol-struct-pop-\d{4}\.csv", "population") == data


def test_meta_dictionary_is_never_picked(tmp_path):
    touch(tmp_path / "meta_base-ic-logement-2021.CSV")
    data = touch(tmp_path / "base-ic-logement-2021.CSV")
    assert find_extracted_file(tmp_path, r"base-ic-logement-\d{4}\.csv", "housing") == data


def test_search_is_recursive(tmp_path):
    layer = touch(tmp_path / "indicateurs_icu" / "indicateurs_icu.gpkg")
    touch(tmp_path / "indicateurs_icu" / "indicateurs_icu.qgz")
    assert find_extracted_file(tmp_path, r".+\.(gpkg|shp|geojson)", "heat layer") == layer


def test_no_match_lists_every_file_found(tmp_path):
    touch(tmp_path / "readme.txt")
    touch(tmp_path / "sub" / "other.CSV")
    with pytest.raises(RuntimeError) as err:
        find_extracted_file(tmp_path, r"BPE\d{2}\.csv", "BPE equipment file")
    message = str(err.value)
    assert "BPE equipment file: no file" in message
    assert "readme.txt" in message and "other.CSV" in message


def test_several_matches_are_an_error_not_a_guess(tmp_path):
    touch(tmp_path / "BPE24.csv")
    touch(tmp_path / "BPE25.csv")
    with pytest.raises(RuntimeError, match="2 files"):
        find_extracted_file(tmp_path, r"BPE\d{2}\.csv", "BPE equipment file")


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _fake_dataset(monkeypatch, resources):
    import utils.download as download

    monkeypatch.setattr(download.requests, "get", lambda url, timeout: _FakeResponse({"resources": resources}))
    return download.find_datagouv_resource


def test_datagouv_resource_takes_the_latest_matching_title(monkeypatch):
    find = _fake_dataset(monkeypatch, [
        {"title": "acceslibre.csv", "last_modified": "2026-07-10T23:17:14", "url": "https://x/20260710/acceslibre.csv"},
        {"title": "acceslibre-with-web-url.csv", "last_modified": "2026-09-30T23:20:46", "url": "https://x/web.csv"},
        {"title": "acceslibre.csv", "last_modified": "2026-09-30T23:20:10", "url": "https://x/20260930/acceslibre.csv"},
    ])
    assert find("slug", r"acceslibre\.csv") == "https://x/20260930/acceslibre.csv"


def test_datagouv_missing_resource_lists_available_titles(monkeypatch):
    find = _fake_dataset(monkeypatch, [{"title": "indicateurs-icu-v2.zip", "url": "https://x/v2.zip"}])
    with pytest.raises(RuntimeError) as err:
        find("slug", r"indicateurs-icu\.zip")
    assert "indicateurs-icu-v2.zip" in str(err.value)


class _Status:
    def __init__(self, code):
        self.status_code = code
        self.url = "https://example.test/x"

    def raise_for_status(self):
        import requests

        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)


def _fake_get(monkeypatch, outcomes):
    """outcomes: list of exceptions or status codes, consumed in order."""
    import utils.download as download

    calls = []

    def fake(url, **kwargs):
        outcome = outcomes[len(calls)]
        calls.append(url)
        if isinstance(outcome, Exception):
            raise outcome
        return _Status(outcome)

    monkeypatch.setattr(download.requests, "get", fake)
    monkeypatch.setattr(download.time, "sleep", lambda seconds: None)
    return download.get_with_retry, calls


def test_transient_dns_failure_is_retried(monkeypatch):
    import requests

    get, calls = _fake_get(monkeypatch, [requests.ConnectionError("Temporary failure in name resolution"), 200])
    assert get("https://data.education.gouv.fr/x").status_code == 200
    assert len(calls) == 2


def test_client_error_is_not_retried(monkeypatch):
    import requests

    get, calls = _fake_get(monkeypatch, [404, 200])
    with pytest.raises(requests.HTTPError):
        get("https://example.test/missing")
    assert len(calls) == 1


def test_persistent_gateway_error_gives_up(monkeypatch):
    get, calls = _fake_get(monkeypatch, [503, 503, 503])
    with pytest.raises(RuntimeError, match="after 3 attempts"):
        get("https://example.test/busy")
    assert len(calls) == 3
