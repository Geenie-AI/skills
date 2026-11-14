## What changed

<!-- One or two sentences. Name the skill(s) touched and link the issue if there is one. -->

## Checklist

- [ ] `python3 scripts/validate.py` passes locally.
- [ ] If a model-facing file under `skills/<name>/` changed: `CHANGELOG.md` has an entry under `## [Unreleased]` in the skill's group.
- [ ] If a rule, scope, target or host overlay changed: a scenario under `tests/<name>/scenarios/` covers it, with `expected-checks.md` updated.
- [ ] Host facts I added are verified against the host's current docs, or marked `verify:` with the URL.
- [ ] The shared `SKILL.md` still names no host tools (rule H1) and has only `name` and `description` (plus the spec's optional keys) in its frontmatter (rule H3).
- [ ] New skill or changed description: `python3 scripts/skillrepo.py sync` was run (or the catalog workflow will do it on main).

## Scenario evidence (optional)

<!-- Paste the summary.md from scripts/run-scenario.sh if you ran one. -->
