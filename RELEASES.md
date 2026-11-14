# Release history

One entry per release tag, newest first: the scenario selection the release
ran and how every scenario scored on it. Written by the `release` workflow
(`scripts/release-history.py`); do not edit by hand. What changed in each
release is in [`CHANGELOG.md`](CHANGELOG.md); the zips are on the
[Releases](https://github.com/Geenie-AI/skills/releases) page.

<!-- release-history:start -->
## v0.1.0 (2026-11-14) — 1 failing

Selection: host `claude` · skills `all` · scenario `S08m`.

> [!WARNING]
> **1 of 1 scenarios failed.** The release was published anyway; the failed checks are listed below.

| Skill | Scenario | Host | Result | Up-front q | Deferred q | Judge checks |
|---|---|---|---|---|---|---|
| agentic-architect | S08m-prompt-scope-mini | claude | FAIL | 3/3 | 0/2 | 0/0 |

Failures:

- **agentic-architect / S08m-prompt-scope-mini / claude**
  - judge: judge output had no parseable JSON

Run: 2026-11-14 · [full results (zip)](https://github.com/Geenie-AI/skills/releases/download/v0.1.0/scenario-results-v0.1.0.zip) · [workflow artifact](https://github.com/Geenie-AI/skills/actions/runs/43643443727/artifacts/14133169338) · [workflow run](https://github.com/Geenie-AI/skills/actions/runs/43643443727).

The zip holds each scenario's `results.json`, `summary.md`, judge output and run log.
<!-- release-history:end -->
