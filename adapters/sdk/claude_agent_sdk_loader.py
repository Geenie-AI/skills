"""Load one of this repository's skills into a Claude Agent SDK agent.

    pip install claude-agent-sdk
    python adapters/sdk/claude_agent_sdk_loader.py <skill-name> "<request for the skill>"

SKILL.md becomes the appended system prompt; `read_skill_file` serves the
skill's reference files on demand. Set SKILL_DIR to use a skill folder outside
this repository. Checked against https://code.claude.com/docs/en/agent-sdk/python
on 2026-11-14.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

REPO_ROOT = Path(__file__).resolve().parents[2]


def skill_dir(name: str) -> Path:
    override = os.environ.get("SKILL_DIR")
    path = Path(override).resolve() if override else (REPO_ROOT / "skills" / name).resolve()
    if not (path / "SKILL.md").exists():
        sys.exit(f"no SKILL.md under {path}")
    return path


def load_skill_body(path: Path) -> str:
    text = (path / "SKILL.md").read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, rest = text.partition("\n---\n")  # drop the frontmatter block
        text = rest
    return text.strip()


def resolve_inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if root not in candidate.parents and candidate != root:
        raise ValueError(f"path escapes the skill folder: {relative}")
    return candidate


def build_options(name: str) -> ClaudeAgentOptions:
    path = skill_dir(name)

    @tool(
        "read_skill_file",
        f"Read a file that the {name} skill references by relative path, "
        "for example reference/<file>.md or templates/<file>.md.",
        {"path": str},
    )
    async def read_skill_file(args: dict[str, Any]) -> dict[str, Any]:
        try:
            body = resolve_inside(path, args["path"]).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            return {"content": [{"type": "text", "text": f"error: {exc}"}], "is_error": True}
        return {"content": [{"type": "text", "text": body}]}

    skill_server = create_sdk_mcp_server(name="skill", version="1.0.0", tools=[read_skill_file])
    preamble = (
        f"You are running the {name} skill. When the skill says to read one of its files, "
        "call the read_skill_file tool with that relative path. Treat the current working "
        "directory as the user's project and write output files where the skill says, "
        "relative to it.\n\n"
    )
    return ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code", "append": preamble + load_skill_body(path)},
        mcp_servers={"skill": skill_server},
        allowed_tools=["mcp__skill__read_skill_file", "Read", "Write", "Edit", "Glob", "Grep"],
        permission_mode="acceptEdits",
        cwd=os.getcwd(),
    )


async def main(name: str, request: str) -> None:
    async for message in query(prompt=request, options=build_options(name)):
        # ResultMessage carries the final text; print everything else compactly.
        result = getattr(message, "result", None)
        if result:
            print(result)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: claude_agent_sdk_loader.py <skill-name> "<request for the skill>"')
    asyncio.run(main(sys.argv[1], " ".join(sys.argv[2:])))
