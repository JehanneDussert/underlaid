"""Download and normalize IRIS boundaries for the Metropole du Grand Paris
(Petite Couronne: Paris + Hauts-de-Seine + Seine-Saint-Denis + Val-de-Marne).

Source: data.iledefrance.fr, dataset "iris" (Opendatasoft Explore API v2.1).
This is the IGN & INSEE "Contours IRIS" 2024 edition republished by the
Ile-de-France regional portal (confirmed via the dataset's own metadata:
publisher=IGN & INSEE, references=geoservices.ign.fr/contoursiris), used
here as the single geometric reference all other scripts join against.
Confirmed via direct query: 2,752 IRIS across the 4 departments (992 in
75, 616 in 92, 614 in 93, 530 in 94).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from utils.io import save_geojson
from utils.opendatasoft import export_dataset

RAW_PATH = config.DATA_RAW / "iris" / "iris_mgp_raw.geojson"


def download() -> Path:
    dep_list = ",".join(f'"{d}"' for d in config.MGP_DEP_CODES)
    return export_dataset(
        base_url=config.IDF_OPENDATASOFT_BASE,
        dataset_id=config.IRIS_DATASET_ID,
        dest_path=RAW_PATH,
        fmt="geojson",
        where=f"dep in ({dep_list})",
    )


def normalize(raw_path: Path):
    import geopandas as gpd

    gdf = gpd.read_file(raw_path)
    gdf = gdf.rename(columns={"code_iris": config.IRIS_JOIN_COLUMN})
    gdf = gdf[[config.IRIS_JOIN_COLUMN, "nom_iris", "insee_com", "nom_com", "typ_iris", "geometry"]]
    gdf = gdf.to_crs(config.CRS_LATLON)
    return gdf


def main():
    raw_path = download()
    gdf = normalize(raw_path)
    save_geojson(gdf, config.IRIS_REFERENCE_PATH, required_cols=[config.IRIS_JOIN_COLUMN, "geometry"])


if __name__ == "__main__":
    main()
