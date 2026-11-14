# Host adapters

Every skill in this repository is host-agnostic: `../skills/<name>/` is a plain
[Agent Skills](https://agentskills.io/specification) folder (a `SKILL.md` with
`name` and `description` frontmatter plus supporting files), and it runs
unchanged inside any host that loads that format. An **adapter** is a tiny
host-specific wrapper that points at the shared folder and adds whatever the
host needs on top. The skill body is never copied into an adapter, and nothing
in this directory is specific to one skill: `../scripts/install.sh --skill <name>`
generates every pointer line and snippet from the skill's own frontmatter.

| Adapter | What it holds |
|---|---|
| [`claude/`](claude/README.md) | Install via the repository marketplace or by copy; the `disable-model-invocation` overlay |
| [`codex/`](codex/README.md) | Install path and the generated `AGENTS.md` pointer |
| [`copilot/`](copilot/README.md) | GitHub Copilot: `.github/skills/`, `/<name>` in the CLI and VS Code |
| [`gemini/`](gemini/README.md) | Gemini CLI: `.gemini/skills/`, activation by description |
| [`cursor/`](cursor/README.md) | Cursor: `.cursor/skills/`, plus an optional generated `.cursor/rules` file |
| [`kiro/`](kiro/README.md) | Kiro: `.kiro/skills/`, `skill://` resources for custom agents |
| [`agents/`](agents/README.md) | The shared `.agents/skills/` layout read by OpenCode, Amp, Goose, Roo Code, Windsurf/Devin and most other hosts |
| [`sdk/`](sdk/README.md) | Loader samples for custom agents on the Claude Agent SDK and the OpenAI Agents SDK; the pattern applies to Google ADK, LangChain, Pydantic AI, Mastra and the Vercel AI SDK |

`../scripts/install.sh --skill <name> --host <claude|codex|copilot|gemini|cursor|kiro|agents|generic>`
performs the copy or link and prints how to invoke the skill on that host.

## Portability rules (H1–H8)

These rules keep every shared skill runnable on every host. `scripts/validate.py`
enforces H1, H3 and H4 mechanically; the rest are reviewed.

- **H1 Capability verbs, not tool names.** The skill body says "read the file", "search the repository", "measure the token count", "present the questions in one message and wait for the reply". It never names a host tool. Each host maps verbs to its own tools. The deny-list is `../scripts/host-tool-names.txt`.
- **H2 Single-context fallback.** Every step runs inline. Where a host can delegate to a sub-agent with its own context, the skill may use it and says "if the host can delegate, do X; otherwise do X inline". Correctness never depends on delegation.
- **H3 Frontmatter is the common subset.** Only `name` and `description` appear in the shared `SKILL.md`, plus the spec's optional `license`, `compatibility` and `metadata` when needed. Host-specific keys (invocation restrictions, allowed tools, model hints) live in the adapters, never in the shared file.
- **H4 Relative paths only.** Supporting files are referenced relative to `SKILL.md`, so the folder can live at any install path.
- **H5 External systems only through MCP or files.** A skill reaches outside the repository only through an MCP server the user has configured, or through files in the project. It works fully with files when no MCP server exists.
- **H6 Model-neutral writing.** Instructions rely on no model-specific prompt tricks; they use steps with completion criteria, disclosed reference, leading words and positive phrasing, which hold across models. The scenarios in `../tests/<name>/scenarios/` are the regression test.
- **H7 User-invocation is a host overlay.** Hosts express "only the user triggers this" differently or not at all: the Claude adapter adds `disable-model-invocation: true` on install; hosts without the concept expose the skill by name and description.
- **H8 No host-specific file layout assumptions.** A skill finds a project's existing agents, skills and prompts by asking for paths or by searching common layouts (`.claude/`, `.agents/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`), never by assuming one.

## Host facts and verification

Checked against each host's documentation on 2026-11-14. Items marked `verify:`
could not be confirmed from the docs and should be re-checked before a release.
`<name>` stands for any skill in `../skills/`.

| Host | Skills location | Invocation | Frontmatter beyond the spec | Source |
|---|---|---|---|---|
| Claude Code | `.claude/skills/<name>/SKILL.md` (project), `~/.claude/skills/<name>/` (user), `<plugin>/skills/<name>/SKILL.md` (plugin), `.claude/skills/` in a `--add-dir` folder | `/<name>` typed by the user, or model-invoked when the description matches | `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`; unknown keys are ignored silently | https://code.claude.com/docs/en/skills |
| Claude Code plugins | `.claude-plugin/marketplace.json` at the repository root; each entry has `source: "./"` and `skills: ["./skills/<name>"]`, so only that folder loads for that plugin | `/<name>:<name>` | marketplace.json needs `name`, `owner.name`, `plugins[]` with `name` and `source`; an entry accepts every plugin.json field | https://code.claude.com/docs/en/plugins/manifest-reference, https://code.claude.com/docs/en/plugins/marketplace-reference |
| Claude Code headless | `claude -p "<prompt>" --output-format json --permission-mode acceptEdits --allowedTools "Read,Write,Edit,Bash,Glob,Grep" --add-dir <path>`; `--json-schema` for structured output; a slash command goes inside the prompt string. `--bare` skips skill discovery, so it is not used for the scenario run | | | https://code.claude.com/docs/en/headless |
| OpenAI Codex | `.agents/skills/<name>/SKILL.md` in the working directory, parent dirs up to the repo root, or `~/.agents/skills/`; `/etc/codex/skills` for admins | `$<name>` in the prompt or `/skills` in the CLI; implicit when the description matches | `agents/openai.yaml` beside the skill with `policy: allow_implicit_invocation: false` disables implicit use | https://learn.chatgpt.com/docs/build-skills |
| Codex headless | `codex exec -C <dir> --sandbox workspace-write -a never --json -o <last-message-file> "<prompt>"`; `--skip-git-repo-check` outside a repo; `CODEX_API_KEY=<key>` for a single run. `--full-auto` is no longer supported. `verify:` `-m/--model` spelling | | | https://learn.chatgpt.com/docs/non-interactive-mode |
| GitHub Copilot | `.github/skills/<name>/SKILL.md` (also `.claude/skills/`, `.agents/skills/`); user `~/.copilot/skills/`, `~/.agents/skills/`; serves the coding agent, code review, CLI, app and VS Code | By description, or `/<name>` in the CLI and VS Code; `copilot skill add|list` | `disable-model-invocation`, `user-invocable` (VS Code), `license`, `allowed-tools` | https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills |
| Gemini CLI | `.gemini/skills/` (alias `.agents/skills/`); user `~/.gemini/skills/` (alias `~/.agents/skills/`) | By description via the `activate_skill` tool with a confirmation prompt; `/skills list|enable|disable|reload`; `gemini skills install <url>` | none documented | https://geminicli.com/docs/cli/skills/ |
| Gemini CLI headless | `gemini -p "<prompt>" -o json --approval-mode auto_edit` | | | https://geminicli.com/docs/cli/headless/ |
| Cursor | `.cursor/skills/<name>/SKILL.md` (also `.agents/skills/`, `.claude/skills/`, `.codex/skills/`, nested dirs); user `~/.cursor/skills/`, `~/.agents/skills/` | `/<name>` in Agent chat, by description, or as a Custom Mode; `/migrate-to-skills` converts rules | `disable-model-invocation`, `paths`, `icon`, `color`, `metadata` | https://cursor.com/docs/skills |
| Kiro | `.kiro/skills/<name>/SKILL.md`; user `~/.kiro/skills/` | `/<name>`, or by description; custom agents list `skill://<name>` in `resources` | none documented | https://kiro.dev/docs/skills/ |
| OpenCode, Amp, Goose, Roo Code, Windsurf/Devin | `.agents/skills/` and `~/.agents/skills/`, plus each host's own directory (see `agents/README.md`) | By description; OpenCode `@<name>`, Goose `/skills <name>`, Windsurf `/<name>` | none documented | per host, listed in `agents/README.md` |
| Google ADK | No directory: `load_skill_from_dir(<path>)` and `SkillToolset(skills=[...])` passed in the agent's `tools`; follows the Agent Skills spec | The agent's `load_skill` / `load_skill_resource` tools, by description | n/a | https://adk.dev/skills/ |
| Vercel AI SDK | No native loader; the official cookbook scans `.agents/skills`, injects names and descriptions into `instructions`, and adds a `loadSkill` tool | By description through the custom tool | n/a | https://ai-sdk.dev/cookbook/guides/agent-skills |
| Community `skills` CLI | `npx skills add Geenie-AI/skills --skill <name>` scans `skills/*/SKILL.md` and the paths declared in `.claude-plugin/marketplace.json`, and installs into the agents it detects (`-a <agent>`, `-g` for a global install) | per host | n/a | https://github.com/vercel-labs/skills (docs/creating-skills.md, checked 2026-11-14) |
| Agent Skills spec | `SKILL.md` + optional `scripts/`, `references/`, `assets/` | n/a | `name` 1–64 chars, lowercase `a-z 0-9 -`, equal to the directory; `description` 1–1024 chars; optional `license`, `compatibility` (≤ 500 chars), `metadata`, `allowed-tools`; validate with `skills-ref validate` | https://agentskills.io/specification |
| Any other host | Copy the folder anywhere | A pointer line in the host's always-on instructions, printed by `install.sh --host generic` | n/a | |
