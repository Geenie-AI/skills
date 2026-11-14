# GitHub Copilot adapter

The shared skills live at `../../skills/<name>`. Copilot loads Agent Skills
from `.github/skills/<name>/SKILL.md` in the repository (it also reads
`.claude/skills/` and `.agents/skills/`) and from `~/.copilot/skills/` or
`~/.agents/skills/` for the user. The same folder serves the Copilot coding
agent, code review, the Copilot CLI, the Copilot app and VS Code agent mode.
Checked 2026-11-14 against
https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
and https://code.visualstudio.com/docs/copilot/customization/agent-skills.

## Install

```bash
scripts/install.sh --skill <name> --host copilot --project    # .github/skills/<name>
scripts/install.sh --skill <name> --host copilot --user       # ~/.copilot/skills/<name>
```

Or in the Copilot CLI: `copilot skill add skills/<name>` after cloning.

## Invoke

- Copilot selects the skill from its description when the request matches.
- Copilot CLI and VS Code: start the prompt with `/<name>` to force it.
- Frontmatter accepted beyond the spec: `disable-model-invocation: true` makes
  the skill slash-only in VS Code; `user-invocable: false` hides it from the `/`
  menu. Neither is set in the shared files; add them to the copy if wanted.

Always-on repository guidance belongs in `.github/copilot-instructions.md` or
`AGENTS.md`; the skill stays on demand.
