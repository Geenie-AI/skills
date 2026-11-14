# Release history

One entry per release tag, newest first: the scenario selection the release
ran and how every scenario scored on it. Written by the `release` workflow
(`scripts/release-history.py`); do not edit by hand. What changed in each
release is in [`CHANGELOG.md`](CHANGELOG.md); the zips are on the
[Releases](https://github.com/Geenie-AI/skills/releases) page.

<!-- release-history:start -->
## v0.1.0 (2026-11-14)

Selection: host `claude` · skills `all` · scenario `S08m`.

**All 1 scenarios passed.**

| Skill | Scenario | Host | Result | Up-front q | Deferred q | Judge checks |
|---|---|---|---|---|---|---|
| agentic-architect | S08m-prompt-scope-mini | claude | pass | 3/3 | 2/2 | 8/8 |

Run: 2026-11-14 · [full results (zip)](https://github.com/Geenie-AI/skills/releases/download/v0.1.0/scenario-results-v0.1.0.zip) · [workflow artifact](https://github.com/Geenie-AI/skills/actions/runs/43650159911/artifacts/14136077464) · [workflow run](https://github.com/Geenie-AI/skills/actions/runs/43650159911).

The zip holds each scenario's `results.json`, `summary.md`, judge output and run log.
<!-- release-history:end -->
