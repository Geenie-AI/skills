#!/usr/bin/env python3
"""Shared helpers for the skills repository tooling.

Every script under scripts/ imports this module for the repository layout, the
list of skills, each skill's configuration (``tests/<skill>/config.yaml``) and a
small YAML reader that needs no third-party package.

Layout the helpers assume (see docs/skill-pattern.md):

  skills/<name>/            the Agent Skills folder that ships (SKILL.md + supporting files)
  tests/<name>/config.yaml  validation and eval settings for the skill
  tests/<name>/scenarios/   acceptance scenarios
  planning/<name>/          design documents

Command line:

  python3 scripts/skillrepo.py list
  python3 scripts/skillrepo.py config <skill> [dotted.key]
  python3 scripts/skillrepo.py catalog                  # Markdown table of every skill
  python3 scripts/skillrepo.py sync [--check]           # README catalogue + marketplace entries from SKILL.md
  python3 scripts/skillrepo.py plan-eval [--skill S] [--scenario X] [--changed-from FILE]

The repository has one version (``version`` in .claude-plugin/marketplace.json,
tagged vX.Y.Z); skills are not versioned individually.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
TESTS_DIR = ROOT / "tests"
PLANNING_DIR = ROOT / "planning"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CATALOG_START = "<!-- catalog:start -->"
CATALOG_END = "<!-- catalog:end -->"

# Files that may sit inside a skill folder for humans and are never read by the
# model (not referenced from SKILL.md). They are exempt from the model-facing checks.
HUMAN_FILES = ("README.md",)

DEFAULT_CONFIG: dict = {
    "validate": {
        "max_skill_lines": 150,
        "max_reference_lines": 400,
        # Markdown file inside the skill whose "## N" headings define the
        # "doc § N" sections scenarios may cite. Empty disables the check.
        "section_template": "",
    },
    "eval": {
        # Folder (relative to the project) where the skill writes its output.
        "output_dir": "",
        # File inside output_dir the judge reads in full; others are listed.
        "primary_document": "",
        # Regex for the IDs of questions the skill may ask (questions.log, answers.yaml).
        "question_id_pattern": r"Q\d{1,2}",
        # Scenario whose output other scenarios are diffed against, and the
        # scenario-name prefixes that need the diff.
        "baseline": {"scenario": "", "for": []},
        # Scenario the release workflow runs as a blocking gate.
        "release_scenario": "",
        # Extra answer files that rerun a scenario under another label.
        "variants": [],
    },
}


# --------------------------------------------------------------------------- #
# YAML subset reader
# --------------------------------------------------------------------------- #


class YamlError(ValueError):
    pass


def load_yaml(text: str) -> dict:
    """Parse the YAML subset used by config.yaml, answers.yaml and profiles.

    Uses PyYAML when importable; otherwise a small indentation-based parser that
    understands nested mappings, lists of scalars or mappings, quoted strings,
    inline lists/maps and ``|``/``>`` block scalars.
    """
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except ImportError:
        pass
    except Exception as exc:  # pragma: no cover - PyYAML present but file broken
        raise YamlError(str(exc)) from exc
    return _MiniYaml(text).parse()


class _MiniYaml:
    def __init__(self, text: str) -> None:
        self.lines = [ln.rstrip("\n") for ln in text.splitlines()]
        self.i = 0

    def parse(self) -> dict:
        value = self._parse_block(0)
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise YamlError("top level must be a mapping")
        return value

    def _peek(self):
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                self.i += 1
                continue
            return len(raw) - len(raw.lstrip(" ")), raw
        return None

    def _parse_block(self, indent: int):
        nxt = self._peek()
        if nxt is None:
            return None
        ind, raw = nxt
        if ind < indent:
            return None
        if raw.lstrip().startswith("- "):
            return self._parse_list(ind)
        return self._parse_map(ind)

    def _parse_list(self, indent: int) -> list:
        items: list = []
        while True:
            nxt = self._peek()
            if nxt is None or nxt[0] != indent or not nxt[1].lstrip().startswith("- "):
                break
            self.i += 1
            body = nxt[1].lstrip()[2:].strip()
            if body == "":
                items.append(self._parse_block(indent + 2))
            elif ":" in body and not body.startswith(("'", '"', "[", "{")):
                self.lines[self.i - 1] = " " * (indent + 2) + body
                self.i -= 1
                items.append(self._parse_map(indent + 2))
            else:
                items.append(self._scalar(body))
        return items

    def _parse_map(self, indent: int) -> dict:
        result: dict = {}
        while True:
            nxt = self._peek()
            if nxt is None or nxt[0] != indent:
                if nxt is not None and nxt[0] > indent:
                    raise YamlError(f"line {self.i + 1}: unexpected indentation")
                break
            stripped = nxt[1].strip()
            m = re.match(r"^([^:#][^:]*?)\s*:(?:\s+(.*))?$", stripped)
            if not m:
                raise YamlError(f"line {self.i + 1}: expected 'key: value'")
            key = m.group(1).strip().strip("'\"")
            rest = (m.group(2) or "").strip()
            self.i += 1
            if rest == "":
                child = self._parse_block(indent + 1)
                result[key] = {} if child is None else child
            elif rest in ("|", ">", "|-", ">-"):
                result[key] = self._block_scalar(indent, fold=rest.startswith(">"))
            else:
                result[key] = self._scalar(rest)
        return result

    def _block_scalar(self, indent: int, fold: bool) -> str:
        chunk: list[str] = []
        base = None
        while self.i < len(self.lines):
            raw = self.lines[self.i]
            if raw.strip() == "":
                chunk.append("")
                self.i += 1
                continue
            ind = len(raw) - len(raw.lstrip(" "))
            if ind <= indent:
                break
            if base is None:
                base = ind
            chunk.append(raw[base:])
            self.i += 1
        while chunk and chunk[-1] == "":
            chunk.pop()
        return (" ".join(chunk) if fold else "\n".join(chunk)) + "\n"

    @staticmethod
    def _scalar(text: str):
        if text.startswith(("'", '"')):
            quote = text[0]
            end = text.find(quote, 1)
            if end != -1:
                return text[1:end]
        if " #" in text:
            text = text.split(" #")[0].rstrip()
        if text.startswith("[") and text.endswith("]"):
            inner = text[1:-1].strip()
            return [] if not inner else [_MiniYaml._scalar(x.strip()) for x in inner.split(",")]
        if text.startswith("{") and text.endswith("}"):
            inner = text[1:-1].strip()
            out: dict = {}
            for pair in filter(None, (p.strip() for p in inner.split(","))):
                k, _, v = pair.partition(":")
                out[k.strip().strip("'\"")] = _MiniYaml._scalar(v.strip())
            return out
        low = text.lower()
        if low in ("true", "yes"):
            return True
        if low in ("false", "no"):
            return False
        if low in ("null", "~"):
            return None
        if re.fullmatch(r"-?\d+", text):
            return int(text)
        if re.fullmatch(r"-?\d+\.\d+", text):
            return float(text)
        return text


# --------------------------------------------------------------------------- #
# Skills and their configuration
# --------------------------------------------------------------------------- #


def list_skills(root: Path = ROOT) -> list[str]:
    """Names of every folder under skills/ that holds a SKILL.md."""
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def skill_dir(name: str, root: Path = ROOT) -> Path:
    return root / "skills" / name


def tests_dir(name: str, root: Path = ROOT) -> Path:
    return root / "tests" / name


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(name: str, root: Path = ROOT) -> dict:
    """The skill's tests/<name>/config.yaml merged over DEFAULT_CONFIG."""
    path = tests_dir(name, root) / "config.yaml"
    data: dict = {}
    if path.exists():
        data = load_yaml(path.read_text(encoding="utf-8"))
    cfg = _merge(DEFAULT_CONFIG, data)
    cfg["skill"] = name
    return cfg


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Return (mapping, line_of_closing_fence). Mapping is empty when absent."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fm: dict[str, str] = {}
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return fm, idx + 1
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", lines[idx])
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("'\"")
    return fm, 0


def frontmatter(name: str, root: Path = ROOT) -> dict[str, str]:
    path = skill_dir(name, root) / "SKILL.md"
    if not path.exists():
        return {}
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8").splitlines())
    return fm


def marketplace(root: Path = ROOT) -> dict:
    path = root / ".claude-plugin" / "marketplace.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def marketplace_entry(name: str, root: Path = ROOT) -> dict | None:
    for entry in marketplace(root).get("plugins") or []:
        if entry.get("name") == name:
            return entry
    return None


def scenario_names(name: str, root: Path = ROOT) -> list[str]:
    scen = tests_dir(name, root) / "scenarios"
    if not scen.exists():
        return []
    return sorted(p.name for p in scen.iterdir() if p.is_dir())


def resolve_scenario(name: str, ref: str, root: Path = ROOT) -> str | None:
    """Full scenario directory name from a name or an ID prefix such as S02."""
    names = scenario_names(name, root)
    if ref in names:
        return ref
    matches = [n for n in names if n.startswith(ref + "-")]
    return matches[0] if len(matches) == 1 else None


# --------------------------------------------------------------------------- #
# Eval planning (used by .github/workflows/eval.yml)
# --------------------------------------------------------------------------- #


def changed_scenarios(name: str, changed: list[str], root: Path = ROOT) -> list[str]:
    """Scenarios of one skill affected by a list of changed paths.

    Everything under the skill folder, the skill's judge prompt or preamble, and
    the shared runner put every scenario under test; otherwise only the scenarios
    whose own folder changed.
    """
    all_names = scenario_names(name, root)
    prefix_all = (
        f"skills/{name}/",
        f"tests/{name}/judge-prompt.md",
        f"tests/{name}/preamble.md",
        f"tests/{name}/config.yaml",
        "scripts/run-scenario.sh",
        "scripts/grade-scenario.py",
        "scripts/skillrepo.py",
        "scripts/install.sh",
    )
    picked: set[str] = set()
    for path in changed:
        p = path.replace("\\", "/")
        if p.startswith(prefix_all):
            return all_names
        m = re.match(rf"^tests/{re.escape(name)}/scenarios/([^/]+)/", p)
        if m and m.group(1) in all_names:
            picked.add(m.group(1))
    return sorted(picked)


def plan_eval(skill: str | None, scenario: str | None, changed: list[str] | None, root: Path = ROOT) -> dict:
    """Matrix entries for the eval workflow.

    Returns {"runs": [...], "baselines": [...]} where every item has ``skill``,
    ``scenario``, ``answers`` and ``label``. A baseline scenario is pulled out of
    ``runs`` and listed under ``baselines`` whenever a selected run is diffed
    against it, so it runs first and exactly once.
    """
    runs: list[dict] = []
    baselines: list[dict] = []
    for name in list_skills(root):
        if skill and skill != "all" and name != skill:
            continue
        cfg = load_config(name, root)["eval"]
        if changed is not None:
            names = changed_scenarios(name, changed, root)
        elif scenario and scenario != "all":
            full = resolve_scenario(name, scenario, root)
            names = [full] if full else []
        else:
            names = scenario_names(name, root)
        base = cfg["baseline"].get("scenario") or ""
        base_for = tuple(cfg["baseline"].get("for") or [])
        needs_base = bool(base) and (base in names or (bool(base_for) and any(n.startswith(base_for) for n in names)))
        for n in names:
            if needs_base and n == base:
                continue
            runs.append({"skill": name, "scenario": n, "answers": "answers.yaml", "label": n})
            for variant in cfg.get("variants") or []:
                if variant.get("scenario") == n:
                    runs.append(
                        {
                            "skill": name,
                            "scenario": n,
                            "answers": variant.get("answers", "answers.yaml"),
                            "label": f"{n}-{variant.get('suffix', 'variant')}",
                        }
                    )
        if needs_base:
            baselines.append({"skill": name, "scenario": base, "answers": "answers.yaml", "label": base})
    return {"runs": runs, "baselines": baselines}


# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #


def catalog_rows(root: Path = ROOT) -> list[dict]:
    return [{"name": n, "description": frontmatter(n, root).get("description", "")} for n in list_skills(root)]


def catalog_table(root: Path = ROOT) -> str:
    out = ["| Skill | What it does |", "|---|---|"]
    for r in catalog_rows(root):
        desc = " ".join(r["description"].split()).replace("|", "\\|")
        out.append(f"| [`{r['name']}`](skills/{r['name']}/) | {desc} |")
    return "\n".join(out)


def _replace_block(text: str, start: str, end: str, block: str) -> str | None:
    a, b = text.find(start), text.find(end)
    if a == -1 or b == -1 or b < a:
        return None
    return text[: a + len(start)] + "\n" + block + "\n" + text[b:]


def synced_marketplace(root: Path = ROOT) -> dict:
    """The marketplace manifest with one entry per skill, descriptions taken from
    SKILL.md, every entry's version equal to the repository version, and no
    entry for a skill that no longer exists. Fields a maintainer set by hand
    (displayName, category, keywords, tags, ...) are kept."""
    data = marketplace(root)
    version = data.get("version") or data.get("metadata", {}).get("version") or "0.0.0"
    owner = (data.get("owner") or {}).get("name", "")
    repo_url = data.get("metadata", {}).get("repository", "")
    existing = {e.get("name"): e for e in data.get("plugins") or []}
    plugins = []
    for name in list_skills(root):
        fm = frontmatter(name, root)
        entry = dict(existing.get(name) or {})
        entry.setdefault("name", name)
        entry["source"] = "./"
        entry["skills"] = [f"./skills/{name}"]
        entry.setdefault("displayName", name.replace("-", " ").title())
        entry["version"] = version
        entry["description"] = " ".join(fm.get("description", "").split())
        entry.setdefault("author", {"name": owner})
        if repo_url:
            entry.setdefault("homepage", f"{repo_url}/tree/main/skills/{name}")
            entry.setdefault("repository", repo_url)
        entry.setdefault("license", data.get("metadata", {}).get("license", "MIT"))
        entry.setdefault("category", "engineering")
        entry.setdefault("keywords", ["skills"])
        entry.setdefault("tags", [])
        plugins.append(entry)
    data["plugins"] = plugins
    return data


def sync(root: Path = ROOT, write: bool = True) -> list[str]:
    """Bring README.md's catalogue block and marketplace.json in line with the
    skills on disk. Returns the names of files that were (or would be) changed."""
    changed: list[str] = []
    readme = root / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        new = _replace_block(text, CATALOG_START, CATALOG_END, catalog_table(root))
        if new is None:
            print(f"skillrepo: catalog markers not found in {readme}", file=sys.stderr)
        elif new != text:
            changed.append("README.md")
            if write:
                readme.write_text(new, encoding="utf-8")
    path = root / ".claude-plugin" / "marketplace.json"
    if path.exists():
        current = path.read_text(encoding="utf-8")
        new = json.dumps(synced_marketplace(root), indent=2, ensure_ascii=False) + "\n"
        if new != current:
            changed.append(".claude-plugin/marketplace.json")
            if write:
                path.write_text(new, encoding="utf-8")
    return changed


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _dig(data, dotted: str):
    for part in dotted.split("."):
        if isinstance(data, dict) and part in data:
            data = data[part]
        else:
            return None
    return data


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    c = sub.add_parser("config")
    c.add_argument("skill")
    c.add_argument("key", nargs="?")
    sub.add_parser("catalog")
    sy = sub.add_parser("sync")
    sy.add_argument("--check", action="store_true", help="exit 1 if anything is out of date, change nothing")
    p = sub.add_parser("plan-eval")
    p.add_argument("--skill", default="all")
    p.add_argument("--scenario", default="all")
    p.add_argument("--changed-from", type=Path, default=None, help="file with one changed path per line")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print("\n".join(list_skills()))
        return 0
    if args.cmd == "config":
        if args.skill not in list_skills():
            print(f"skillrepo: unknown skill '{args.skill}'", file=sys.stderr)
            return 1
        cfg = load_config(args.skill)
        value = _dig(cfg, args.key) if args.key else cfg
        if isinstance(value, str):
            print(value)
        else:
            print(json.dumps(value, indent=2))
        return 0
    if args.cmd == "catalog":
        print(catalog_table())
        return 0
    if args.cmd == "sync":
        changed = sync(write=not args.check)
        for name in changed:
            print(("stale: " if args.check else "updated: ") + name)
        if not changed:
            print("catalogue and marketplace are up to date")
        return 1 if (args.check and changed) else 0
    if args.cmd == "plan-eval":
        changed = None
        if args.changed_from is not None:
            changed = [ln.strip() for ln in args.changed_from.read_text(encoding="utf-8").splitlines() if ln.strip()]
        print(json.dumps(plan_eval(args.skill, args.scenario, changed)))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
