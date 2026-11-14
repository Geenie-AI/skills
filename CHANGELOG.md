# Changelog

All notable changes to this repository are recorded here, grouped by skill
and by the shared tooling. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The repository has
one [semantic version](https://semver.org/), kept in
`.claude-plugin/marketplace.json` (`version`) and tagged `vX.Y.Z`; skills are
not versioned individually. MAJOR when a skill's inputs or the shape of what
it produces change incompatibly; MINOR when a skill, rule, scenario, target or
host overlay is added; PATCH for wording fixes that keep every scenario's
expected checks unchanged.

The Unreleased section must be non-empty on every pull request that touches a
model-facing file of any skill (checked by `scripts/validate.py --changed-files`).

## [Unreleased]

### agentic-architect

#### Fixed

- Changes template (template § 11): adds an example row for a hygiene
  change and a review-checklist item, so a change that fixes only audit
  rows carries `hygiene (no failure targeted)` (S08m check 7).

## [0.1.0] - 2026-11-14

### Repository

- Created from the stand-alone `agentic-architect` repository as the Geenie-AI
  skills collection. The install script, static validator, scenario runner,
  judge scoring, eval report, changelog helper, host adapters, SDK loaders and
  the GitHub workflows were generalised to serve every skill under `skills/`,
  driven by `tests/<name>/config.yaml` and `scripts/skillrepo.py`.
- `scripts/new-skill.sh` scaffolds a skill from `template/`; `docs/` describes
  the pattern every skill follows.
- One Claude Code marketplace (`geenie-ai-skills`) at the repository root with
  one plugin entry per skill. The README catalogue and the marketplace entries
  are generated from each skill's `SKILL.md` description by
  `scripts/skillrepo.py sync`, which the `catalog` workflow runs on `main`.
- One repository version and one changelog; releases are tagged `vX.Y.Z` and
  ship a zip per skill.
- Scenario evals default to Claude Code for every skill:
  `scripts/run-scenario.sh` no longer needs `--host`, and the `eval` workflow
  (weekly, pull-request and manual runs) runs Codex only when a manual run
  picks `codex` or `all`.
- CI authenticates to the Claude API with GitHub's OIDC token through
  Anthropic Workload Identity Federation (`.github/actions/anthropic-oidc`);
  no Anthropic API key is stored in the repository.
- Release history: the `release` workflow records each tag's scenario
  results in `RELEASES.md` (linked from the README) and appends them to the
  GitHub release body (`scripts/release-history.py`). Release scenarios are
  chosen per run (host, skill, scenario; default `claude`, `all`, `S08m`)
  instead of each skill's `eval.release_scenario`, which is removed.
  Failing release scenarios no longer stop the release: it is published
  marked as failing, with each failed check and the judge's reason, a
  `scenario-results-<tag>.zip` asset and links to the workflow artifact
  and run; the run still ends red.

### agentic-architect

First release, built from the design in `planning/agentic-architect/`.

#### Added

- The host-neutral skill at `skills/agentic-architect/`: `SKILL.md` with the
  four steps (intake, diagnose, design, emit), each with a completion criterion.
- Reference files: layers and scope (scopes `prompt`, `skill`,
  `skill-assignment`, `agent`, `knowledge`, `system`; rules SC1–SC8 and
  AS1–AS6), the fixed intake question set Q1–Q26 with the derive-first asking
  policy, the decision framework (two axes, lever order, gates, rejection
  rules), long-context and chain rules R4.1–R4.7 with the prompt audit
  P1–P12, retrieval design and failure grid, fine-tuning gates G6.1–G6.5,
  good-enough worksheets and handoff patterns.
- Emit targets: Claude (Claude Code, Agent SDK, Messages API), OpenAI (Agents
  SDK, Responses API, file search, fine-tuning) and generic, with the common
  emit rules E1–E8.
- Templates for `architecture.md` and the eval set; profile records with a
  resolution order, staleness window and external mappings.
- Host overlays under `adapters/` for Claude Code (marketplace and copy
  install), OpenAI Codex, Cursor, and SDK loaders for the Claude Agent SDK and
  OpenAI Agents SDK in Python and TypeScript.
- Tooling: `scripts/install.sh`, `scripts/validate.py` (static checks, no
  model), `scripts/run-scenario.sh` with `scripts/grade-scenario.py`
  (scenario evals), `scripts/changelog-section.py`.
- GitHub workflows: `validate.yml`, `eval.yml` (weekly and on request),
  `release.yml` (tag-driven packaging and release).
- Acceptance scenarios S1–S12 under `tests/agentic-architect/scenarios/` with
  the LLM-judge rubric.
- Scenario S08m-prompt-scope-mini: S08 with a ~5k-token policy excerpt in
  place of the generated 90k-token manual, and eight merged checks, for a
  cheaper smoke run of `prompt` scope.
- `scripts/eval-report.py` builds the scenario-eval summary; scheduled and
  manual eval runs write it into the "Scenario eval results" section at the
  bottom of the skill's README and commit it.
- Install support and adapter docs for GitHub Copilot (`.github/skills/`),
  Gemini CLI (`.gemini/skills/`), Cursor skills (`.cursor/skills/`), Kiro
  (`.kiro/skills/`) and the shared `.agents/skills/` layout read by OpenCode,
  Amp, Goose, Roo Code and Windsurf/Devin.
- `targets/generic-target.md`: parameter-name mapping for LangChain/LangGraph,
  CrewAI, AutoGen/AG2, Microsoft Agent Framework, Semantic Kernel, Pydantic
  AI, Mastra, LlamaIndex, Google ADK and the Vercel AI SDK, so generic
  artifacts use the named framework's own names.
- Q2 names the common frameworks the user may answer with.

#### Changed

- Moved into the Geenie-AI skills repository. The skill folder is now
  `skills/agentic-architect/`, its scenarios `tests/agentic-architect/`, its
  design documents `planning/agentic-architect/`; install, validation,
  scenario runner, adapters and workflows are shared with every skill and
  parameterised by `tests/agentic-architect/config.yaml`. Install with
  `scripts/install.sh --skill agentic-architect --host <host>` or
  `claude plugin install agentic-architect@geenie-ai-skills`.
- Scenario fixtures for profiles moved from `fixtures/profiles/` to
  `fixtures/repo/dot-agentic-architect/profiles/`, so the shared runner needs
  no skill-specific rule.
- `scripts/install.sh --host generic` prints the pointer line only unless
  `--dest` is given, and refuses a target inside this repository's `skills/`
  folder.
- Diagnosis (SKILL.md § 2, template § 5): an optimize run with no existing
  eval adds a `missing eval` row at L5 whose lever is a baseline eval of
  ≥ 20 items.
- Changes (SKILL.md § 3 step 5): when failures were supplied, every doc § 11
  change names at least one failure row; a change that fixes only audit rows
  is labelled `hygiene (no failure targeted)`.
- S08 expected checks: the schema row may sit at L0, L1 or L3; a seed eval
  with an explicit plan to reach 20 items passes when Q5 says fewer exist;
  changes may be labelled hygiene; deferred Q22 items are allowed.
- S01 check 14: every change maps to a failure row or is labelled hygiene.

[Unreleased]: https://github.com/Geenie-AI/skills/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Geenie-AI/skills/releases/tag/v0.1.0
