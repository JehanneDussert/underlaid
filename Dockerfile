FROM python:3.12-slim

# geopandas/fiona need GDAL at the OS level; pip alone can't provide it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
COPY tests/ tests/

VOLUME ["/app/data"]

CMD ["python", "scripts/run_all.py"]
