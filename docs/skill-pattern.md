# The skill pattern

Every skill in this repository is built the same way, so a person (or an
agent) who has read one can navigate, test and release any other. This page
is the contract. `scripts/validate.py` enforces the mechanical parts; the
rest is reviewed in pull requests.

## 1. One skill, three folders

| Folder | Ships to users | Holds |
|---|---|---|
| `skills/<name>/` | yes | The [Agent Skills](https://agentskills.io/specification) folder: `SKILL.md` plus the supporting files it points to. Also a `README.md` for people browsing GitHub; the installer and the release zip drop it. |
| `tests/<name>/` | no | `config.yaml` (validation and eval settings), `preamble.md` (non-interactive instructions), `judge-prompt.md` (the grading rubric) and `scenarios/` (acceptance scenarios). |
| `planning/<name>/` | no | The design documents the skill was built from: goal, rules with their sources, output specification, scenarios. `00-README.md` indexes them. |

Nothing else about a skill lives anywhere else. The shared parts (`scripts/`,
`adapters/`, `.github/workflows/`, `docs/`, `template/`) know a skill only
through its folder name and its `config.yaml`.

Why the split: hosts such as Cursor scan skill folders recursively, and a
`SKILL.md` inside a test fixture would be discovered as a skill. Keeping tests
and planning outside the shipped folder also keeps installs small.

## 2. The shipped folder

```
skills/<name>/
  SKILL.md            frontmatter (name, description) + the steps
  README.md           front page for GitHub: Geenie-AI logo header (as in the template), what it does, install, usage, eval results block
  reference/          rules the steps load on demand, each rule with an ID
  templates/          skeletons of what the skill produces
  targets/, profiles/, ...   any further supporting folders the skill needs
```

### SKILL.md

- **Frontmatter** holds `name` (equal to the folder name, lowercase, hyphens) and `description` (1–1024 chars; this is what hosts show and match on, and what the README catalogue and the marketplace entry are generated from). The spec's optional `license`, `compatibility` and `metadata` are allowed; host-specific keys are not (rule H3), they live in `adapters/`.
- **Body** is written for an agent: a one-paragraph statement of what the skill does and what it declines, a short list of **leading words** (the vocabulary the rest of the skill uses), then numbered **steps**. Each step says which reference files to read, lists its actions, and ends with a **Done when** line that an agent can check.
- **Capability verbs**, never tool names: "read the file", "search the working directory", "present the questions in one message and wait for the reply" (rule H1; the deny-list is `scripts/host-tool-names.txt`).
- **Non-interactive mode.** The body says what to do when the request states that the user's answers are in a file: log every question it would have asked, take the answer from the file, treat confirmations as given. The scenario runner relies on this.
- **Budgets.** `SKILL.md` stays under 150 lines and every other model-facing file under 400 (configurable per skill). Everything beyond that moves into a reference file the step loads on demand.

### Reference files and rule IDs

Every rule the skill applies is written once, in one reference file, as a
bullet that opens with its bold ID (`- **R4.1** ...`) or a table row whose
first cell is the ID. IDs are a short capital prefix plus a number
(`R4.1`, `P12`, `SC3`, `Q22`). The steps, the scenarios' expected checks and
the changelog cite those IDs; the validator fails when a cited ID is not
defined or is defined twice. Pick prefixes per rule family and list them in
`planning/<name>/00-README.md`.

Where a rule paraphrases an external source (a vendor guide, a standard),
the bullet cites the section. Where the skill goes beyond its source, it says
so (agentic-architect marks these "Beyond the guide").

### Templates and the primary document

A skill that produces a document writes it from a template in `templates/`
whose `## N` headings are numbered. Scenarios cite those sections as
`doc § N`, and the validator checks every citation against the template named
in `config.yaml` (`validate.section_template`).

## 3. The test folder

```
tests/<name>/
  config.yaml          see below
  preamble.md          text the runner puts in front of every scenario's input.md
  judge-prompt.md      rubric with {{EXPECTED_CHECKS}}, {{ARCHITECTURE_MD}}, {{ARTIFACT_LISTING}}, {{QUESTIONS_LOG}}
  README.md            scenario conventions specific to the skill
  scenarios/<ID>-<slug>/
    input.md           the user's first message, verbatim
    answers.yaml       canned answers keyed by question ID, budgets, expectations
    expected-checks.md numbered checks, each ending with its citation in [brackets]
    fixtures/          artifacts/ (pasted material), repo/ (copied into the project; dot-x/ becomes .x/), build.py
```

`config.yaml` keys (defaults in `scripts/skillrepo.py`):

| Key | Meaning |
|---|---|
| `validate.max_skill_lines`, `validate.max_reference_lines` | Line budgets |
| `validate.section_template` | Template whose `## N` headings define `doc § N` |
| `eval.output_dir` | Folder, relative to the project, where the skill writes |
| `eval.primary_document` | The file in that folder the judge reads in full |
| `eval.question_id_pattern` | Regex for question IDs in `questions.log` and `answers.yaml` |
| `eval.baseline.scenario`, `eval.baseline.for` | Scenario whose output others (by name prefix) are diffed against |
| `eval.variants` | Extra answer files that rerun a scenario under another label |

See [`testing.md`](testing.md) for how a scenario is run and graded.

## 4. Portability

The rules H1–H8 in [`adapters/README.md`](../adapters/README.md) keep a
skill runnable on every host. Short form: capability verbs, inline fallback
for anything a host might delegate, spec-only frontmatter, relative paths,
external systems only through MCP or files, model-neutral writing, user-only
invocation as a host overlay, no assumptions about a project's layout.

A skill never needs its own adapter: `scripts/install.sh --skill <name>`
generates pointer lines and snippets from the skill's description, and the
marketplace entry in `.claude-plugin/marketplace.json` is one object.

## 5. Versioning and the catalogue

The repository has one semantic version (`version` in
`.claude-plugin/marketplace.json`, tagged `vX.Y.Z`) and one `CHANGELOG.md`
whose entries are grouped by skill; skills are not versioned individually.
A pull request that touches a model-facing file of a skill adds an entry
under `## [Unreleased]`. See [`releasing.md`](releasing.md).

The skills catalogue in the root README and the plugin entries in the
marketplace manifest are generated, never edited by hand:
`python3 scripts/skillrepo.py sync` writes one row and one entry per
`skills/<name>/SKILL.md` with the description from the frontmatter, and the
`catalog` workflow runs it on `main` and commits the result. The validator
warns when they are stale.

## 6. Checklist for a new skill

1. `scripts/new-skill.sh <name>` creates the three folders from `template/` and syncs the catalogue and marketplace entry from the description.
2. Write `planning/<name>/` first: what the skill does, the rules with IDs and sources, the output shape, the scenarios.
3. Write `SKILL.md` and the reference files from the plan; keep the budgets.
4. Write at least three scenarios with checks that cite rule IDs and document sections.
5. `python3 scripts/validate.py --skill <name>` is green.
6. `scripts/run-scenario.sh --skill <name> --host claude --scenario S01` passes on at least one host.
7. Fill `skills/<name>/README.md` and add the skill under `## [Unreleased]` in `CHANGELOG.md`; the next `vX.Y.Z` tag ships it.
