"""Read/write helpers with light schema validation for processed outputs."""
from pathlib import Path

import geopandas as gpd


def save_geojson(gdf: gpd.GeoDataFrame, path: Path, required_cols: list[str] | None = None) -> None:
    if required_cols:
        missing = [c for c in required_cols if c not in gdf.columns]
        if missing:
            raise ValueError(f"Cannot save {path.name}: missing required columns {missing}")

    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")
    print(f"Saved {len(gdf)} features to {path}")


def read_geojson(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)
