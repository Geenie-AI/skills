#!/usr/bin/env python3
"""Build the scenario-eval summary table and, optionally, write it into a skill's README.

Usage:
  scripts/eval-report.py RESULTS_DIR [--skill NAME] [--readme README.md]
                         [--run-url URL] [--trigger EVENT] [--date YYYY-MM-DD]

RESULTS_DIR is searched recursively for results.json files produced by
scripts/run-scenario.sh. With --skill only that skill's rows are used. The
summary (Markdown) is printed to stdout; with --readme the block between the
markers below is replaced in that file (normally skills/<name>/README.md).
Exit status is 0 even when scenarios fail: the eval is non-blocking.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

START = "<!-- eval-results:start -->"
END = "<!-- eval-results:end -->"


def load_rows(results_dir: pathlib.Path, skill: str | None) -> list[dict]:
    rows = []
    for p in sorted(results_dir.rglob("results.json")):
        try:
            data = json.loads(p.read_text())
        except (OSError, ValueError) as exc:
            print(f"eval-report: skipping {p}: {exc}", file=sys.stderr)
            continue
        if skill and data.get("skill") != skill:
            continue
        rows.append(data)
    return rows


def table(rows: list[dict], with_skill: bool) -> str:
    head = ("| Skill | " if with_skill else "| ") + "Scenario | Host | Result | Up-front q | Deferred q | Judge checks |"
    sep = ("|---|" if with_skill else "|") + "---|---|---|---|---|---|"
    out = [head, sep]
    for r in rows:
        q = r.get("questions", {})
        j = r.get("judge", {})
        passed, failed = j.get("passed", 0), j.get("failed", 0)
        cells = []
        if with_skill:
            cells.append(r.get("skill", "?"))
        cells += [
            r.get("label") or r.get("scenario", "?"),
            r.get("host", "?"),
            "pass" if r.get("pass") else "FAIL",
            f"{q.get('upfront', '?')}/{q.get('upfront_max', '?')}",
            f"{q.get('deferred', '?')}/{q.get('deferred_max', '?')}",
            f"{passed}/{passed + failed}",
        ]
        out.append("| " + " | ".join(str(c) for c in cells) + " |")
    return "\n".join(out)


def summary(rows: list[dict], run_url: str | None, trigger: str | None, date: str, with_skill: bool) -> str:
    lines = []
    if not rows:
        lines.append("No results were produced (host jobs skipped or failed before grading).")
    else:
        total = len(rows)
        ok = sum(1 for r in rows if r.get("pass"))
        hosts = ", ".join(sorted({r.get("host", "?") for r in rows}))
        lines.append(f"**{ok}/{total} passed** on {hosts}.")
        lines.append("")
        lines.append(table(rows, with_skill))
    meta = [f"Last run: {date}"]
    if trigger:
        meta.append(f"trigger: {trigger}")
    if run_url:
        meta.append(f"[workflow run]({run_url})")
    lines.append("")
    lines.append(" · ".join(meta) + ".")
    lines.append("")
    lines.append("Non-blocking. Full output is in the workflow artifacts.")
    return "\n".join(lines)


def write_readme(path: pathlib.Path, block: str) -> bool:
    text = path.read_text()
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        print(f"eval-report: markers {START} / {END} not found in {path}", file=sys.stderr)
        return False
    new = text[: start + len(START)] + "\n" + block + "\n" + text[end:]
    if new == text:
        return False
    path.write_text(new)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_dir", type=pathlib.Path)
    ap.add_argument("--skill")
    ap.add_argument("--readme", type=pathlib.Path)
    ap.add_argument("--run-url")
    ap.add_argument("--trigger")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args()

    rows = load_rows(args.results_dir, args.skill)
    block = summary(rows, args.run_url, args.trigger, args.date, with_skill=not args.skill)
    title = f"## Scenario eval results ({args.skill})" if args.skill else "## Scenario eval results"
    print(title + "\n")
    print(block)

    if args.readme:
        if not rows:
            print("eval-report: no results; README left unchanged", file=sys.stderr)
        elif write_readme(args.readme, block):
            print(f"eval-report: updated {args.readme}", file=sys.stderr)
        else:
            print(f"eval-report: {args.readme} unchanged", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
