<p align="center">
  <a href="https://github.com/Geenie-AI/skills"><img src="https://raw.githubusercontent.com/Geenie-AI/.github/main/profile/assets/geenie-ai-logo.png" alt="Geenie-AI logo" width="96"></a>
</p>

<h1 align="center">{{SKILL}}</h1>

<p align="center">A <a href="https://github.com/Geenie-AI/skills">Geenie-AI skill</a>: TODO one line.</p>

<p align="center">
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml/badge.svg" alt="eval"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f" alt="Agent Skills compatible"></a>
</p>

TODO: two sentences on what the skill does and the method it follows.

Part of the [Geenie-AI skills](../../README.md) collection; it follows the repository's [skill pattern](../../docs/skill-pattern.md).

## What it does

TODO

## Install

```bash
claude plugin marketplace add Geenie-AI/skills
claude plugin install {{SKILL}}@geenie-ai-skills       # then /{{SKILL}}:{{SKILL}}

scripts/install.sh --skill {{SKILL}} --host <claude|codex|copilot|gemini|cursor|kiro|agents|generic> [--project|--user]
```

Per-host paths and invocation forms are in [`adapters/`](../../adapters/README.md).

## Usage

```
/{{SKILL}} TODO an example request
```

## How it decides

TODO: the rules, with their sources, live in [`reference/`](reference/).

## Layout

```
skills/{{SKILL}}/          the host-neutral skill
  SKILL.md                 the steps
  reference/               rules with IDs
  templates/               output skeletons
tests/{{SKILL}}/           config, judge prompt, preamble, scenarios
planning/{{SKILL}}/        design documents
```

## Contributing

- Read [`planning/{{SKILL}}/00-README.md`](../../planning/{{SKILL}}/00-README.md) first.
- Run `python3 scripts/validate.py --skill {{SKILL}}` before opening a pull request.
- Changes to rules need a scenario in [`tests/{{SKILL}}/scenarios/`](../../tests/{{SKILL}}/) and an entry under `Unreleased` in the repository [`CHANGELOG.md`](../../CHANGELOG.md).

## Scenario eval results

<!-- eval-results:start -->
No scheduled run has completed yet.
<!-- eval-results:end -->
