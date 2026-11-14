# 08 — Portability and distribution

Two different kinds of "agnostic" are in play, and the plan keeps them apart:

- **Target-agnostic** (already covered in `04-framework-targets.md`): the solutions the skill *designs* can be emitted for Claude, OpenAI, or a generic framework.
- **Host-agnostic** (this file): the skill *itself* runs unchanged inside any agent host that understands a skill folder, such as Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, or a custom agent built on either SDK. Anyone can install it from this repo.

A third dimension, **programming-language-agnostic**, matters only for emitted SDK artifacts and is handled at the end.

Items marked `verify:` are host behaviours that must be checked against the host's current documentation at build time (P3/P9); hosts change their skill-loading paths and frontmatter keys more often than anything else here.

## 1. One source, many hosts

The skill is a plain folder of Markdown files following the open **Agent Skills** format (a `SKILL.md` with YAML frontmatter plus optional supporting files; `verify:` spec at agentskills.io and the hosts' own docs). That format is the portability contract. Everything the skill needs to work is inside the folder; nothing depends on a host feature that another host lacks.

```
skills/agentic-architect/
  SKILL.md                 # frontmatter: name, description (host-neutral keys only)
  reference/  targets/  templates/  profiles/
```

Rules for the content so it runs anywhere:

- **H1 Capability verbs, not tool names.** The body says "read the file", "search the repository", "measure the token count", "present the questions in one message and wait for the reply". It never names a host tool (no `AskUserQuestion`, `Read`, `apply_patch`). Each host maps verbs to its own tools.
- **H2 Single-context fallback.** Every step runs inline. Where a host offers delegation to a sub-agent with its own context, the skill may use it for the emit step (one sub-agent per target) and says "if the host can delegate to a sub-agent, do X; otherwise do X inline". Correctness never depends on delegation.
- **H3 Frontmatter is the common subset.** Only `name` and `description` are required by every host. Host-specific keys (invocation restrictions, allowed tools, model hints) live in host overlays (§ 2), never in the shared `SKILL.md`. `verify:` which optional keys each host ignores silently versus rejects.
- **H4 Relative paths only.** Supporting files are referenced relative to `SKILL.md`, so the folder can live at any install path.
- **H5 External systems only through MCP or files.** Profile lookups (`02` § Intake profiles) and retrieval measurements reach outside the repo only through an MCP server the user has configured, or through files in the repo. MCP is the one integration mechanism that Claude, OpenAI, Codex, Cursor, and most other hosts share (`verify:` per host). The skill works fully with file-based profiles when no MCP server exists.
- **H6 Model-neutral writing.** Instructions rely on no model-specific prompt tricks; they use the `writing-for-agents` levers (steps with completion criteria, disclosed reference, leading words, positive phrasing), which hold across models. Scenario checks in `06-scenarios.md` are the regression test for this.
- **H7 User-invocation is a host overlay.** The planning calls for a user-invoked skill (zero context load). Hosts express that differently or not at all. The shared `SKILL.md` keeps a short human-facing description; the Claude overlay adds the invocation restriction key; hosts without the concept simply expose the skill by name and description.
- **H8 No host-specific file layout assumptions.** The skill reads a project's existing agents/skills/prompts (for `agent` and `skill-assignment` scopes) by asking the user for paths (Q26) or by searching for common layouts (`.claude/`, `.agents/`, `.cursor/`, `AGENTS.md`, `CLAUDE.md`), never by assuming one.

## 2. Host overlays and install paths

An overlay is a tiny host-specific wrapper that points at the shared skill folder; the body is never copied. Overlays live in `adapters/<host>/` and the install step for each host copies or links the shared folder to where that host looks.

| Host | Where the host looks (`verify:` each) | Overlay contents | Install |
|---|---|---|---|
| Claude Code | `.claude/skills/<name>/` (project) or `~/.claude/skills/<name>/` (user); or as a plugin via a marketplace | `.claude-plugin/plugin.json` + `marketplace.json` at repo root so the repo can be added as a marketplace; overlay frontmatter adds `disable-model-invocation: true` | `claude plugin marketplace add <owner>/<repo>` then install, or copy the folder |
| OpenAI Codex | `verify:` project `.agents/skills/<name>/` or user-level skills directory; `AGENTS.md` pointer | one-line `AGENTS.md` snippet naming the skill and when to invoke it | copy or link the folder; add the `AGENTS.md` line |
| Cursor / Copilot / Gemini CLI / others with skill support | `verify:` each host's skills directory | a rules/instructions snippet that names the skill folder | copy or link |
| Any host with no skill support | n/a | `AGENTS.md`-style pointer: "for designing or optimizing agentic solutions, read `skills/agentic-architect/SKILL.md` and follow it" | pointer only |
| Custom agent on Claude Agent SDK or OpenAI Agents SDK | n/a | a loader example: read `SKILL.md` into the system prompt or expose it as a tool result | code sample in `adapters/sdk/` |

A generic install script (`scripts/install.sh --host <claude|codex|cursor|generic> [--user|--project]`) performs the copy or symlink and prints the pointer line to add. A community skills CLI (`verify:` e.g. `npx skills add <owner>/<repo>`) is documented if it resolves this repo's layout.

## 3. Repository layout

```
agentic-architect/
  README.md                      # professional front page (planned in § 6)
  LICENSE                        # decision pending (§ 8)
  CHANGELOG.md                   # keep-a-changelog format
  skills/agentic-architect/      # the shared, host-neutral skill (the only thing a host needs)
  adapters/                      # host overlays and SDK loader samples
    claude/  codex/  cursor/  sdk/
  .claude-plugin/                # plugin.json, marketplace.json (Claude Code marketplace install)
  scripts/
    install.sh                   # host-aware copy/link
    validate.py                  # static checks (§ 4), no model needed
    run-scenario.sh              # drives one scenario through one host (§ 5)
  tests/
    scenarios/S01…S11/           # input.md, expected-checks.md, fixtures (artifacts, profiles, repo stubs)
    judge-prompt.md              # LLM-judge rubric that scores a run's architecture.md against expected-checks.md
  planning/                      # these documents
  .github/
    workflows/validate.yml  eval.yml  release.yml
    PULL_REQUEST_TEMPLATE.md  CODEOWNERS
```

## 4. Static validation (no model, runs on every push)

`scripts/validate.py` fails the build on:

- Frontmatter: `name` present and equal to the folder name; `description` present and within the spec length (`verify:` limit); no host-specific keys in the shared `SKILL.md`.
- H1: a deny-list of host tool names found in `skills/**` (maintained in `scripts/host-tool-names.txt`).
- H4: every relative link in `skills/**` resolves.
- Sprawl guard: `SKILL.md` under a line budget (default 150) and every reference file under a larger one; the plan's `writing-for-agents` pruning rule, made mechanical.
- Single source of truth: the three rule sets (`decision-framework`, `layers-and-scope`, `intake-questions`) contain no duplicated rule IDs, and every rule ID cited in `SKILL.md` exists.
- Scenario fixtures parse and each `expected-checks.md` references only rule IDs and section numbers that exist.
- Overlays: every host in `adapters/` has a README and references the shared folder by relative path.

## 5. Scenario evals (model required, scheduled or manual)

`eval.yml` runs the scenarios in `tests/scenarios/` through one or more hosts in non-interactive mode and grades the produced `architecture.md` against `expected-checks.md` with the judge prompt.

- Hosts: Claude Code headless (`verify:` `claude -p` with the skill installed to a temp project) and OpenAI Codex non-interactive (`verify:` `codex exec`), each behind a secret; a host job is skipped when its secret is absent.
- Each scenario fixture supplies canned answers for the questions the skill is allowed to ask (an "answer file" the runner feeds back), so the asking-policy budget from `02` is also measured: the runner counts questions and fails the scenario if the count exceeds the budget.
- Grading: pass/fail per check, with the judge's reason. Results post as a PR comment and as a summary artifact. Non-blocking by default; a maintainer can require it for releases.
- Cost control: scheduled weekly plus `workflow_dispatch`; PRs run only the scenarios whose fixtures or rule files changed.

## 6. README plan (written as `README.md` at the repo root)

Sections, in order: what it is (two sentences), the method it follows (link to the OpenAI guide, five-line summary), what you can point it at (scopes), what it produces, install per host, usage (invocation, scopes, profiles, optimize vs design), how it decides (axes, lever order, gates), targets it can emit for, repository layout, contributing (validation, scenarios, planning docs), versioning and releases, license. No badges until CI exists; then validate and release badges only.

## 7. Versioning, tagging, releases

- **Semantic versioning** on the skill's behaviour: MAJOR when the intake fact set, scopes, or output document shape change incompatibly (profiles or downstream tooling would break); MINOR when a rule, scenario, target, or host overlay is added; PATCH for wording fixes that keep every scenario's expected checks unchanged.
- **Tags** `vMAJOR.MINOR.PATCH` on `main` only. `CHANGELOG.md` in keep-a-changelog form; the `Unreleased` section is required to be non-empty on every PR that touches `skills/**` (checked by `validate.yml`).
- **`release.yml`** on tag push: run static validation, run the scenario eval against at least one host (blocking for releases), package `skills/agentic-architect/` as `agentic-architect-<version>.zip`, create the GitHub release with the changelog section as its body and the zip attached, and bump the version field in `.claude-plugin/plugin.json` and `marketplace.json` if they do not already match the tag (fail if the tag and the manifest disagree).
- **Pre-releases** `v1.2.0-rc.1` are allowed and marked as such on GitHub; marketplaces are pointed at tagged releases, never at `main`.
- Optional automation: release-please or a conventional-commits bump can generate the changelog and tag; deferred until there is more than one maintainer.

## 8. Decisions pending for the user

- License (MIT or Apache-2.0 suggested for a skill people copy into their repos).
- Repository name and owner for the install commands in the README.
- Which hosts get a maintained overlay on day one (default: Claude Code and OpenAI Codex, generic pointer for the rest).
- Whether the eval workflow is blocking for releases from the first version, given it needs API secrets.

## 9. Programming-language-agnostic emission

Only SDK targets produce code. Rules:

- The emit step detects the project's language from the repo (lockfiles, imports) and otherwise asks lazily (a deferred question, `02` asking policy) only when a code artifact is about to be emitted.
- Templates exist for Python and TypeScript for both SDK targets; other languages fall back to the generic declarative form (`04` generic target) plus a note.
- Non-code artifacts (prompts, skills, schemas, eval sets, policies) are language-neutral by construction and are the default output; code is emitted only when the target is an SDK and the user asked for runnable artifacts (scope includes L1 agents for an SDK target).

## 10. Build phase added to the skill plan

| Phase | Deliverable | Exit test |
|---|---|---|
| P9 | Host overlays, install script, static validation, scenario runner, workflows, README, CHANGELOG, first tag `v0.1.0` | A fresh clone installs into Claude Code and Codex with the documented commands; `validate.yml` is green; scenario S2 passes on at least one host via `eval.yml`; the release workflow produces a GitHub release from the tag |
