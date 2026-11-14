# OpenAI Codex adapter

The shared skills live at `../../skills/<name>`. Codex reads the same Agent
Skills format, so the folder is copied unchanged.

## Install

```bash
scripts/install.sh --skill <name> --host codex --user       # ~/.agents/skills/<name>
scripts/install.sh --skill <name> --host codex --project    # ./.agents/skills/<name>
```

Codex discovers skills in `.agents/skills/<name>/SKILL.md` in the working
directory and in each parent directory up to the repository root, in
`~/.agents/skills/` for the user, and in `/etc/codex/skills` for administrators.

## Invoke

- Explicitly: type `$<name>` in the prompt, or pick it from `/skills` in the CLI.
- Implicitly: Codex may select the skill when the request matches its description. To make it explicit-only (the equivalent of the Claude overlay), add `agents/openai.yaml` beside the installed `SKILL.md` with `policy: allow_implicit_invocation: false`.

## AGENTS.md pointer

Codex does not need a pointer to find an installed skill, but an `AGENTS.md`
line tells it when to reach for this one. The install script prints the line,
generated from the skill's description:

```markdown
## Skills

- `<name>` (`.agents/skills/<name>/SKILL.md`): use it, or let the user invoke it with `$<name>`, when the request matches: <description>
```

## Headless use

```bash
codex exec -C . --sandbox workspace-write -a never --json -o last.md \
  "Use the \$<name> skill. <request>"
```

`--skip-git-repo-check` is needed outside a git repository. `CODEX_API_KEY=<key>`
sets the key for one run. `--full-auto` is no longer supported.

Docs: https://learn.chatgpt.com/docs/build-skills, https://learn.chatgpt.com/docs/non-interactive-mode, https://learn.chatgpt.com/docs/agent-configuration/agents-md (checked 2026-11-14). `verify:` the `-m/--model` flag spelling for `codex exec`.
