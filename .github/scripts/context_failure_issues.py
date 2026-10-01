"""Open (or comment on) one GitHub issue per context layer that run_all.py
kept from a previous run — see scripts/pipeline_policy.py.

Reads data/processed/run_report.json; needs the `gh` CLI with GH_TOKEN
(available on GitHub-hosted runners) and the workflow's `issues: write`
permission. RUN_URL is the link to the workflow run, for the issue body.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPORT = Path("data/processed/run_report.json")


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()


def body_for(failure: dict, run_url: str) -> str:
    kept = "\n".join(f"- `{name}`: kept from {date}" for name, date in failure["layers_kept"].items())
    return (
        f"`{failure['script']}` failed (exit code {failure['exit_code']}) in [this run]({run_url}).\n\n"
        "It is a context-only layer (not scored), so the pipeline went on: the previous version "
        "was kept and the site shows it with its own date.\n\n"
        f"{kept}\n\n"
        "It will block the pipeline once it is more than two quarters old.\n\n"
        f"Last lines of its log:\n\n```\n{failure['log_tail'].strip()}\n```"
    )


def main() -> int:
    if not REPORT.exists():
        print("No run report — nothing to do.")
        return 0
    failures = json.loads(REPORT.read_text(encoding="utf-8")).get("context_failures", [])
    run_url = os.environ.get("RUN_URL", "")
    for failure in failures:
        title = f"[pipeline] Context layer failed: {failure['script']}"
        body = body_for(failure, run_url)
        existing = gh("issue", "list", "--state", "open", "--search", f'in:title "{title}"', "--json", "number,title")
        matches = [i["number"] for i in json.loads(existing or "[]") if i["title"] == title]
        if matches:
            gh("issue", "comment", str(matches[0]), "--body", body)
            print(f"Commented on #{matches[0]}: {title}")
        else:
            print(gh("issue", "create", "--title", title, "--body", body))
    print(f"{len(failures)} context failure(s) reported.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
