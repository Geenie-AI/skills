# Releasing

The repository has one semantic version and ships every skill at once on a
tag `vX.Y.Z` (pre-releases `vX.Y.Z-rc.N`). Skills are not versioned
individually; the catalogue and the marketplace entries carry the repository
version.

## Steps

1. In `CHANGELOG.md`, move the `## [Unreleased]` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section (entries are grouped by skill and by the shared tooling) and update the comparison links at the bottom.
2. Set `version` to `X.Y.Z` in `.claude-plugin/marketplace.json` and run `python3 scripts/skillrepo.py sync` so every plugin entry carries it. The validator fails when they disagree.
3. Make sure every skill's `eval.release_scenario` in `tests/<name>/config.yaml` names the scenario that must pass (a skill without one is skipped with a warning).
4. Merge to `main`, then tag and push:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

`release.yml` then validates every skill, checks that the catalogue is in
sync and that the manifest version equals the tag, extracts the changelog
section, runs each skill's release scenario on Claude Code (blocking), zips
each `skills/<name>` without
its README, and publishes a GitHub release titled `Geenie-AI skills vX.Y.Z`
with the zips attached.

Users of the Claude Code marketplace receive the new version when the entry
versions change; `claude plugin update` fetches it.

## Semantic versioning on behaviour

- **MAJOR**: a skill's inputs, scopes or the shape of what it produces change incompatibly (saved inputs or downstream tooling would break).
- **MINOR**: a skill, rule, scenario, target or host overlay is added.
- **PATCH**: wording fixes that keep every scenario's expected checks unchanged.

## Automation on `main`

- `catalog.yml` regenerates the README catalogue and the marketplace entries from every `skills/<name>/SKILL.md` whenever one changes, and commits the result. Run `python3 scripts/skillrepo.py sync` locally for the same effect.
- `eval.yml` refreshes the "Scenario eval results" block in each skill's README on its weekly and manual runs.

## Required repository settings

- **Claude API access** uses [Workload Identity Federation](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions): the eval and release jobs exchange the run's GitHub OIDC token for a short-lived Anthropic token through `.github/actions/anthropic-oidc`, so no Anthropic key is stored. The federation rule, organization, service account and workspace IDs default to Geenie-AI's in the workflows and can be overridden with the repository variables `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID` and `ANTHROPIC_WORKSPACE_ID`. The rule's match must accept every run that needs a token: `subject_prefix` `repo:Geenie-AI/skills:*` covers pushes to `main` (`ref:refs/heads/main`), release tags (`ref:refs/tags/v...`), scheduled and manual runs, and same-repository pull requests (`pull_request`). Pull requests from forks get no OIDC token and skip the Claude host.
- Secrets: `OPENAI_API_KEY` only if the Codex eval host should run.
- The `catalog` and `eval` workflows push to `main`; allow GitHub Actions to write to the repository, or protect `main` with a rule that permits the Actions bot.
- Replace the `@Geenie-AI/skills-maintainers` placeholder in `.github/CODEOWNERS` with real teams or logins.
