# Testing

Two layers, both shared by every skill.

## Static validation (no model)

```bash
python3 scripts/validate.py                       # every skill
python3 scripts/validate.py --skill <name>        # one skill
python3 scripts/validate.py --changed-files-from changed.txt   # adds the CHANGELOG check
```

Per skill it checks the frontmatter (H3), host tool names (H1), relative
links and paths (H4), line budgets, rule-ID integrity (defined once, cited
IDs exist, `doc § N` sections exist in the template), scenario fixtures,
the test harness files, and that `README.md` exists. Repository-wide it
checks the adapters, `.claude-plugin/marketplace.json` (one entry per skill at
the repository version) and, as a warning, that the README catalogue and the
marketplace descriptions match the skills on disk. It runs on every push and
pull request (`.github/workflows/validate.yml`).

## Scenario evals (model required)

```bash
scripts/run-scenario.sh --skill <name> --scenario S02                    # host defaults to claude; needs the claude CLI
scripts/run-scenario.sh --skill <name> --host codex  --scenario S02      # needs the codex CLI
scripts/run-scenario.sh --skill <name> --host claude --scenario S02 --dry-run   # build the project, no model call
```

One run:

1. **Build a project.** A temporary directory gets the scenario's `fixtures/repo/` (directories named `dot-x` become `.x`), `fixtures/artifacts/` under `artifacts/`, the answers file as `answers.yaml`, the output of `fixtures/build.py` if present, an empty `questions.log`, and the skill installed with `scripts/install.sh` for the host.
2. **Run the host headlessly** with the prompt `<invocation line> + tests/<name>/preamble.md + input.md`. The preamble tells the skill that answers are in the file, to log every question it would have asked, and where to write.
3. **Judge.** `tests/<name>/judge-prompt.md` is filled with the expected checks, the primary document, a listing (with contents) of everything in the output folder, the questions log, and, when the scenario is graded against a baseline run, a unified diff of the two primary documents. The host's model returns strict JSON with one verdict per check.
4. **Score.** `scripts/grade-scenario.py score` combines the judge's verdicts with the question budget (`budget.upfront_max`, `budget.deferred_max`), the expectations (`expect_asked`, `expect_not_asked`) and whether the primary document exists, and writes `results.json` and `summary.md`.

Results land in `.eval-results/<name>/<label>-<host>/` (or `--out`).

### Baselines and variants

`eval.baseline` in `config.yaml` names a scenario whose primary document
other scenarios (matched by name prefix) are diffed against; the runner finds
the baseline run next to `--out` or under `.eval-results/` and passes the
diff to the judge. `eval.variants` lists extra answer files that rerun a
scenario under another label (`<scenario>-<suffix>`).

### In CI

`.github/workflows/eval.yml` runs weekly, on request (`workflow_dispatch`
with host, skill and scenario inputs), and on pull requests that touch a
skill or its tests. The `plan` job asks `scripts/skillrepo.py plan-eval` for
the matrix: on a pull request only the affected scenarios run (everything of
a skill when the skill folder, its harness files or the runner changed). Each
host runs through the reusable `scenario-host.yml`: baselines first, then
the matrix of runs. Every skill evaluates on Claude Code by default; Codex
runs only when a manual run picks `codex` or `all`. Claude Code authenticates with the run's GitHub OIDC
token (Workload Identity Federation, see `docs/releasing.md`), so no key is
stored; it is skipped on pull requests from forks. Codex is skipped when the
`OPENAI_API_KEY` secret is absent. The `report` job posts a
table as a pull-request comment or, on scheduled and manual runs, refreshes
the "Scenario eval results" block in each skill's README and commits it.

Evals are non-blocking except for the release scenario in the release
workflow.

## Writing a scenario

- `input.md` is what a user would type, including the paths they would see. Keep fixtures deterministic; `build.py` uses the standard library only and never reads outside its own folder.
- `answers.yaml` holds `scenario`, `budget` (`upfront_max`, `deferred_max`), `answers` keyed by question ID, and optionally `expected` (free-form, for humans), `expect_asked`, `expect_not_asked`.
- `expected-checks.md` is a numbered list. Each check is decidable from the material the judge receives and ends with its citation in square brackets: a rule ID, a question ID or `doc § N`. Checks that something is absent say what to search for.
- A check that compares two runs needs the baseline configured; otherwise the judge fails it with "diff not supplied".
