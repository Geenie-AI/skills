"""Load one of this repository's skills into an OpenAI Agents SDK agent.

    pip install openai-agents
    python adapters/sdk/openai_agents_loader.py <skill-name> "<request for the skill>"

SKILL.md becomes the agent's instructions; `read_skill_file` serves the skill's
reference files on demand; `read_project_file` and `write_file` give the skill
file access inside the current working directory (the Agents SDK has no
built-in file tools). Set SKILL_DIR to use a skill folder outside this repository.

verify: import names against https://openai.github.io/openai-agents-python/tools/
(the decorator is documented as `function_tool`; some pages show `agents.decorators.tool`).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agents import Agent, Runner, function_tool

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path.cwd().resolve()


def skill_dir(name: str) -> Path:
    override = os.environ.get("SKILL_DIR")
    path = Path(override).resolve() if override else (REPO_ROOT / "skills" / name).resolve()
    if not (path / "SKILL.md").exists():
        sys.exit(f"no SKILL.md under {path}")
    return path


def load_skill_body(path: Path) -> str:
    text = (path / "SKILL.md").read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, rest = text.partition("\n---\n")
        text = rest
    return text.strip()


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError(f"path escapes {root.name}: {relative}")
    return candidate


def build_agent(name: str) -> Agent:
    path = skill_dir(name)

    @function_tool
    def read_skill_file(rel_path: str) -> str:
        """Read a file the skill references by relative path, e.g. reference/<file>.md."""
        try:
            return _inside(path, rel_path).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            return f"error: {exc}"

    @function_tool
    def read_project_file(rel_path: str) -> str:
        """Read a file from the user's project by relative path."""
        try:
            return _inside(PROJECT_DIR, rel_path).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            return f"error: {exc}"

    @function_tool
    def write_file(rel_path: str, content: str) -> str:
        """Write a file inside the user's project (path relative to the project root)."""
        try:
            target = _inside(PROJECT_DIR, rel_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"wrote {target.relative_to(PROJECT_DIR)}"
        except (OSError, ValueError) as exc:
            return f"error: {exc}"

    preamble = (
        f"You are running the {name} skill. When the skill says to read one of its files, "
        "call read_skill_file with that relative path. Use read_project_file to inspect the "
        "user's project and write_file to emit every output file where the skill says, "
        "relative to the project root.\n\n"
    )
    return Agent(
        name=name,
        instructions=preamble + load_skill_body(path),
        tools=[read_skill_file, read_project_file, write_file],
    )


def main(name: str, request: str) -> None:
    result = Runner.run_sync(build_agent(name), request)
    print(result.final_output)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: openai_agents_loader.py <skill-name> "<request for the skill>"')
    main(sys.argv[1], " ".join(sys.argv[2:]))
