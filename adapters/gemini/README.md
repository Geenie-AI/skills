# Gemini CLI adapter

The shared skills live at `../../skills/<name>`. Gemini CLI loads Agent
Skills from `.gemini/skills/<name>/SKILL.md` in the workspace (alias
`.agents/skills/`) and from `~/.gemini/skills/` (alias `~/.agents/skills/`) for
the user. Checked 2026-11-14 against https://geminicli.com/docs/cli/skills/
and https://geminicli.com/docs/cli/cli-reference/.

## Install

```bash
scripts/install.sh --skill <name> --host gemini --project    # .gemini/skills/<name>
scripts/install.sh --skill <name> --host gemini --user       # ~/.gemini/skills/<name>
gemini skills list                                           # confirm it is discovered
```

`gemini skills install <git-url-or-dir> --scope workspace` is the CLI's own
installer and accepts a clone of this repository's `skills/<name>` folder.

## Invoke

Gemini CLI injects every skill's name and description into the session; when a
request matches, the model calls its `activate_skill` tool and asks you to
confirm, then loads `SKILL.md` and the folder tree. There is no `/<name>`
invocation; describe the task and confirm the activation.
`/skills enable|disable <name>` toggles it; `/skills reload` rescans after an
update.

Headless: `gemini -p "<request>" --approval-mode auto_edit -o json` runs the
request non-interactively; the skill still activates by description.

`GEMINI.md` holds always-on workspace context; keep the skill out of it.
