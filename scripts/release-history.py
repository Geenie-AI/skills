#!/usr/bin/env python3
"""Summarise a release's scenario results and record them in RELEASES.md.

Usage:
  scripts/release-history.py RESULTS_DIR --tag vX.Y.Z
                             [--host H] [--skill S] [--scenario X]
                             [--run-url URL] [--results-url URL]
                             [--artifact-url URL] [--date YYYY-MM-DD]
                             [--history RELEASES.md]

RESULTS_DIR is searched recursively for results.json files produced by
scripts/run-scenario.sh. The release section (Markdown, for the GitHub
release body) is printed to stdout. With --history the same section, headed
by the tag, is inserted at the top of the list between the markers below,
replacing an earlier entry for the same tag (a re-run of the release).
Failed scenarios are listed with the text of each failed check from the
scenario's expected-checks.md and the judge's reason; the release and its
history entry are marked as failing.
--host, --skill and --scenario only label what was selected for the run.
--results-url links the full results attached to the release (permanent);
--artifact-url links the workflow artifact (expires with its retention).
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

START = "<!-- release-history:start -->"
END = "<!-- release-history:end -->"

_spec = importlib.util.spec_from_file_location("eval_report", pathlib.Path(__file__).with_name("eval-report.py"))
eval_report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_report)


def check_texts(r: dict) -> dict[str, str]:
    """Numbered checks of the scenario's expected-checks.md, by number."""
    path = ROOT / "tests" / str(r.get("skill", "")) / "scenarios" / str(r.get("scenario", "")) / "expected-checks.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    return {m.group(1): " ".join(m.group(2).split()) for m in re.finditer(r"(?m)^(\d+)\.\s+(.+)$", text)}


def failures(r: dict) -> list[str]:
    """Why one scenario failed, one short reason per item."""
    out = []
    if not r.get("produced_primary", True):
        out.append(f"`{r.get('primary_document', 'primary document')}` not produced")
    q = r.get("questions", {})
    if r.get("budget_ok") is False:
        out.append(
            f"question budget exceeded (up-front {q.get('upfront')}/{q.get('upfront_max')}, "
            f"deferred {q.get('deferred')}/{q.get('deferred_max')})"
        )
    if q.get("expected_but_not_asked"):
        out.append("expected questions not asked: " + ", ".join(q["expected_but_not_asked"]))
    if q.get("forbidden_but_asked"):
        out.append("questions asked that should not be: " + ", ".join(q["forbidden_but_asked"]))
    if q.get("missing_reason"):
        out.append("questions logged without a reason: " + ", ".join(q["missing_reason"]))
    j = r.get("judge", {})
    if j.get("error"):
        out.append(f"judge: {j['error']}")
    texts = check_texts(r)
    for c in j.get("checks", []):
        if c.get("pass") is not True:
            cid = str(c.get("id", "?"))
            item = f"check {cid} failed" + (f": {texts[cid]}" if cid in texts else "")
            reason = " ".join(str(c.get("reason", "")).split())
            if reason:
                item += f"\n    - judge: {reason}"
            out.append(item)
    return out or ["failed (see full results)"]


def failed_count(rows: list[dict]) -> int:
    return sum(1 for r in rows if not r.get("pass"))


def body(
    rows: list[dict],
    host: str,
    skill: str,
    scenario: str,
    run_url: str | None,
    date: str,
    results_url: str | None = None,
    artifact_url: str | None = None,
) -> str:
    lines = [f"Selection: host `{host}` · skills `{skill}` · scenario `{scenario}`.", ""]
    if not rows:
        lines.append("> [!WARNING]\n> No scenario results were produced; this release is untested.")
    else:
        bad = failed_count(rows)
        if bad:
            lines.append(
                f"> [!WARNING]\n> **{bad} of {len(rows)} scenarios failed.** "
                "The release was published anyway; the failed checks are listed below."
            )
        else:
            lines.append(f"**All {len(rows)} scenarios passed.**")
        lines.append("")
        lines.append(eval_report.table(rows, with_skill=True))
        failed = [r for r in rows if not r.get("pass")]
        if failed:
            lines += ["", "Failures:", ""]
            for r in failed:
                name = f"{r.get('skill', '?')} / {r.get('label') or r.get('scenario', '?')} / {r.get('host', '?')}"
                lines.append(f"- **{name}**")
                lines += [f"  - {f}" for f in failures(r)]
    links = []
    if results_url:
        links.append(f"[full results (zip)]({results_url})")
    if artifact_url:
        links.append(f"[workflow artifact]({artifact_url})")
    if run_url:
        links.append(f"[workflow run]({run_url})")
    lines += ["", " · ".join([f"Run: {date}"] + links) + "."]
    if results_url:
        lines += [
            "",
            "The zip holds each scenario's `results.json`, `summary.md`, judge output and run log.",
        ]
    return "\n".join(lines)


def write_history(path: pathlib.Path, tag: str, entry: str) -> None:
    text = path.read_text()
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit(f"release-history: markers {START} / {END} not found in {path}")
    inner = text[start + len(START) : end]
    # Entries start with "## <tag> (date)[ — flag]"; drop an earlier one for this tag.
    parts = re.split(r"(?m)^(?=## )", inner.strip("\n"))
    kept = [p.strip("\n") for p in parts if p.strip() and not p.startswith(f"## {tag}\n") and not p.startswith(f"## {tag} ")]
    new_inner = "\n\n".join([entry] + kept)
    path.write_text(text[: start + len(START)] + "\n" + new_inner + "\n" + text[end:])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_dir", type=pathlib.Path)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--host", default="claude")
    ap.add_argument("--skill", default="all")
    ap.add_argument("--scenario", default="all")
    ap.add_argument("--run-url")
    ap.add_argument("--results-url")
    ap.add_argument("--artifact-url")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--history", type=pathlib.Path)
    args = ap.parse_args()

    rows = eval_report.load_rows(args.results_dir, None) if args.results_dir.exists() else []
    text = body(rows, args.host, args.skill, args.scenario, args.run_url, args.date, args.results_url, args.artifact_url)
    print("## Scenario results\n")
    print(text)

    if args.history:
        bad = failed_count(rows)
        flag = f" — {bad} failing" if bad else (" — untested" if not rows else "")
        write_history(args.history, args.tag, f"## {args.tag} ({args.date}){flag}\n\n{text}")
        print(f"release-history: updated {args.history}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
