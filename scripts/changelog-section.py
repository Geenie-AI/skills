#!/usr/bin/env python3
"""Print one version's section of the root CHANGELOG.md (keep-a-changelog format).

Usage:
  python3 scripts/changelog-section.py 0.1.0        # body of ## [0.1.0]
  python3 scripts/changelog-section.py v0.1.0       # leading 'v' is stripped
  python3 scripts/changelog-section.py --unreleased # body of ## [Unreleased]

Exit status 1 when the section is missing or empty, so release.yml fails
before publishing an empty release.
"""

from __future__ import annotations

import sys
from pathlib import Path


def section(changelog: Path, version: str) -> list[str]:
    wanted = f"## [{version}]".lower()
    out: list[str] = []
    inside = False
    for line in changelog.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = line.lower().startswith(wanted)
            continue
        if inside:
            out.append(line)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    changelog = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
    if not changelog.exists():
        print("CHANGELOG.md not found", file=sys.stderr)
        return 1
    version = "Unreleased" if argv[0] == "--unreleased" else argv[0].lstrip("v")
    body = section(changelog, version)
    if not any(ln.strip() and not ln.startswith("#") for ln in body):
        print(f"CHANGELOG.md has no content for [{version}]", file=sys.stderr)
        return 1
    print("\n".join(body))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
