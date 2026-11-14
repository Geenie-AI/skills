#!/usr/bin/env python3
"""Helper for scripts/run-scenario.sh: builds the judge prompt and scores a run.

Subcommands:

  judge-prompt --skill NAME --scenario DIR --project DIR
      Prints tests/<skill>/judge-prompt.md with the placeholders filled:
      {{EXPECTED_CHECKS}}, {{ARCHITECTURE_MD}} (the skill's primary document),
      {{ARTIFACT_LISTING}}, {{QUESTIONS_LOG}}.

  score --skill NAME --scenario DIR --project DIR --judge-output FILE --out DIR
        [--host H] [--answers FILE] [--label L]
      Reads the answers file (budgets and expectations), the project's
      questions.log, and the judge's raw output; writes <out>/results.json and
      <out>/summary.md. Exit status 0 when the scenario passed, 1 otherwise.

The skill's output folder, primary document and question-ID pattern come from
tests/<skill>/config.yaml (see scripts/skillrepo.py). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillrepo import ROOT, YamlError, load_config, load_yaml  # noqa: E402

MAX_ARTIFACT_CHARS = 12_000   # per file, so the judge prompt stays bounded
MAX_LISTING_CHARS = 120_000   # total across all artifact contents


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def read_answers(path: Path) -> dict:
    try:
        return load_yaml(path.read_text(encoding="utf-8"))
    except (OSError, YamlError) as exc:
        sys.exit(f"grade-scenario: cannot read {path}: {exc}")


def read_questions(project: Path, question_re: re.Pattern) -> list[dict]:
    log = project / "questions.log"
    if not log.exists():
        return []
    line_re = re.compile(rf"^\s*(upfront|deferred)\s+({question_re.pattern})\s*\|", re.IGNORECASE)
    rows: list[dict] = []
    for raw in log.read_text(encoding="utf-8").splitlines():
        m = line_re.match(raw)
        if not m:
            continue
        parts = [p.strip() for p in raw.split("|")]
        rows.append(
            {
                "timing": m.group(1).lower(),
                "q": m.group(2).upper(),
                "reason": parts[1] if len(parts) > 1 else "",
                "decision": parts[2] if len(parts) > 2 else "",
            }
        )
    return rows


def artifact_listing(out_dir: Path, primary: str, extra_files: list[str] | None = None) -> str:
    """File list plus contents of every emitted artifact (the primary document is
    supplied separately). Extra files (for example a cross-run diff) are appended
    under their own name so the judge can cite them."""
    if not out_dir.exists() and not extra_files:
        return f"(no {out_dir.name}/ directory was produced)"
    names: list[str] = []
    bodies: list[str] = []
    budget = MAX_LISTING_CHARS
    files = sorted(p for p in out_dir.rglob("*") if p.is_file()) if out_dir.exists() else []
    for p in files:
        rel = str(p.relative_to(out_dir))
        names.append(f"{rel}  ({p.stat().st_size} bytes)")
        if rel == primary:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = "(binary file)"
        if len(text) > MAX_ARTIFACT_CHARS:
            text = text[:MAX_ARTIFACT_CHARS] + "\n… (truncated)"
        if budget - len(text) < 0:
            bodies.append(f"\n===== {rel} =====\n(omitted: listing budget exhausted)")
            continue
        budget -= len(text)
        bodies.append(f"\n===== {rel} =====\n{text}")
    for extra in extra_files or []:
        ep = Path(extra)
        if ep.exists():
            text = ep.read_text(encoding="utf-8")
            if len(text) > MAX_ARTIFACT_CHARS * 2:
                text = text[:MAX_ARTIFACT_CHARS * 2] + "\n… (truncated)"
            names.append(f"{ep.name}  ({ep.stat().st_size} bytes, supplied by the runner)")
            bodies.append(f"\n===== {ep.name} =====\n{text}")
    if not names:
        return f"({out_dir.name}/ is empty)"
    return "\n".join(names) + "\n" + "".join(bodies)


def primary_text(out_dir: Path, primary: str) -> str:
    path = out_dir / primary
    if not path.exists():
        return f"({primary} was not produced)"
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# judge-prompt
# --------------------------------------------------------------------------- #


def cmd_judge_prompt(args: argparse.Namespace) -> int:
    cfg = load_config(args.skill)["eval"]
    out_dir = Path(args.project) / cfg["output_dir"]
    template = (ROOT / "tests" / args.skill / "judge-prompt.md").read_text(encoding="utf-8")
    checks = (Path(args.scenario) / "expected-checks.md").read_text(encoding="utf-8")
    questions = Path(args.project) / "questions.log"
    qlog = questions.read_text(encoding="utf-8") if questions.exists() else "(no questions were asked)"
    filled = (
        template.replace("{{EXPECTED_CHECKS}}", checks)
        .replace("{{ARCHITECTURE_MD}}", primary_text(out_dir, cfg["primary_document"]))
        .replace("{{ARTIFACT_LISTING}}", artifact_listing(out_dir, cfg["primary_document"], args.extra_file))
        .replace("{{QUESTIONS_LOG}}", qlog)
    )
    sys.stdout.write(filled)
    return 0


# --------------------------------------------------------------------------- #
# score
# --------------------------------------------------------------------------- #


def _loads(text: str):
    try:
        return json.loads(text, strict=False)  # tolerate raw newlines inside strings
    except json.JSONDecodeError:
        return None


def _balanced_objects(text: str):
    """Yield every balanced {...} substring, outermost first, ignoring braces in strings."""
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for start in starts:
        depth = 0
        in_str = False
        esc = False
        for j in range(start, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield text[start : j + 1]
                    break


def extract_json(text: str) -> dict | None:
    """Find the judge's JSON object in free text (optionally fenced or wrapped).

    Claude Code's --output-format json wraps the answer as {"result": "..."} (or
    {"structured_output": {...}} with --json-schema); Codex -o writes the bare
    message. The judge may also fence its JSON or add prose around it.
    """
    text = text.strip()
    outer = _loads(text)
    if isinstance(outer, dict):
        if "checks" in outer:
            return outer
        if isinstance(outer.get("structured_output"), dict) and "checks" in outer["structured_output"]:
            return outer["structured_output"]
        if isinstance(outer.get("result"), str):
            text = outer["result"]
    for candidate in _balanced_objects(text):
        if "checks" not in candidate:
            continue
        for variant in (candidate, candidate.replace('\\"', '"')):
            data = _loads(variant)
            if isinstance(data, dict) and isinstance(data.get("checks"), list):
                return data
    return None


def cmd_score(args: argparse.Namespace) -> int:
    cfg = load_config(args.skill)["eval"]
    question_re = re.compile(cfg["question_id_pattern"])
    scenario = Path(args.scenario)
    project = Path(args.project)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    answers = read_answers(scenario / args.answers)
    budget = answers.get("budget") or {}
    upfront_max = int(budget.get("upfront_max", 0))
    deferred_max = int(budget.get("deferred_max", 0))
    expect_asked = [str(q).upper() for q in (answers.get("expect_asked") or [])]
    expect_not_asked = [str(q).upper() for q in (answers.get("expect_not_asked") or [])]

    rows = read_questions(project, question_re)
    asked = {r["q"] for r in rows}
    upfront = sum(1 for r in rows if r["timing"] == "upfront")
    deferred = sum(1 for r in rows if r["timing"] == "deferred")
    missing_reason = [r["q"] for r in rows if not r["reason"]]
    budget_ok = upfront <= upfront_max and deferred <= deferred_max
    not_asked_but_expected = [q for q in expect_asked if q not in asked]
    asked_but_forbidden = [q for q in expect_not_asked if q in asked]
    expectations_ok = not not_asked_but_expected and not asked_but_forbidden and not missing_reason

    judge_raw = Path(args.judge_output).read_text(encoding="utf-8") if Path(args.judge_output).exists() else ""
    judge = extract_json(judge_raw)
    judge_ok = False
    if judge is not None:
        checks = judge.get("checks") or []
        passed = sum(1 for c in checks if c.get("pass") is True)
        failed = len(checks) - passed
        judge = {"checks": checks, "passed": passed, "failed": failed}
        judge_ok = failed == 0 and len(checks) > 0
    else:
        judge = {"checks": [], "passed": 0, "failed": 0, "error": "judge output had no parseable JSON"}

    produced = (project / cfg["output_dir"] / cfg["primary_document"]).exists()
    result = {
        "skill": args.skill,
        "scenario": scenario.name,
        "label": args.label or scenario.name,
        "host": args.host,
        "produced_primary": produced,
        "primary_document": cfg["primary_document"],
        "questions": {
            "upfront": upfront,
            "deferred": deferred,
            "upfront_max": upfront_max,
            "deferred_max": deferred_max,
            "asked": sorted(asked),
            "missing_reason": missing_reason,
            "expected_but_not_asked": not_asked_but_expected,
            "forbidden_but_asked": asked_but_forbidden,
        },
        "budget_ok": budget_ok,
        "expectations_ok": expectations_ok,
        "judge": judge,
        "pass": produced and budget_ok and expectations_ok and judge_ok,
    }
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(render_summary(result), encoding="utf-8")
    print(render_summary(result))
    return 0 if result["pass"] else 1


def render_summary(r: dict) -> str:
    q = r["questions"]
    status = "PASS" if r["pass"] else "FAIL"
    lines = [
        f"## {r['skill']} / {r['label']} on {r['host'] or 'unknown host'}: {status}",
        "",
        f"- {r['primary_document']} produced: {'yes' if r['produced_primary'] else 'no'}",
        f"- questions up front: {q['upfront']} / {q['upfront_max']}  deferred: {q['deferred']} / {q['deferred_max']}  budget {'ok' if r['budget_ok'] else 'exceeded'}",
    ]
    if q["missing_reason"]:
        lines.append(f"- questions without a reason: {', '.join(q['missing_reason'])}")
    if q["expected_but_not_asked"]:
        lines.append(f"- expected but not asked: {', '.join(q['expected_but_not_asked'])}")
    if q["forbidden_but_asked"]:
        lines.append(f"- asked but should not have been: {', '.join(q['forbidden_but_asked'])}")
    j = r["judge"]
    if j.get("error"):
        lines.append(f"- judge: {j['error']}")
    else:
        lines.append(f"- judge checks: {j['passed']} passed, {j['failed']} failed")
        for c in j.get("checks", []):
            if c.get("pass") is not True:
                lines.append(f"  - check {c.get('id')}: {c.get('reason', '').strip()}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    jp = sub.add_parser("judge-prompt")
    jp.add_argument("--skill", required=True)
    jp.add_argument("--scenario", required=True)
    jp.add_argument("--project", required=True)
    jp.add_argument("--extra-file", action="append", default=[], help="extra file to include in the artifact listing (e.g. a cross-run diff)")
    jp.set_defaults(func=cmd_judge_prompt)
    sc = sub.add_parser("score")
    sc.add_argument("--skill", required=True)
    sc.add_argument("--scenario", required=True)
    sc.add_argument("--project", required=True)
    sc.add_argument("--judge-output", required=True)
    sc.add_argument("--out", required=True)
    sc.add_argument("--host", default="")
    sc.add_argument("--answers", default="answers.yaml")
    sc.add_argument("--label", default="")
    sc.set_defaults(func=cmd_score)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
