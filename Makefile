PYTHON ?= python

ifeq ($(OS),Windows_NT)
    VENV_PYTHON := .venv/Scripts/python.exe
else
    VENV_PYTHON := .venv/bin/python
endif

.PHONY: venv install run run-% test clean docker-build docker-run

venv:
	$(PYTHON) -m venv .venv

install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

run: install
	$(VENV_PYTHON) scripts/run_all.py

# Run a single script, e.g. `make run-01_iris_contours`
run-%: install
	$(VENV_PYTHON) scripts/$*.py

test: install
	$(VENV_PYTHON) -m pytest tests/ -v

clean:
	rm -rf .venv
	find data/raw -mindepth 2 -type f ! -name '.gitkeep' -delete
	find data/interim -type f ! -name '.gitkeep' -delete
	find data/processed -type f -name '*.geojson' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +

docker-build:
	docker build -t underlaid-data .

docker-run: docker-build
	docker run --rm -v "$(CURDIR)/data:/app/data" underlaid-data
