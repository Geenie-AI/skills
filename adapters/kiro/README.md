# Kiro adapter

The shared skills live at `../../skills/<name>`. Kiro loads Agent Skills from
`.kiro/skills/<name>/SKILL.md` in the workspace and `~/.kiro/skills/` for the
user (workspace wins on a name clash). Checked 2026-11-14 against
https://kiro.dev/docs/skills/.

## Install

```bash
scripts/install.sh --skill <name> --host kiro --project    # .kiro/skills/<name>
scripts/install.sh --skill <name> --host kiro --user       # ~/.kiro/skills/<name>
```

## Invoke

Type `/<name> <request>` or let Kiro pick the skill from its description. A
custom Kiro agent must list the skill in its `resources` as `skill://<name>` to
reach it.

Always-on guidance belongs in `.kiro/steering/*.md` or `AGENTS.md`; the skill
stays on demand.
