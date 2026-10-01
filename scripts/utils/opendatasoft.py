"""Generic client for the Opendatasoft Explore API v2.1.

Shared by every portal built on Opendatasoft: opendata.paris.fr,
data.iledefrance.fr, data.education.gouv.fr and data.ademe.fr all expose
the same /api/explore/v2.1/catalog/datasets/{id}/... routes.
"""
from pathlib import Path

from .download import DEFAULT_TIMEOUT, get_with_retry

PAGE_SIZE = 100


def dept_where_clause(field: str, dep_codes: list[str]) -> str:
    """Build an Opendatasoft `where` clause matching any of `dep_codes` as

    a prefix of `field` (a commune code). Unlike Paris, where a single
    3-digit prefix ("751") covers every arrondissement, the 4 MGP
    departments don't share a common prefix, so this needs an OR of one
    `startswith()` per department rather than a single prefix check.
    """
    return " or ".join(f'startswith({field}, "{d}")' for d in dep_codes)


def export_dataset(base_url: str, dataset_id: str, dest_path: Path, fmt: str = "geojson", where: str | None = None) -> Path:
    """Download a full dataset export (no pagination needed for exports)."""
    url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/{fmt}"
    params = {"where": where} if where else {}
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    response = get_with_retry(url, params=params, timeout=DEFAULT_TIMEOUT)
    dest_path.write_bytes(response.content)
    return dest_path


def query_records(
    base_url: str,
    dataset_id: str,
    where: str | None = None,
    select: str | None = None,
    group_by: str | None = None,
) -> list[dict]:
    """Fetch all records via the paginated /records route, for datasets

    too large to export in one call or when only specific fields are needed.

    `group_by` lets `select` include Opendatasoft's server-side aggregation
    functions (avg(), count(...), etc.) so a coarse-grain summary (e.g. one
    row per arrondissement) can be pulled without downloading every raw row
    first — used by script 18 to avoid fetching all ~219k tree records just
    to average one field per arrondissement.
    """
    url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
    records = []
    offset = 0
    while True:
        params = {"limit": PAGE_SIZE, "offset": offset}
        if where:
            params["where"] = where
        if select:
            params["select"] = select
        if group_by:
            params["group_by"] = group_by
        response = get_with_retry(url, params=params, timeout=DEFAULT_TIMEOUT)
        payload = response.json()
        batch = payload.get("results", [])
        records.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return records
