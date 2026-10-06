"""Monthly watch of the sources the site depends on (GitHub Actions,
.github/workflows/sources-watch.yml). Prints one line per finding to
watch_findings.txt; the workflow opens an issue for each new finding.

Checks (state of the project on 6 October 2026):
- INSEE census at IRIS level: a "Population en <year>" release newer than
  2022 (the reference since 3 October 2026);
- INSEE Filosofi at IRIS level (income): a release newer than 2021;
- INSEE Filosofi 200 m grid: a release newer than 2021;
- INSEE BPE (equipment base): a release newer than 2025;
- RNA (associations): Paris missing from the regional extract, the kept
  version expires around 25 January 2027 (issue #2): reminder from
  10 January 2027.
INSEE titles are read from the insee.fr search service (JSON).
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

import requests

SEARCH = "https://www.insee.fr/fr/solr/consultation?q=*:*"
OUT = Path("watch_findings.txt")
CHECKS = [
    # (query, title regex with the year as group 1, newest year in use, label)
    ("Population en IRIS infracommunale", r"^Population en (\d{4})$", 2022, "Recensement à l'IRIS (population, logement)"),
    ("Revenus pauvreté niveau de vie Iris", r"^Revenus, pauvreté et niveau de vie en (\d{4}) \(Iris\)", 2021, "Filosofi à l'IRIS (revenu médian)"),
    ("Revenus pauvreté niveau de vie données carroyées", r"niveau de vie en (\d{4}).*[Cc]arroy", 2021, "Filosofi en carreaux de 200 m"),
    ("Équipements géolocalisés base permanente des équipements", r"^[ÉE]quipements géolocalisés .* en (\d{4})$", 2025, "Base permanente des équipements (BPE, équipements géolocalisés)"),
]
RNA_REMINDER_FROM = dt.date(2027, 1, 10)


def search(query: str) -> list[dict]:
    body = {"q": query, "start": 0, "sortFields": [{"field": "score", "order": "desc"}], "filters": [], "rows": 30, "facetsQuery": []}
    r = requests.post(SEARCH, json=body, timeout=60)
    r.raise_for_status()
    return r.json().get("documents", [])


def main():
    findings = []
    errors = []
    for query, pattern, in_use, label in CHECKS:
        try:
            docs = search(query)
        except Exception as e:  # report, do not fail the whole watch
            errors.append(f"{label} : recherche INSEE impossible ({e})")
            continue
        newer = []
        for d in docs:
            m = re.search(pattern, d.get("titre") or "")
            if m and int(m.group(1)) > in_use:
                newer.append(f"{d['titre']} (https://www.insee.fr/fr/statistiques/{d['id']}, diffusé le {(d.get('dateDiffusion') or '')[:10]})")
        if newer:
            findings.append(f"Nouvelle édition : {label} : " + " ; ".join(sorted(set(newer))))
    if dt.date.today() >= RNA_REMINDER_FROM:
        findings.append("Rappel RNA : la version gardée de l'extrait régional (sans Paris) arrive à échéance vers le 25/01/2027 ; vérifier la source ou basculer sur le RNA national (issue #2).")
    OUT.write_text("\n".join(findings + errors) + ("\n" if findings or errors else ""), encoding="utf-8")
    print("\n".join(findings + errors) or "Rien de nouveau.")


if __name__ == "__main__":
    sys.exit(main())
