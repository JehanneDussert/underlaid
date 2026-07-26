"""Generic HTTP download helpers with retry and caching by presence."""
from pathlib import Path
from urllib.parse import quote
import re
import zipfile

import requests

DEFAULT_TIMEOUT = 60
DEFAULT_RETRIES = 3


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
                continue
    raise RuntimeError(f"Failed to download {url} after {DEFAULT_RETRIES} attempts: {last_error}")


def extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    return dest_dir


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
