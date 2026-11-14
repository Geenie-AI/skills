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
| agentic-architect | S08m-prompt-scope-mini | claude | FAIL | 2/3 | 0/2 | 7/8 |

Failures:

- **agentic-architect / S08m-prompt-scope-mini / claude**
  - check 7 failed: Every row in the changes table maps to at least one of the three failure rows, or is labelled `hygiene (no failure targeted)`. [E5, doc § 11]
    - judge: § 11 row 'Reposition the output contract to start+end' lists Targets rows = A2 (an audit finding, not one of the three failure rows D1/D2/D3) and is not labelled 'hygiene (no failure targeted)'.

Run: 2026-11-14 · [full results (zip)](https://github.com/Geenie-AI/skills/releases/download/v0.1.0/scenario-results-v0.1.0.zip) · [workflow artifact](https://github.com/Geenie-AI/skills/actions/runs/43648205884/artifacts/14135930877) · [workflow run](https://github.com/Geenie-AI/skills/actions/runs/43648205884).

The zip holds each scenario's `results.json`, `summary.md`, judge output and run log.
<!-- release-history:end -->
