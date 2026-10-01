"""Generic HTTP download helpers with retry and caching by presence."""
from pathlib import Path
from urllib.parse import quote
import re
import time
import zipfile

import requests

DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3
# Waits before retries 2, 3...: a transient DNS or gateway failure on a CI
# runner (seen 2026-10-01: "Temporary failure in name resolution" for
# data.education.gouv.fr) doesn't clear in milliseconds.
RETRY_BACKOFF_SECONDS = (5, 20, 60)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def get_with_retry(url: str, **kwargs) -> requests.Response:
    """requests.get with retries on network errors, timeouts and transient
    HTTP statuses (429, 5xx). Other 4xx are real errors and raise at once."""
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    last_error = None
    for attempt in range(DEFAULT_RETRIES):
        if attempt:
            time.sleep(RETRY_BACKOFF_SECONDS[min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)])
        try:
            response = requests.get(url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
            continue
        if response.status_code in RETRYABLE_STATUS:
            last_error = requests.HTTPError(f"{response.status_code} for {response.url}", response=response)
            continue
        response.raise_for_status()
        return response
    raise RuntimeError(f"GET {url} failed after {DEFAULT_RETRIES} attempts: {last_error}")


def download_file(url: str, dest_path: Path, force: bool = False, encode_path: bool = False) -> Path:
    """Download a file to dest_path, skipping if it already exists.

    encode_path percent-encodes the URL path segment only (not the query
    string), needed for sources like bruitparif.fr whose links contain
    literal spaces and accented characters.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and not force:
        return dest_path

    request_url = quote(url, safe=":/?&=%") if encode_path else url

    last_error = None
    for attempt in range(1, DEFAULT_RETRIES + 1):
        try:
            with requests.get(request_url, stream=True, timeout=DEFAULT_TIMEOUT) as response:
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            return dest_path
        except requests.RequestException as exc:
            last_error = exc
            if attempt < DEFAULT_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS[min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)])
                continue
    raise RuntimeError(f"Failed to download {url} after {DEFAULT_RETRIES} attempts: {last_error}")


def extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    return dest_dir


def find_extracted_file(extract_dir: Path, name_pattern: str, what: str) -> Path:
    """The single file under extract_dir (searched recursively) whose name
    fully matches name_pattern, case-insensitively.

    Case-insensitive because publishers don't keep extensions stable: INSEE
    ships "base-ic-evol-struct-pop-2021.CSV" — a `rglob("*.csv")` finds it
    on Windows/macOS (case-insensitive filesystems) but not on Linux, which
    is exactly how the quarterly workflow broke on 2026-10-01 while every
    local run passed. A precise name pattern rather than "the first CSV":
    INSEE zips also carry a "meta_….CSV" data dictionary, and directory
    order on Linux is arbitrary, so "first match" could silently load the
    dictionary instead of the data.

    Raises with the full list of files actually extracted when there isn't
    exactly one match, so a renamed upstream file is diagnosed from the
    workflow log alone.
    """
    regex = re.compile(name_pattern, re.IGNORECASE)
    files = sorted(p for p in Path(extract_dir).rglob("*") if p.is_file())
    matches = [p for p in files if regex.fullmatch(p.name)]
    if len(matches) == 1:
        return matches[0]
    listing = "\n".join(f"  - {p.relative_to(extract_dir)}" for p in files) or "  (no files at all)"
    problem = "no file" if not matches else f"{len(matches)} files"
    raise RuntimeError(
        f"{what}: {problem} under {extract_dir} match /{name_pattern}/ (case-insensitive). "
        f"Files found:\n{listing}"
    )


DATAGOUV_API = "https://www.data.gouv.fr/api/1/datasets"


def find_datagouv_resource(dataset_slug: str, title_pattern: str) -> str:
    """Current download URL of a data.gouv.fr resource, looked up by its
    title (full match, case-insensitive) through the dataset API.

    Never hardcode a static.data.gouv.fr URL: it embeds the upload
    timestamp (".../20260710-231714/acceslibre.csv") and returns 404 as
    soon as the publisher replaces the file — which broke script 12 in a
    cold run on 2026-10-01 while the July file cached locally hid it. When
    several resources match, the most recently modified one wins.
    """
    response = requests.get(f"{DATAGOUV_API}/{dataset_slug}/", timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    resources = response.json().get("resources", [])
    regex = re.compile(title_pattern, re.IGNORECASE)
    matches = [r for r in resources if regex.fullmatch(r.get("title", ""))]
    if not matches:
        titles = "\n".join(f"  - {r.get('title')}" for r in resources) or "  (no resources)"
        raise RuntimeError(
            f"No resource of data.gouv.fr dataset '{dataset_slug}' matches /{title_pattern}/. "
            f"Resources found:\n{titles}"
        )
    latest = max(matches, key=lambda r: r.get("last_modified") or "")
    return latest["url"]


def find_download_link(page_url: str, filename_pattern: str) -> str:
    """Scrape a plain HTML page for the first href matching filename_pattern.

    Used for sources (e.g. INSEE statistics pages) that only expose a
    human-facing download page rather than a stable direct file URL.
    """
    response = requests.get(page_url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    matches = re.findall(r'href="([^"]+)"', response.text)
    for href in matches:
        if re.search(filename_pattern, href, re.IGNORECASE):
            if href.startswith("http"):
                return href
            return requests.compat.urljoin(page_url, href)
    raise RuntimeError(f"No link matching '{filename_pattern}' found on {page_url}")


def fetch_datagouv_resource_urls(dataset_slug: str) -> list[dict]:
    """Return the list of resources (title, format, url) for a data.gouv.fr dataset.

    Resolving resources through the API instead of hardcoding a /r/<uuid>
    link keeps the script working after the dataset owner replaces a file.
    """
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_slug}/"
    response = requests.get(api_url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return [
        {"title": r.get("title"), "format": r.get("format"), "url": r.get("url")}
        for r in payload.get("resources", [])
    ]
