"""Batch geocoding against the Base Adresse Nationale (Géoplateforme CSV API).

Results are cached per unique (address, postcode, citycode) in a CSV, so
a re-run only sends addresses it hasn't seen. A result is kept with its
score and type: callers decide what quality to accept, and report it.
"""
import io
from pathlib import Path

import pandas as pd
import requests

from .download import RETRY_BACKOFF_SECONDS, RETRYABLE_STATUS

GEOCODE_CSV_URL = "https://data.geopf.fr/geocodage/search/csv"
CHUNK_ROWS = 5000
KEY_COLS = ["address", "postcode", "citycode"]
RESULT_COLS = ["longitude", "latitude", "result_score", "result_type", "result_label", "result_citycode"]


def _post_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    import time

    body = chunk[KEY_COLS].to_csv(index=False).encode("utf-8")
    last_error = None
    for attempt, wait in enumerate((0, *RETRY_BACKOFF_SECONDS)):
        if wait:
            time.sleep(wait)
        try:
            r = requests.post(
                GEOCODE_CSV_URL,
                files={"data": ("chunk.csv", body, "text/csv")},
                data={"columns": "address", "postcode": "postcode", "citycode": "citycode"},
                timeout=600,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
            continue
        if r.status_code in RETRYABLE_STATUS:
            last_error = f"HTTP {r.status_code}"
            continue
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.content.decode("utf-8")), dtype=str)
    raise RuntimeError(f"Geocoding chunk failed after retries: {last_error}")


def geocode(df: pd.DataFrame, cache_path: Path) -> pd.DataFrame:
    """Return df with RESULT_COLS added (longitude/latitude/score as floats)."""
    keys = df[KEY_COLS].fillna("").astype(str).drop_duplicates()
    cache = pd.read_csv(cache_path, dtype=str).fillna("") if cache_path.exists() else pd.DataFrame(columns=KEY_COLS + RESULT_COLS)
    todo = keys.merge(cache[KEY_COLS], on=KEY_COLS, how="left", indicator=True)
    todo = todo[todo["_merge"] == "left_only"][KEY_COLS]
    if len(todo):
        results = [_post_chunk(todo.iloc[i:i + CHUNK_ROWS]) for i in range(0, len(todo), CHUNK_ROWS)]
        new = pd.concat(results, ignore_index=True).fillna("")
        new[KEY_COLS] = todo[KEY_COLS].values  # echo the exact keys sent
        cache = pd.concat([cache, new[KEY_COLS + RESULT_COLS]], ignore_index=True)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache.to_csv(cache_path, index=False)
    out = df.copy()
    out[KEY_COLS] = out[KEY_COLS].fillna("").astype(str)
    out = out.merge(cache[KEY_COLS + RESULT_COLS], on=KEY_COLS, how="left")
    for col in ("longitude", "latitude", "result_score"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out
