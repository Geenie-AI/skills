<p align="center">
  <a href="https://github.com/Geenie-AI"><img src="https://raw.githubusercontent.com/Geenie-AI/.github/main/profile/assets/geenie-ai-logo.png" alt="Geenie-AI logo" width="140"></a>
</p>

<h1 align="center">Geenie-AI skills</h1>

<p align="center">Agentic AI solutions for any platform and any programming language.</p>

<p align="center">
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml/badge.svg" alt="eval"></a>
  <a href="https://github.com/Geenie-AI/skills/releases/latest"><img src="https://img.shields.io/github/v/release/Geenie-AI/skills?display_name=tag&sort=semver" alt="latest release"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f" alt="Agent Skills compatible"></a>
  <a href="#install"><img src="https://img.shields.io/badge/Claude%20Code-marketplace-d97757" alt="Claude Code marketplace"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="license: MIT"></a>
</p>

<p align="center">
  <a href="RELEASES.md"><b>Release history</b></a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="LICENSE">License</a>
</p>

Portable agent skills, built and tested the same way. Each skill is a plain
folder in the open [Agent Skills](https://agentskills.io) format, so it runs
unchanged in Claude Code, OpenAI Codex, GitHub Copilot, Gemini CLI, Cursor,
Kiro, OpenCode, Amp, Goose, Roo Code, Windsurf and any custom agent built on
the Claude Agent SDK or the OpenAI Agents SDK. The repository supplies what a
single skill folder cannot: one installer for every host, static validation,
model-graded acceptance scenarios, per-skill releases, and a scaffold so the
next skill starts with all of it.

## Skills

<!-- catalog:start -->
| Skill | What it does |
|---|---|
| [`agentic-architect`](skills/agentic-architect/) | Designs a new agentic solution or diagnoses and improves an existing one (a prompt, a skill set, a skill-to-agent assignment, an agent, the knowledge layer, or a whole system) for Claude Code, Claude Agent SDK, Claude API, OpenAI Agents SDK, OpenAI Responses API, Codex, or a generic framework, following OpenAI's Optimizing LLM Accuracy method. Use when asked to design, architect, review, optimize, or fix prompts, skills, agents, retrieval, or multi-agent pipelines, or when a pipeline hallucinates, ignores its schema, or needs an eval plan. |
<!-- catalog:end -->

The table is generated from each skill's `SKILL.md` description by the
`catalog` workflow; edit the description, not the table. Each skill's own
README covers what it does, how to invoke it, and its latest scenario eval
results.

## Install

Replace `<name>` with a skill from the table.

| Platform | Install | Invoke |
|---|---|---|
| **Claude Code** (plugin) | `claude plugin marketplace add Geenie-AI/skills` then `claude plugin install <name>@geenie-ai-skills` | `/<name>:<name> <request>` |
| **Claude Code** (copy, user-invoked only) | `scripts/install.sh --skill <name> --host claude --project` (the copy gains `disable-model-invocation`) | `/<name> <request>` |
| **Claude Agent SDK** | Keep the folder under `.claude/skills/` with `setting_sources` including `project`, or use the loader in [`adapters/sdk/`](adapters/sdk/) | By description, or prefix the request with the skill |
| **OpenAI Codex** | `scripts/install.sh --skill <name> --host codex --project` (`.agents/skills/`); the printed `AGENTS.md` line is optional | `$<name> <request>`, or `/skills` in the CLI |
| **OpenAI Agents SDK** | Loader in [`adapters/sdk/`](adapters/sdk/): `SKILL.md` becomes the instructions, a `read_skill_file` tool serves the reference files | Pass the request to the agent |
| **GitHub Copilot** | `scripts/install.sh --skill <name> --host copilot --project` (`.github/skills/`), or `copilot skill add skills/<name>` | `/<name>` in the CLI or VS Code, or by description |
| **Gemini CLI** | `scripts/install.sh --skill <name> --host gemini --project` (`.gemini/skills/`), or `gemini skills install <dir>` | By description; Gemini asks you to confirm |
| **Cursor** | `scripts/install.sh --skill <name> --host cursor --project` (`.cursor/skills/`); add `--rule` for a `.cursor/rules` file | `/<name>` in Agent chat, by description, or as a Custom Mode |
| **Kiro** | `scripts/install.sh --skill <name> --host kiro --project` (`.kiro/skills/`) | `/<name>`; custom agents add `skill://<name>` |
| **OpenCode, Amp, Goose, Roo Code, Windsurf/Devin** and other Agent Skills hosts | `scripts/install.sh --skill <name> --host agents --project` (`.agents/skills/`, read by all of them) | By description; OpenCode `@<name>`, Goose `/skills <name>`, Windsurf `/<name>` |
| **Community `skills` CLI** | `npx skills add Geenie-AI/skills --skill <name>` (`-g` for a global install, `-a <agent>` to target one agent) | Per host |
| **Google ADK, Vercel AI SDK, LangChain, Pydantic AI, Mastra, CrewAI, others** | Read `SKILL.md` into the agent's instructions and expose the folder through a small read-file tool, as the [`adapters/sdk/`](adapters/sdk/) samples do | Pass the request to the agent |
| **Anything else** | `scripts/install.sh --skill <name> --host generic` prints a pointer line for the host's always-on instruction file | The host reads `SKILL.md` |

Paths and commands were verified against each host's documentation on
2026-11-14 and are listed with their sources in [`adapters/README.md`](adapters/README.md).

## How every skill is built

The full contract is in [`docs/skill-pattern.md`](docs/skill-pattern.md). In short:

- **One skill, three folders.** `skills/<name>/` is the Agent Skills folder that ships. `tests/<name>/` holds the skill's eval settings, judge prompt and acceptance scenarios. `planning/<name>/` holds the design documents it was built from. Nothing about a skill lives anywhere else.
- **Written for agents.** `SKILL.md` is numbered steps with a "Done when" line each, a short vocabulary of leading words, and capability verbs instead of host tool names. Rules live in reference files loaded on demand, each with an ID that the steps, the scenarios and the validator share.
- **Host-neutral by rule.** The portability rules H1–H8 in [`adapters/README.md`](adapters/README.md) are enforced by the validator where they can be, so one source folder runs everywhere; per-host details are generated from the skill's own description.
- **Tested two ways.** `scripts/validate.py` checks structure without a model on every push. `scripts/run-scenario.sh` runs a scenario through a real host headlessly and has the host's model grade the result against expected checks; the eval workflow does that weekly and on pull requests.
- **Released together.** The repository has one version and one changelog grouped by skill; running the `release` workflow on `main` tags the marketplace version `vX.Y.Z`, validates every skill, runs the selected release scenarios, and publishes a zip per skill; [`RELEASES.md`](RELEASES.md) records each tag's scenario results. The Claude Code marketplace at the repository root lists every skill as a plugin, with entries generated from the same descriptions as the catalogue.

## Repository layout

```
skills/<name>/          the shipped skill folder (SKILL.md, reference/, templates/, README.md)
tests/<name>/           config.yaml, preamble.md, judge-prompt.md, scenarios/
planning/<name>/        design documents
adapters/               host overlays, portability rules, verified host facts, SDK loader samples
scripts/                install.sh, validate.py, run-scenario.sh, grade-scenario.py, eval-report.py,
                        changelog-section.py, release-history.py, new-skill.sh, skillrepo.py (shared helpers)
template/               scaffold for a new skill
docs/                   skill-pattern.md, testing.md, releasing.md
.claude-plugin/         marketplace.json (one plugin entry per skill)
.github/workflows/      validate.yml, catalog.yml, eval.yml + scenario-host.yml, release.yml
```

## Developing

```bash
python3 scripts/validate.py                                        # every skill, no model needed
scripts/run-scenario.sh --skill agentic-architect --host claude --scenario S02    # one scenario on Claude Code
scripts/new-skill.sh my-skill                                      # scaffold a new skill
python3 scripts/skillrepo.py sync                                  # regenerate the catalogue and marketplace entries
```

The tooling is Python 3 standard library plus bash 3.2-compatible shell; no
dependencies to install. Scenario runs need the host's CLI (`claude` or
`codex`) signed in; in CI, Claude Code authenticates with the run's GitHub
OIDC token through Anthropic's Workload Identity Federation, so the
repository stores no Anthropic key.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for what a change needs,
[`docs/testing.md`](docs/testing.md) for the scenario harness, and
[`docs/releasing.md`](docs/releasing.md) for tags and versions.

## License

[MIT](LICENSE).
