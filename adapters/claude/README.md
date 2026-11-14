# Claude Code adapter

The shared skills live at `../../skills/<name>`. This adapter adds nothing to
any skill body; it documents the two install paths and the one frontmatter key
Claude Code understands that the shared files leave out.

## Install as a plugin (marketplace)

The repository root is a marketplace (`.claude-plugin/marketplace.json`) with
one plugin entry per skill. Each entry has `source: "./"` and
`skills: ["./skills/<name>"]`, which makes Claude Code load only that folder
for that plugin.

```bash
claude plugin marketplace add Geenie-AI/skills
claude plugin install <name>@geenie-ai-skills
```

Inside a session the skill is `/<name>:<name>` (plugin skills carry the plugin
name as a prefix). Every entry carries the repository version; updates arrive
when a release (tag `vX.Y.Z`) bumps it.

The marketplace install uses the shared `SKILL.md` **as-is**: its frontmatter has
only `name` and `description`, so the skill is model-invocable and its
description sits in context on every turn (about a hundred tokens). If you want
the user-only behaviour, use the copy install below or disable the plugin's
automatic invocation with the `user-invocable` / `disable-model-invocation`
settings documented at https://code.claude.com/docs/en/skills.

## Install by copying (user-invoked only)

```bash
scripts/install.sh --skill <name> --host claude --user       # ~/.claude/skills/<name>
scripts/install.sh --skill <name> --host claude --project    # ./.claude/skills/<name>
```

The script copies the folder (without the human-facing `README.md`) and
inserts one line into the **copy's** frontmatter:

```yaml
---
disable-model-invocation: true
name: <name>
description: ...
---
```

With that key the skill only runs when a person types `/<name>`, its
description stays out of context, and it is never preloaded into subagents
(rule H7). The source folder in this repository is never changed. `--link`
symlinks instead of copying and therefore keeps the shared frontmatter.

## Overlay contents

| Where | What |
|---|---|
| `/.claude-plugin/marketplace.json` | Marketplace manifest: one entry per skill, each pointing at `./skills/<name>`, generated from the skill's description by `scripts/skillrepo.py sync` |
| `scripts/install.sh --host claude` | Copy install plus the `disable-model-invocation: true` line |

## Headless use

```bash
claude -p "/<name> <request>" \
  --output-format json --permission-mode acceptEdits \
  --allowedTools "Read,Write,Edit,Glob,Grep"
```

The scenario runner (`scripts/run-scenario.sh --skill <name> --host claude`)
uses this form with the skill installed into a temporary project. `--bare` is
not used for the run because it skips skill discovery.

Docs: https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/plugins/manifest-reference, https://code.claude.com/docs/en/plugins/marketplace-reference, https://code.claude.com/docs/en/headless (checked 2026-11-14).
