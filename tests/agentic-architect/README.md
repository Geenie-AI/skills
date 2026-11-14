# Tests

Acceptance scenarios for the `agentic-architect` skill, taken from `planning/agentic-architect/06-scenarios.md`. The shared harness is described in [`docs/testing.md`](../../docs/testing.md): static validation (`scripts/validate.py --skill agentic-architect`) checks that every fixture parses and that every citation in an `expected-checks.md` names a rule ID or document section that exists; scenario evals (`scripts/run-scenario.sh --skill agentic-architect`, `.github/workflows/eval.yml`) run one scenario through one host and grade the result with `judge-prompt.md`; `scripts/eval-report.py` folds the `results.json` files of a run into the table at the bottom of `skills/agentic-architect/README.md`.

## Layout

```
tests/agentic-architect/
  README.md
  config.yaml                      # output folder, primary document, question-ID pattern, baseline
  preamble.md                      # non-interactive instructions the runner puts in front of input.md
  judge-prompt.md                  # LLM judge; placeholders are substituted by the runner
  scenarios/<ID>-<slug>/
    input.md                       # the user's first message, verbatim
    answers.yaml                   # canned answers the runner feeds back, plus budgets and expectations
    expected-checks.md             # numbered checks; each ends with its citation in [brackets]
    fixtures/
      artifacts/                   # pasted prompts, agent definitions, skills, failure examples
      repo/                        # copied into the temporary project root before the run
        dot-agentic-architect/profiles/<id>.yaml   # becomes <project>/.agentic-architect/profiles/
      eval/                        # existing eval sets the input refers to
      build.py                     # optional; run as `python3 -I fixtures/build.py <project-dir>`
```

## Conventions

- `input.md` references fixture files by the path the user would see. Paths under `fixtures/artifacts/` are pasted or attached as-is; paths under `artifacts/` or at the project root are produced by copying `fixtures/repo/` and running `fixtures/build.py`.
- A repo stub cannot contain a literal `.claude/` directory (local tooling refuses to write there), so fixtures use `dot-claude/`; the runner renames `dot-claude` to `.claude` when it copies the stub into the project root. The same applies to any other dot-directory (`dot-agents/`, `dot-cursor/`).
- `build.py` is deterministic and uses the standard library only. It writes generated material under `<project-dir>/` (for example `artifacts/policy-corpus.md`, `policies/*.md`) and never reads anything outside its own `fixtures/` folder.
- `answers.yaml` keys answers by question ID (`Q1`–`Q26`). Q22 is a single string of letter:value pairs. `budget` caps the questions the skill may ask: `upfront_max` for the first batch, `deferred_max` for questions asked at a decision point. `expect_asked` and `expect_not_asked` list question IDs that must or must not appear in `questions.log`.
- The runner writes every question the skill asked to `questions.log`, one line per question with its ID, the stated reason, and whether it was up-front or deferred. The judge receives this log.
- `expected-checks.md` cites only rule IDs (`R4.1`–`R4.7`, `R4a.1`–`R4a.5`, `P1`–`P12`, `R5.1`–`R5.4`, `G6.1`–`G6.5`, `R9.1`–`R9.5`, `SC1`–`SC8`, `AS1`–`AS6`, `E1`–`E8`, `Q1`–`Q26`) and document sections (`doc § 0`–`doc § 15`, `doc § 2a`, `doc § 4a`, `doc § 7.1`–`doc § 7.5`, `doc § 7.2a`).
- S05 is a rerun of S02 with a different target and is graded by diffing its `architecture.md` against the S02 run's; S07 and S07b are graded the same way. The runner diffs against `--baseline <dir>` (default: the S02 results dir for the same host) and supplies the diff to the judge. The baseline is declared in `config.yaml` (`eval.baseline`). S05's second answers file, `answers-generic.yaml`, drives the generic-target rerun (`eval.variants`): `scripts/run-scenario.sh --skill agentic-architect --host claude --scenario S05 --answers answers-generic.yaml`.
- `scripts/run-scenario.sh --skill agentic-architect --dry-run` builds the temporary project and the prompt without calling a host; use it to check a new fixture.
- All dates in fixtures are relative to a run date of 2026-11-14; the profile in S07 has one answer deliberately older than its 90-day staleness window.
