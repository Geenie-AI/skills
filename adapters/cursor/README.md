# Cursor adapter

The shared skills live at `../../skills/<name>`. Cursor loads Agent Skills
from `.cursor/skills/<name>/SKILL.md` in the project (also `.agents/skills/`,
`.claude/skills/`, `.codex/skills/`, and nested subdirectories) and from
`~/.cursor/skills/` or `~/.agents/skills/` for the user. Checked 2026-11-14
against https://cursor.com/docs/skills and https://cursor.com/docs/context/rules.

## Install

```bash
scripts/install.sh --skill <name> --host cursor --project    # .cursor/skills/<name>
scripts/install.sh --skill <name> --host cursor --user       # ~/.cursor/skills/<name>
```

## Invoke

- `/<name>` in the Agent chat attaches the skill for one message.
- Cursor also picks it from the description when the request matches.
- To run it as a mode for a whole session, choose it as a Custom Mode (Option/Alt+Enter).
- Frontmatter accepted beyond the spec: `disable-model-invocation: true`
  (slash-only), `paths` (globs that scope the skill). Neither is set in the
  shared files; add them to the copy if wanted.

## Optional rule

`rule.template.mdc` is a project-rule template (`alwaysApply: false`, selected
by description) that tells the agent to read the installed `SKILL.md`. It
predates Cursor's skills support and is kept for projects that pin behaviour
through `.cursor/rules/`; with the skill installed it is not needed.

```bash
scripts/install.sh --skill <name> --host cursor --project --rule   # also writes .cursor/rules/<name>.mdc
```
