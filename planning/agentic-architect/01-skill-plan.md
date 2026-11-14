# 01 — Skill build plan

## Goal

Build a skill, `agentic-architect`, that takes a scenario (new or existing) and produces a reliable agentic architecture plus the concrete artifacts for the chosen framework. "Reliable" means: every recommendation is justified by the *Optimizing LLM Accuracy* method, every design ships with an eval set and a failure-handling path, and the user can trace each artifact back to a diagnosed need.

## Scope

In scope:

- **Design mode**: user describes a new situation; skill produces the ideal architecture and artifacts.
- **Optimize mode**: user supplies an existing prompt / chain / agent set / RAG setup plus observed failures; skill diagnoses and produces targeted improvements and rewritten artifacts.
- **Targets**: Claude (Claude Code skills/subagents/CLAUDE.md, Claude Agent SDK, Messages API), OpenAI (Agents SDK, Responses API, prompts, file search/vector stores, fine-tuning), and a generic target (framework-agnostic artifacts: plain system prompts, JSON tool schemas, pseudo-graph of steps) for anything else.
- **Artifact kinds**: prompts, skills/instruction documents, agent definitions (single or multi), tool definitions, retrieval design, context budget plan, eval set spec, failure-handling policy, rollout plan.
- **Scopes** (see `07-layers-and-scope.md`): a run may be confined to one layer or any subset: `prompt`, `skill`, `skill-assignment`, `agent`, `knowledge`, `system`, or custom. Diagnosis always covers every layer; changes are confined to the scope and out-of-scope findings are reported.

Out of scope (state this in the skill so it declines cleanly):

- Running training jobs, provisioning vector stores, or executing evals. The skill *specifies* them; it does not run them.
- Picking a vendor on price. The skill accepts the target as given.

## Skill shape (follows `writing-for-agents`)

User-invoked (`disable-model-invocation: true`): this skill only ever fires when a human types `/agentic-architect`. Zero context load.

```
agentic-architect/
  SKILL.md                      # the steps, in order; short; completion criteria on every step
  reference/
    layers-and-scope.md         # layer model, scope rules, per-scope intake/output matrix, skill-assignment rules (loaded in step 1 and step 4)
    intake-questions.md         # the fixed question set (disclosed; loaded in step 1 only)
    decision-framework.md       # axes, lever order, diagnosis table, gates (loaded in step 2–3)
    long-context.md             # chaining + context-budget rules (loaded only when context > threshold or chain > 1 step)
    rag.md                      # retrieval design + retrieval/LLM failure grid (loaded only if context axis fires)
    fine-tuning.md              # gates, dataset rules, prompt baking (loaded only if behavior axis fires AND examples are available)
    good-enough.md              # break-even accuracy worksheet + graceful failure patterns (loaded in step 3 always)
  targets/
    claude.md                   # emit rules + artifact templates for Claude Code / Agent SDK / Messages API
    openai.md                   # emit rules + artifact templates for Agents SDK / Responses API / file search / fine-tuning
    generic.md                  # framework-agnostic emit rules
  templates/
    architecture.md             # the output document skeleton (05-output-spec.md)
    eval-set.md                 # eval set skeleton
  profiles/
    README.md                   # profile record format, resolution order, staleness rule
    <id>.yaml                   # stored intake answers keyed by ID (optional, per project)
    mappings/<source>.yaml      # field-to-question mapping for an external source reached by tool/MCP
```

The folder above is the host-neutral skill and lives at `skills/agentic-architect/` in the repo; host overlays, install script, CI and release plumbing are planned in `08-portability-and-distribution.md`. The body uses capability verbs rather than host tool names and runs fully inline, so it installs unchanged on Claude Code, OpenAI Codex, and any host that loads the Agent Skills format.

Design notes that come straight from the writing-for-agents reference:

- `SKILL.md` carries **steps only**. All reference is disclosed behind pointers, and the pointer wording names the branch that reaches it ("when the chain has more than one step, read `reference/long-context.md`").
- Every step ends on a **checkable, exhaustive completion criterion** ("every intake question has an answer or an explicit `unknown`", "every observed failure is tagged `context` or `behavior` or `both`").
- Leading words the skill reuses: **axis** (context / behavior), **lever** (prompt, examples, retrieval, fine-tune), **baseline** (the prompt-only eval result), **break-even** (the accuracy at which the system pays for itself), **handoff** (the graceful-failure path), **budget** (tokens per step).
- Phrase rules positively. "Put critical instructions at the start and end of the prompt" rather than "don't bury instructions".

## The four steps (what SKILL.md will contain)

1. **Intake.** Establish the **scope** first (Block I): which layers this run may change and which are given. Then fill the fixed fact set from `reference/intake-questions.md` by **deriving first** (request text, artifacts, profile, repo) and asking only what is still unknown, in scope, and decision-relevant; questions that bind only to a specific lever are deferred to the point in step 3 where that lever is chosen. The facts cover the task, knowledge, failures, risk, envelope, and permissions (which shapes the skill may introduce); the user is never asked to choose an architecture. Mode (design/optimize) and target framework are mandatory; everything else may be answered `unknown`. If a **profile ID** is given, resolve it first (repo store → previous run → external source via a declared mapping), pre-fill, and ask only Q1, the gaps, the stale answers, and the per-run failure questions; always show the permissions back for confirmation. In optimize mode, also collect the existing artifacts verbatim and at least three concrete failure examples. *Done when:* every up-front question has an answer or `unknown`, every answer carries a provenance tag (derived:<source> / asked / profile / default) and, for asked ones, the reason it could not be derived, `unknown` answers each have a stated default assumption, and the permissions block has been confirmed by the user in this run; the scope is named and every out-of-scope layer the work depends on has been supplied or marked absent.
2. **Diagnose.** Run the prompt audit on every pasted prompt, skill and agent definition (measured, not asked), then build the diagnosis table across **all layers**: one row per requirement (design mode) or per observed failure (optimize mode), each tagged with an axis, a candidate lever, and the layer the lever lives in. Compute the context budget for each step of the proposed or existing chain. *Done when:* every prompt read has an audit row with a verdict; every row has an axis, a lever, a layer, and a one-line reason; rows whose layer is out of scope are marked for doc § 15; the budget table has a row for every step (or, in `skill-assignment` scope, a context-load ledger per agent).
3. **Design.** Apply the lever order and gates from `reference/decision-framework.md`. When a gate depends on a deferred question (cost ceiling, data constraints, a specific Q22 permission, upkeep, tie-break), ask it now, stating the decision it affects, then continue. Produce the architecture document from `templates/architecture.md`, including the eval set spec, break-even accuracy, and handoff policy. *Done when:* every section the scope requires is filled and the rest marked `n/a (scope)`, every lever chosen is justified by an in-scope diagnosis row, doc § 15 lists every out-of-scope row with the recommended widening, and the design includes a baseline step before any retrieval or fine-tuning step.
4. **Emit.** Read the matching `targets/<framework>.md` and write each artifact in that framework's native form. *Done when:* every artifact listed in the architecture document exists as a file or a code block, each one names the diagnosis rows it serves, and every agent changed in this run has its prompts and skills re-emitted (rule SC6).

## Build phases

| Phase | Deliverable | Exit test |
|---|---|---|
| P0 | This planning set reviewed and agreed | User signs off on question set and framework list |
| P1 | `SKILL.md` + `reference/intake-questions.md` + `reference/decision-framework.md` + `reference/good-enough.md` | Running the skill on scenario S2 (new situation) in `06-scenarios.md` produces a complete architecture document with a prompt-only baseline, an eval spec, and a break-even figure |
| P2 | `reference/long-context.md` + `reference/rag.md` | Scenario S1 (massive chained prompt) produces the expected diagnosis and the expected set of fixes |
| P3 | `targets/claude.md`, `targets/openai.md`, `targets/generic.md` + templates | Same scenario emits correct native artifacts for each of the three targets |
| P4 | `reference/fine-tuning.md` | Scenario S3 (behavior gap with examples) recommends fine-tuning only after the gates pass, and recommends against it in S4 |
| P5 | Asking policy: derivation sources, decision-relevance test, lazy questions at the decision point | Scenario S11 passes: question counts within budget; every asked question carries a reason; derivations are shown for correction |
| P6 | Scope handling: Block I, per-scope block pruning, doc § 15, skill-assignment rules and the agents × skills matrix | Scenarios S8–S10 pass: prompt-only, skill-assignment, and agent-scope runs confine changes to scope and report out-of-scope root causes |
| P7 | Profiles: `profiles/README.md`, resolution logic in the intake step, write-back offer | Scenario S7 passes: a profile run and a hand-typed run with the same answers give identical diagnoses; stale and per-run questions are still asked |
| P8 | Prune pass per `writing-for-agents` | Every line in `SKILL.md` changes behavior versus default; no reference is duplicated between files |
| P9 | Portability and distribution (`08`): host overlays, install script, `validate.py`, scenario runner, workflows, README, CHANGELOG, tag `v0.1.0` | Fresh clone installs on Claude Code and Codex; `validate.yml` green; S2 passes on one host via `eval.yml`; release workflow publishes from the tag |

## Acceptance criteria for the whole skill

- The skill never recommends retrieval or fine-tuning without first specifying a prompt-only baseline and an eval set of at least 20 ground-truth items.
- The skill never emits a design without a break-even accuracy and a handoff policy.
- In optimize mode, every proposed change maps to at least one observed failure.
- For any chain of more than one step, the output includes a per-step context budget and a statement of what each step sees and what it is shielded from.
- Switching the target framework changes only the emitted artifacts, never the diagnosis or the architecture.
- The skill never asks the user whether they need retrieval, multiple steps, multiple agents, tools, or fine-tuning; it infers the need from the facts and asks only for permission to use them (Block H of the intake).
- A user who is anchored on one agent chaining its own prompts, with all permissions granted, receives the design the diagnosis calls for, with the current shape listed in the diagnosis only as evidence.
- When a permission is refused, the design stays within the constraint and doc § 14 states what accuracy is forgone.
- The skill asks a question only when it is in scope, could not be derived from the request, artifacts, profile, or repo, and would change the design; every asked question states why it could not be derived. Scenario S11 bounds the count.
- Permission items are confirmed only when the diagnosis relies on them, and only those items.
- A run from a profile ID still asks the per-run failure questions in optimize mode unless they are derivable from a trace export; every intake row shows its provenance.
- A run in any scope narrower than `system` changes only in-scope layers, and reports every out-of-scope diagnosis row in doc § 15 with its forgone accuracy.
- A `skill-assignment` run produces the agents × skills matrix, the per-agent context-load ledger, and rewritten trigger descriptions, and reports gaps and overlaps.
- All thirteen scenarios in `06-scenarios.md` pass their listed checks.
- Every prompt the skill reads gets an audit row with measured values, and every prompt it emits audits as `lean`; a failure-free review request produces a complete design from audit rows alone (scenario S12).
- The shared `SKILL.md` contains no host tool names and no host-specific frontmatter keys (checked by `validate.py`); the skill completes a scenario on at least two hosts with identical diagnoses.

## Open decisions for the user (P0)

- Should the generic target emit LangGraph-flavoured pseudo-code or stay purely declarative? Default: declarative.
- Minimum eval-set size: the guide says 20+; should the skill hard-block below that, or warn? Default: warn at <20, block at 0.
- Should the skill maintain a per-project `ARCHITECTURE.md` across runs (optimize mode updating the design-mode document)? Default: yes, if one exists in the working directory, read it first and offer its doc § 1 Intake as a profile.
- Which external systems should have a profile mapping on day one (e.g. a tenant or site record), and which fields map to which questions? Default: none; repo profile store only.
- Staleness window for profile answers. Default: 90 days.
