"""Step 3 check: extreme IRIS of the access indicators on IGN aerial imagery.

For each IRIS: the IGN orthophoto (Géoplateforme WMS), the IRIS outline,
GP sites (sized by capacity) and pharmacies within the frame, and the 10-
and 20-minute walking radius (straight line at 4.5 km/h) from the IRIS
centre as a visual scale. One PNG per IRIS in data/interim/analysis/.

Usage: python scripts/analysis/access_extremes_imagery.py CODE_IRIS [...]
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import geopandas as gpd
import matplotlib
import requests
from PIL import Image

import config

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

WMS = "https://data.geopf.fr/wms-r/wms"
OUT_DIR = config.DATA_INTERIM / "analysis"
WALK_M_PER_MIN = 4500 / 60


def orthophoto(bounds, width=1000):
    minx, miny, maxx, maxy = bounds
    height = int(width * (maxy - miny) / (maxx - minx))
    r = requests.get(WMS, timeout=120, params={
        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": "ORTHOIMAGERY.ORTHOPHOTOS",
        "STYLES": "", "CRS": "EPSG:2154", "BBOX": f"{minx},{miny},{maxx},{maxy}",
        "WIDTH": width, "HEIGHT": height, "FORMAT": "image/jpeg",
    })
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content))


def main(codes):
    iris = gpd.read_file(config.IRIS_REFERENCE_PATH).to_crs(config.CRS_PROJECTED)
    gp = gpd.read_file(config.DATA_PROCESSED / "access" / "gp_sites_idf.geojson").to_crs(config.CRS_PROJECTED)
    gp = gp[gp.capacity > 0]
    ph = gpd.read_file(config.DATA_PROCESSED / "access" / "pharmacy_sites_idf.geojson").to_crs(config.CRS_PROJECTED)
    for code in codes:
        poly = iris[iris.code_iris == code]
        centre = poly.geometry.iloc[0].representative_point()
        half = 20 * WALK_M_PER_MIN + 100
        bounds = (centre.x - half, centre.y - half, centre.x + half, centre.y + half)
        img = orthophoto(bounds)
        fig, ax = plt.subplots(figsize=(9, 9))
        ax.imshow(img, extent=(bounds[0], bounds[2], bounds[1], bounds[3]))
        poly.boundary.plot(ax=ax, color="yellow", linewidth=2)
        for minutes in (10, 20):
            gpd.GeoSeries([centre.buffer(minutes * WALK_M_PER_MIN)], crs=poly.crs).boundary.plot(ax=ax, color="white", linewidth=0.8, linestyle="--")
        g = gp.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
        p = ph.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
        g.plot(ax=ax, color="red", markersize=20 + 25 * g.capacity, edgecolor="white", label=f"GP sites ({g.capacity.sum():.0f} GPs)")
        p.plot(ax=ax, color="lime", marker="P", markersize=60, edgecolor="black", label=f"pharmacies ({len(p)})")
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.set_axis_off()
        ax.legend(loc="lower left", fontsize=9)
        ax.set_title(f"{poly.nom_com.iloc[0]} — {poly.nom_iris.iloc[0]} ({code})\n"
                     "dashed: 10 and 20 min walk as the crow flies", fontsize=10)
        out = OUT_DIR / f"extreme_{code}.png"
        fig.savefig(out, dpi=90, bbox_inches="tight")
        plt.close(fig)
        print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
