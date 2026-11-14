# `.agents/skills` adapter (OpenCode, Amp, Goose, Roo Code, Windsurf/Devin, and others)

The shared skills live at `../../skills/<name>`. Most hosts that implement the
Agent Skills format read the shared project directory
`.agents/skills/<name>/SKILL.md` and the user directory `~/.agents/skills/`.
Installing there once serves every one of them; Codex, Copilot, Gemini CLI and
Cursor read it too. Checked 2026-11-14 against each host's docs.

## Install

```bash
scripts/install.sh --skill <name> --host agents --project    # .agents/skills/<name>
scripts/install.sh --skill <name> --host agents --user       # ~/.agents/skills/<name>
```

## Per-host notes

| Host | Also reads | Invoke | Always-on file | Source |
|---|---|---|---|---|
| OpenCode | `.opencode/skills/`, `.claude/skills/`; global `~/.config/opencode/skills/` | `@<name>` in the prompt, or the model's `skill` tool by description | `AGENTS.md` | https://opencode.ai/docs/skills/ |
| Amp | `.claude/skills/`; global `~/.config/agents/skills/` (`amp skill add --global`) | By description; `reload_skills` rescans | `AGENTS.md` | https://ampcode.com/docs/customize/skills |
| Goose | `.goose/skills/`, `.claude/skills/`; global `~/.agents/skills/` | `/skills <name>` in the CLI, or by description | `.goosehints` | https://goose-docs.ai/docs/guides/context-engineering/using-skills/ |
| Roo Code | `.roo/skills/`, `~/.roo/skills/`, mode-specific `.roo/skills-<mode>/` | By description (Roo reads `SKILL.md` when it matches) | `.roo/rules/` | https://roocodeinc.github.io/Roo-Code/features/skills |
| Windsurf / Devin | `.devin/skills/` (primary), legacy `.windsurf/skills/`; global `~/.config/devin/skills/` | `/<name>`, or by description | `AGENTS.md`, `.devin/rules/` | https://docs.devin.ai/desktop/cascade/skills |

Hosts not listed here that follow https://agentskills.io read the same folder;
if one does not, use `scripts/install.sh --skill <name> --host generic` and add
the printed pointer line to its always-on instruction file.
