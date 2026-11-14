#!/usr/bin/env python3
"""Static validation for every skill in the repository.

Runs without a model. Exit status 1 when any check fails. Every failure is
printed as ``path:line: message`` so editors can jump to it.

Per skill (``skills/<name>/``, settings in ``tests/<name>/config.yaml``):

  frontmatter   SKILL.md has ``name`` (equal to the folder name) and ``description``
                (1-1024 chars); the only other keys allowed are the Agent Skills
                spec's optional ``license``, ``compatibility`` and ``metadata``.
                Host-specific keys live in adapters, never here (H3).
  host-tools    No host tool name from scripts/host-tool-names.txt in the skill's
                model-facing files (H1).
  links         Every relative link and skill-internal path resolves (H4).
  budgets       SKILL.md and every other model-facing .md stay under the line budgets.
  rule-ids      Every rule ID is defined exactly once across the skill and
                adapters/README.md; every ID cited in SKILL.md is defined; every ID
                and ``doc § n`` cited in expected-checks.md exists.
  scenarios     Each scenario has input.md, a parseable answers.yaml with the
                required keys, and expected-checks.md with a numbered check.
  harness       tests/<name>/ has config.yaml, judge-prompt.md (with the four
                placeholders) and preamble.md.
  package       skills/<name>/ has a README.md.
  changelog     With --changed-files: if any model-facing file of a skill changed,
                the root CHANGELOG.md ``## [Unreleased]`` section must not be empty.

Repository-wide:

  overlays      Every directory under adapters/ has a README.md that points at
                the shared skills folder by relative path.
  manifests     .claude-plugin/marketplace.json parses, carries the repository
                ``version``, has one entry per skill with ``source: "./"`` and
                ``skills: ["./skills/<name>"]`` at that version, and no entry for
                a skill that does not exist.
  catalogue     README.md's catalogue block and the marketplace descriptions match
                the skills on disk (warning only; ``skillrepo.py sync`` fixes it and
                the catalog workflow commits it).

Usage:
  python3 scripts/validate.py [--skill NAME] [--changed-files F ...]
                              [--changed-files-from FILE] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillrepo import (  # noqa: E402
    HUMAN_FILES,
    ROOT,
    YamlError,
    list_skills,
    load_config,
    load_yaml,
    marketplace,
    parse_frontmatter,
    sync,
)

# --------------------------------------------------------------------------- #
# Shared constants
# --------------------------------------------------------------------------- #

# Shape of a rule ID: one to three capitals, a number, an optional letter, an
# optional ".n" (R4.1, R4a.1, P12, G6.1, SC1, AS1, E1, H1, Q26).
ID_SHAPE = r"[A-Z]{1,3}\d{1,2}[a-z]?(?:\.\d{1,2})?"
# A rule is *defined* on a bullet that opens with the bold ID, or on a table row
# whose first cell is the ID. Everything else is a citation.
DEF_BULLET_RE = re.compile(rf"^\s*[-*]\s+\*\*({ID_SHAPE})\b")
DEF_ROW_RE = re.compile(rf"^\|\s*({ID_SHAPE})\s*\|")
SECTION_CITE_RE = re.compile(r"(?:\bdoc\s*)?§\s*(\d+(?:\.\d+)?[a-z]?)")
HEADING_NUM_RE = re.compile(r"^#{2,3}\s+(\d+[a-z]?(?:\.\d+[a-z]?)?)\b")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
NUMBERED_CHECK_RE = re.compile(r"^\s*\d+[.)]\s+\S")
PATH_LIKE_RE = re.compile(r"^[\w./-]+$")
REQUIRED_FRONTMATTER = ("name", "description")
OPTIONAL_FRONTMATTER = ("license", "compatibility", "metadata")  # agentskills.io specification
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
JUDGE_PLACEHOLDERS = ("{{EXPECTED_CHECKS}}", "{{ARCHITECTURE_MD}}", "{{ARTIFACT_LISTING}}", "{{QUESTIONS_LOG}}")


@dataclass
class Report:
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)

    def fail(self, path: Path | str, line: int | None, msg: str) -> None:
        self.failures.append(_fmt(path, line, msg))

    def warn(self, path: Path | str, line: int | None, msg: str) -> None:
        self.warnings.append(_fmt(path, line, msg))

    def ran(self, name: str) -> None:
        if name not in self.checks_run:
            self.checks_run.append(name)


def _fmt(path: Path | str, line: int | None, msg: str) -> str:
    try:
        path = Path(path).relative_to(ROOT)
    except (ValueError, TypeError):
        pass
    loc = f"{path}:{line}" if line else f"{path}"
    return f"{loc}: {msg}"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def md_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def model_facing(skill_dir: Path) -> list[Path]:
    """Markdown files the model may read: everything except the human files at the top."""
    return [p for p in md_files(skill_dir) if not (p.parent == skill_dir and p.name in HUMAN_FILES)]


# --------------------------------------------------------------------------- #
# Frontmatter (H3)
# --------------------------------------------------------------------------- #


def check_frontmatter(skill_dir: Path, rep: Report) -> None:
    rep.ran("frontmatter")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        rep.fail(skill_md, None, "missing file")
        return
    lines = read_lines(skill_md)
    fm, end = parse_frontmatter(lines)
    if not end:
        rep.fail(skill_md, 1, "frontmatter block (--- ... ---) missing")
        return
    for key in REQUIRED_FRONTMATTER:
        if key not in fm or not fm[key]:
            rep.fail(skill_md, 1, f"frontmatter key '{key}' missing or empty")
    extra = sorted(set(fm) - set(REQUIRED_FRONTMATTER) - set(OPTIONAL_FRONTMATTER))
    if extra:
        rep.fail(skill_md, 1, f"host-specific frontmatter keys in shared SKILL.md: {', '.join(extra)} (H3; put them in adapters/)")
    name = fm.get("name", "")
    if name and name != skill_dir.name:
        rep.fail(skill_md, 1, f"frontmatter name '{name}' != folder name '{skill_dir.name}'")
    if name and not NAME_RE.match(name):
        rep.fail(skill_md, 1, f"name '{name}' must be lowercase letters, digits and single hyphens")
    if name and len(name) > 64:
        rep.fail(skill_md, 1, f"name is {len(name)} chars; limit 64")
    desc = fm.get("description", "")
    if desc and len(desc) > MAX_DESCRIPTION:
        rep.fail(skill_md, 1, f"description is {len(desc)} chars; limit {MAX_DESCRIPTION}")
    compat = fm.get("compatibility", "")
    if compat and len(compat) > MAX_COMPATIBILITY:
        rep.fail(skill_md, 1, f"compatibility is {len(compat)} chars; limit {MAX_COMPATIBILITY}")


# --------------------------------------------------------------------------- #
# H1: host tool names
# --------------------------------------------------------------------------- #


def load_deny_list(path: Path) -> tuple[list[str], list[str]]:
    exact: list[str] = []
    guarded: list[str] = []
    section = None
    for raw in read_lines(path):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[exact]":
            section = exact
        elif line == "[backtick-or-tool]":
            section = guarded
        elif section is not None:
            section.append(line)
    return exact, guarded


def check_host_tools(skill_dir: Path, deny_file: Path, rep: Report) -> None:
    rep.ran("host-tools")
    if not deny_file.exists():
        rep.fail(deny_file, None, "missing deny list")
        return
    exact, guarded = load_deny_list(deny_file)
    exact_re = re.compile(r"\b(" + "|".join(map(re.escape, exact)) + r")\b") if exact else None
    guard_tick_re = re.compile(r"`(" + "|".join(map(re.escape, guarded)) + r")`") if guarded else None
    guard_tool_re = re.compile(r"\b(" + "|".join(map(re.escape, guarded)) + r")\s+tool\b") if guarded else None
    for path in model_facing(skill_dir):
        for n, line in enumerate(read_lines(path), 1):
            if exact_re:
                for m in exact_re.finditer(line):
                    rep.fail(path, n, f"host tool name '{m.group(1)}' (H1: use a capability verb)")
            if guard_tick_re:
                for m in guard_tick_re.finditer(line):
                    rep.fail(path, n, f"host tool name `{m.group(1)}` in backticks (H1)")
            if guard_tool_re:
                for m in guard_tool_re.finditer(line):
                    rep.fail(path, n, f"'{m.group(0)}' names a host tool (H1)")


# --------------------------------------------------------------------------- #
# H4: relative links and skill-internal paths
# --------------------------------------------------------------------------- #


def _is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#", "tel:"))


def _resolves(target: str, from_file: Path, skill_dir: Path) -> bool:
    clean = target.split("#", 1)[0]
    if not clean:
        return True
    candidates = [from_file.parent / clean, skill_dir / clean]
    return any(c.exists() for c in candidates)


def check_links(skill_dir: Path, rep: Report) -> None:
    rep.ran("links")
    top_dirs = tuple(f"{p.name}/" for p in skill_dir.iterdir() if p.is_dir()) + ("./", "../")
    for path in md_files(skill_dir):
        in_fence = False
        for n, line in enumerate(read_lines(path), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            for m in MD_LINK_RE.finditer(line):
                target = m.group(1)
                if _is_external(target) or "<" in target or "*" in target:
                    continue
                if not _resolves(target, path, skill_dir):
                    rep.fail(path, n, f"link target '{target}' does not resolve (H4)")
            if in_fence or (path.parent == skill_dir and path.name in HUMAN_FILES):
                continue
            for m in BACKTICK_RE.finditer(line):
                token = m.group(1).strip()
                if not token.startswith(top_dirs) or not PATH_LIKE_RE.match(token):
                    continue
                if token.endswith("/"):
                    ok = (path.parent / token).is_dir() or (skill_dir / token).is_dir()
                else:
                    ok = _resolves(token, path, skill_dir)
                if not ok:
                    rep.fail(path, n, f"path `{token}` does not resolve (H4)")


# --------------------------------------------------------------------------- #
# Line budgets
# --------------------------------------------------------------------------- #


def check_budgets(skill_dir: Path, max_skill: int, max_ref: int, rep: Report) -> None:
    rep.ran("budgets")
    for path in model_facing(skill_dir):
        count = len(read_lines(path))
        limit = max_skill if path.name == "SKILL.md" and path.parent == skill_dir else max_ref
        if count > limit:
            rep.fail(path, count, f"{count} lines exceeds budget of {limit}")


# --------------------------------------------------------------------------- #
# Rule-ID integrity
# --------------------------------------------------------------------------- #


def collect_definitions(files: Iterable[Path]) -> dict[str, list[tuple[Path, int]]]:
    defs: dict[str, list[tuple[Path, int]]] = {}
    for path in files:
        if not path.exists():
            continue
        in_fence = False
        for n, line in enumerate(read_lines(path), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = DEF_BULLET_RE.match(line) or DEF_ROW_RE.match(line)
            if m:
                defs.setdefault(m.group(1), []).append((path, n))
    return defs


def citation_regex(defs: dict[str, list]) -> re.Pattern | None:
    """IDs are cited only in the families (letter prefixes) that define a rule,
    and in the shape that family uses (R4.1 with a dot, P12 without), so ordinary
    text such as "S3", "H2O" or a bare section number "R4" is never mistaken for
    a citation."""
    families: dict[str, set[bool]] = {}
    for key in defs:
        prefix = re.match(r"[A-Z]+", key).group(0)
        families.setdefault(prefix, set()).add("." in key)
    if not families:
        return None
    parts = []
    for prefix in sorted(families, key=len, reverse=True):
        dotted = families[prefix]
        if dotted == {True}:
            parts.append(rf"{prefix}\d{{1,2}}[a-z]?\.\d{{1,2}}")
        elif dotted == {False}:
            parts.append(rf"{prefix}\d{{1,2}}[a-z]?")
        else:
            parts.append(rf"{prefix}\d{{1,2}}[a-z]?(?:\.\d{{1,2}})?")
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b")


def collect_citations(path: Path, cite_re: re.Pattern) -> list[tuple[int, str]]:
    cites: list[tuple[int, str]] = []
    for n, line in enumerate(read_lines(path), 1):
        for m in cite_re.finditer(line):
            cites.append((n, m.group(0)))
    return cites


def collect_doc_sections(template: Path | None) -> set[str] | None:
    if template is None or not template.exists():
        return None
    sections = {"0"}
    for line in read_lines(template):
        m = HEADING_NUM_RE.match(line)
        if m:
            sections.add(m.group(1))
    return sections


def check_rule_ids(skill_dir: Path, adapters_readme: Path, scenarios_dir: Path, section_template: Path | None, rep: Report) -> None:
    rep.ran("rule-ids")
    sources = model_facing(skill_dir) + [adapters_readme]
    defs = collect_definitions(sources)
    for rule_id, places in sorted(defs.items()):
        if len(places) > 1:
            where = ", ".join(f"{_fmt(p, n, '')[:-2]}" for p, n in places)
            rep.fail(places[0][0], places[0][1], f"rule {rule_id} defined {len(places)} times ({where})")
    cite_re = citation_regex(defs)
    if cite_re is None:
        return
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        for n, rule_id in collect_citations(skill_md, cite_re):
            if rule_id not in defs:
                rep.fail(skill_md, n, f"rule {rule_id} cited but not defined anywhere")
    for path in model_facing(skill_dir):
        if path == skill_md:
            continue
        for n, rule_id in collect_citations(path, cite_re):
            if rule_id not in defs:
                rep.warn(path, n, f"rule {rule_id} cited but not defined (warning)")
    sections = collect_doc_sections(section_template)
    if scenarios_dir.exists():
        for checks in sorted(scenarios_dir.glob("*/expected-checks.md")):
            for n, rule_id in collect_citations(checks, cite_re):
                if rule_id not in defs:
                    rep.fail(checks, n, f"rule {rule_id} cited but not defined")
            if sections is None:
                continue
            for n, line in enumerate(read_lines(checks), 1):
                for m in SECTION_CITE_RE.finditer(line):
                    if m.group(1) not in sections:
                        rep.fail(checks, n, f"section § {m.group(1)} not in {section_template.name}")


# --------------------------------------------------------------------------- #
# Scenario fixtures
# --------------------------------------------------------------------------- #


def check_scenarios(scenarios_dir: Path, question_re: re.Pattern, rep: Report) -> None:
    rep.ran("scenarios")
    if not scenarios_dir.exists():
        rep.warn(scenarios_dir, None, "no scenarios directory; a release needs at least one scenario")
        return
    dirs = sorted(d for d in scenarios_dir.iterdir() if d.is_dir())
    if not dirs:
        rep.warn(scenarios_dir, None, "no scenario folders; a release needs at least one scenario")
    for d in dirs:
        for required in ("input.md", "answers.yaml", "expected-checks.md"):
            if not (d / required).exists():
                rep.fail(d / required, None, "missing file")
        for answers in sorted(d.glob("answers*.yaml")):
            try:
                data = load_yaml(answers.read_text(encoding="utf-8"))
            except YamlError as exc:
                rep.fail(answers, None, f"cannot parse: {exc}")
                continue
            if not isinstance(data.get("scenario"), str):
                rep.fail(answers, None, "missing key 'scenario' (string)")
            if "expected" in data and not isinstance(data["expected"], dict):
                rep.fail(answers, None, "key 'expected' must be a mapping")
            budget = data.get("budget")
            if not isinstance(budget, dict):
                rep.fail(answers, None, "missing key 'budget' (mapping)")
            else:
                for key in ("upfront_max", "deferred_max"):
                    if not isinstance(budget.get(key), int):
                        rep.fail(answers, None, f"'budget.{key}' must be an integer")
            answers_map = data.get("answers")
            if not isinstance(answers_map, dict):
                rep.fail(answers, None, "missing key 'answers' (mapping)")
            else:
                for key in answers_map:
                    if not question_re.fullmatch(str(key)):
                        rep.fail(answers, None, f"answers key '{key}' does not match the question ID pattern")
            for key in ("expect_asked", "expect_not_asked"):
                for q in data.get(key) or []:
                    if not question_re.fullmatch(str(q)):
                        rep.fail(answers, None, f"{key} entry '{q}' does not match the question ID pattern")
        checks = d / "expected-checks.md"
        if checks.exists() and not any(NUMBERED_CHECK_RE.match(ln) for ln in read_lines(checks)):
            rep.fail(checks, None, "no numbered checks found")
        build = d / "fixtures" / "build.py"
        if build.exists():
            try:
                compile(build.read_text(encoding="utf-8"), str(build), "exec")
            except SyntaxError as exc:
                rep.fail(build, exc.lineno, f"syntax error: {exc.msg}")


# --------------------------------------------------------------------------- #
# Test harness files and package files
# --------------------------------------------------------------------------- #


def check_harness(tests_dir: Path, rep: Report) -> None:
    rep.ran("harness")
    if not tests_dir.exists():
        rep.fail(tests_dir, None, "missing tests/<skill>/ directory")
        return
    for name in ("config.yaml", "judge-prompt.md", "preamble.md"):
        if not (tests_dir / name).exists():
            rep.fail(tests_dir / name, None, "missing file")
    judge = tests_dir / "judge-prompt.md"
    if judge.exists():
        text = judge.read_text(encoding="utf-8")
        for ph in JUDGE_PLACEHOLDERS:
            if ph not in text:
                rep.fail(judge, None, f"placeholder {ph} missing")
    cfg = tests_dir / "config.yaml"
    if cfg.exists():
        try:
            data = load_yaml(cfg.read_text(encoding="utf-8"))
        except YamlError as exc:
            rep.fail(cfg, None, f"cannot parse: {exc}")
            return
        if data.get("skill") != tests_dir.name:
            rep.fail(cfg, None, f"'skill' must be '{tests_dir.name}'")
        ev = data.get("eval") or {}
        if not ev.get("output_dir"):
            rep.fail(cfg, None, "eval.output_dir is required (the folder the skill writes into)")
        if not ev.get("primary_document"):
            rep.fail(cfg, None, "eval.primary_document is required (the file the judge reads in full)")


def check_package(skill_dir: Path, rep: Report) -> None:
    rep.ran("package")
    for name in HUMAN_FILES:
        if not (skill_dir / name).exists():
            rep.fail(skill_dir / name, None, "missing file")


# --------------------------------------------------------------------------- #
# Overlays
# --------------------------------------------------------------------------- #

RELATIVE_SKILLS_REF_RE = re.compile(r"(?:\.\./)+skills/|\./skills/")


def check_overlays(adapters_dir: Path, rep: Report) -> None:
    rep.ran("overlays")
    if not adapters_dir.exists():
        rep.fail(adapters_dir, None, "missing directory")
        return
    for d in sorted(p for p in adapters_dir.iterdir() if p.is_dir()):
        readme = d / "README.md"
        if not readme.exists():
            rep.fail(readme, None, "overlay has no README.md")
            continue
        if not RELATIVE_SKILLS_REF_RE.search(readme.read_text(encoding="utf-8")):
            rep.fail(readme, None, "README must reference the shared skills folder (../../skills/) by relative path")


# --------------------------------------------------------------------------- #
# Marketplace manifest
# --------------------------------------------------------------------------- #


def check_manifests(root: Path, skills: list[str], rep: Report) -> dict[str, dict]:
    rep.ran("manifests")
    path = root / ".claude-plugin" / "marketplace.json"
    entries: dict[str, dict] = {}
    if not path.exists():
        rep.fail(path, None, "missing file")
        return entries
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.fail(path, exc.lineno, f"invalid JSON: {exc.msg}")
        return entries
    for key in ("name", "owner", "plugins"):
        if key not in data:
            rep.fail(path, None, f"marketplace.json missing '{key}'")
    if not isinstance(data.get("owner"), dict) or not data["owner"].get("name"):
        rep.fail(path, None, "owner.name is required")
    version = data.get("version")
    if not version or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", str(version)):
        rep.fail(path, None, "top-level 'version' must be the repository's semantic version (X.Y.Z)")
    seen: set[str] = set()
    for entry in data.get("plugins") or []:
        name = entry.get("name", "")
        if name in seen:
            rep.fail(path, None, f"duplicate plugin entry '{name}'")
        seen.add(name)
        if name not in skills:
            rep.fail(path, None, f"plugin entry '{name}' has no skills/{name}/SKILL.md")
            continue
        entries[name] = entry
        if entry.get("source") not in (".", "./"):
            rep.fail(path, None, f"entry '{name}': source must be './' (the repository root is the marketplace)")
        wanted = f"./skills/{name}"
        if entry.get("skills") != [wanted]:
            rep.fail(path, None, f"entry '{name}': skills must be [\"{wanted}\"] so only that folder loads")
        if version and entry.get("version") != version:
            rep.fail(path, None, f"entry '{name}': version {entry.get('version')!r} differs from the repository version {version!r} (run scripts/skillrepo.py sync)")
    for name in skills:
        if name not in seen:
            rep.fail(path, None, f"no plugin entry for skills/{name} (run scripts/skillrepo.py sync)")
    return entries


def check_catalogue(root: Path, rep: Report) -> None:
    rep.ran("catalogue")
    for name in sync(root, write=False):
        rep.warn(root / name, None, "out of date with the skills on disk; run scripts/skillrepo.py sync (the catalog workflow does this on main)")


# --------------------------------------------------------------------------- #
# CHANGELOG (per skill, on pull requests)
# --------------------------------------------------------------------------- #


def unreleased_section(changelog: Path) -> list[str]:
    out: list[str] = []
    inside = False
    for line in read_lines(changelog):
        if line.startswith("## "):
            if inside:
                break
            inside = line.lower().startswith("## [unreleased]")
            continue
        if inside:
            out.append(line)
    return out


def check_changelog(root: Path, skills: list[str], changed: list[str], rep: Report) -> None:
    rep.ran("changelog")
    changelog = root / "CHANGELOG.md"
    if not changelog.exists():
        rep.fail(changelog, None, "missing file")
        return
    touched = []
    for c in changed:
        p = c.replace("\\", "/")
        for name in skills:
            prefix = f"skills/{name}/"
            if p.startswith(prefix) and p[len(prefix):] not in HUMAN_FILES:
                touched.append(p)
    if not touched:
        return
    placeholder = re.compile(r"^[-*\s]*_?\(?(nothing yet|none|no unreleased changes|no changes yet)\.?\)?_?$", re.I)
    body = [
        ln for ln in unreleased_section(changelog)
        if ln.strip() and not ln.startswith("#") and not placeholder.match(ln.strip())
    ]
    if not body:
        rep.fail(changelog, None, f"{len(touched)} model-facing skill file(s) changed but '## [Unreleased]' is empty")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def validate_skill(root: Path, name: str, entries: dict[str, dict], changed: list[str] | None, rep: Report) -> None:
    skill_dir = root / "skills" / name
    tests_dir = root / "tests" / name
    cfg = load_config(name, root)
    v, e = cfg["validate"], cfg["eval"]
    section_template = (skill_dir / v["section_template"]) if v.get("section_template") else None
    try:
        question_re = re.compile(e["question_id_pattern"])
    except re.error as exc:
        rep.fail(tests_dir / "config.yaml", None, f"eval.question_id_pattern is not a valid regex: {exc}")
        question_re = re.compile(r"Q\d{1,2}")

    check_frontmatter(skill_dir, rep)
    check_host_tools(skill_dir, root / "scripts" / "host-tool-names.txt", rep)
    check_links(skill_dir, rep)
    check_budgets(skill_dir, int(v["max_skill_lines"]), int(v["max_reference_lines"]), rep)
    check_rule_ids(skill_dir, root / "adapters" / "README.md", tests_dir / "scenarios", section_template, rep)
    check_scenarios(tests_dir / "scenarios", question_re, rep)
    check_harness(tests_dir, rep)
    check_package(skill_dir, rep)


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=None, help="repository root (default: parent of scripts/)")
    ap.add_argument("--skill", default=None, help="validate one skill only (default: every skill)")
    ap.add_argument("--changed-files", nargs="*", default=None, help="paths changed in this PR; enables the CHANGELOG check")
    ap.add_argument("--changed-files-from", type=Path, default=None, help="file with one changed path per line")
    ap.add_argument("--quiet", action="store_true")
    return ap.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = (args.root or ROOT).resolve()
    rep = Report()

    skills = list_skills(root)
    if not skills:
        rep.fail(root / "skills", None, "no skill folders with a SKILL.md")
    if args.skill and args.skill not in skills:
        rep.fail(root / "skills" / args.skill, None, "no such skill")
    selected = [args.skill] if args.skill else skills

    changed: list[str] | None = None
    if args.changed_files is not None:
        changed = list(args.changed_files)
    if args.changed_files_from is not None:
        changed = (changed or []) + [ln.strip() for ln in read_lines(args.changed_files_from) if ln.strip()]

    entries = check_manifests(root, skills, rep)
    check_overlays(root / "adapters", rep)
    check_catalogue(root, rep)
    for name in selected:
        if name in skills:
            validate_skill(root, name, entries, changed, rep)
    if changed is not None:
        check_changelog(root, skills, changed, rep)

    for w in rep.warnings:
        print(f"warning: {w}")
    for f in rep.failures:
        print(f"FAIL: {f}")
    if not args.quiet:
        print(f"skills: {', '.join(selected)}")
        print(f"checks run: {', '.join(rep.checks_run)}")
    if rep.failures:
        print(f"{len(rep.failures)} failure(s), {len(rep.warnings)} warning(s)")
        return 1
    print(f"OK ({len(rep.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
