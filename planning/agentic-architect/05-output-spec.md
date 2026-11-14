# 05 — Output spec (what the skill produces)

Every run produces `architecture.md` plus one file per artifact. The document is the same shape in both modes and every scope; sections a scope does not need are marked `n/a (scope)` (matrix in `07-layers-and-scope.md`); optimize mode fills the "Current state" and "Changes" sections that design mode leaves as "n/a".

## `architecture.md` template

```markdown
# <solution name> — agentic architecture

Mode: design | optimize        Scope: <prompt | skill | skill-assignment | agent | knowledge | system | custom: L…>        Target: <framework> / <model(s)>        Date: <ISO>        Profile: <id or none>

> Out-of-scope root cause: <one line, or "none"> (rule SC3)

## 1. Intake
<the filled Q1–Q26 table from 02-intake-questions.md, with columns: Q | answer | source (derived:request / derived:artifact / derived:repo / profile:<id> / external:<system.field> / asked / asked (deferred) / default) | at | reason asked (if asked)>
Asked this run: <count up front> + <count deferred>. Permissions relied on and confirmed: <Q22 items or none>.

## 2. Assumptions
<every `unknown` with the default taken; the user corrects these first>

## 2a. Constraints and permissions
Fixed (Q21): <list>     Permissions (Q22): <a–j with yes / no / ask first>     Upkeep capacity (Q23): …     Tie-break (Q24): …

## 3. Accuracy definition
Correct output: <from Q4>          Incorrect output: <from Q4>
Metric: <exact | schema | judge-rubric>     Rubric: <link to eval file>

## 4. Current state (optimize mode)
Artifacts received: <list>     Chain: <steps with token size each>
Failures received: <count>     Review without failures: yes / no (R4a.3)

## 4a. Prompt audit (every prompt read or written; 03 § 4a)
| Prompt | Verdict | P1 resp. | P2 instr. | P3 ref ratio / size | P4 dup/contra | P5 neg. | P6 few-shot | P7 position | P8 abstain | P9 branches | P10 instr. tokens | P11 audiences | P12 inherits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drafting (input) | overdesigned | 5 | 31 | 9.8 / 90k | 2 / 1 | 6 | 0 | end only | no | 1 | 3.1k | yes | yes |
| 04-draft (emitted) | lean | 1 | 9 | 0.4 / 1.2k | 0 / 0 | 0 | 2 | start+end | yes | 0 | 0.9k | no | no |
Eval status: <none | exists and passes | exists and fails> → restructuring justified by <accuracy | cost/latency/maintainability> (R4a.1)

## 5. Diagnosis table
| ID | Requirement / failure | Info present in context? | Axis | Lever | Layer | In scope? | Evidence |
|----|-----------------------|--------------------------|------|-------|-------|-----------|----------|
| D1 | … | yes / no / n/a | context / behavior / both | prompt / examples / tool / retrieval / fine-tune / split / assign | L0–L5 | yes / no → § 15 | … |
| A1 | audit P1: 5 responsibilities in one prompt | n/a | behavior | split | L0/L3 | yes | measured in § 4a |

## 6. Context budget
| Step | Budget (tokens) | Sees | Shielded from | Retrieval into step | Fresh context? |
|------|-----------------|------|---------------|---------------------|----------------|

## 7. Architecture
### 7.1 Step graph
<nodes and typed edges; one responsibility per node>
### 7.2 Agents
<per agent: responsibility, model, tools, input schema, output schema, abstain output, skills it may load>
### 7.2a Skill assignment (when L2 assignment is in scope)
| Agent \ Skill | skill-a | skill-b | … |
|---|---|---|---|
| agent-1 | owner | reach (model-invoked) | — |
Gaps: <agents with a responsibility and no procedure>     Overlaps: <skills with two owners and the same trigger>
Context-load ledger per agent: <prompt + tool descriptions + assigned skill descriptions, in tokens>
### 7.3 Tools
<per tool: purpose, schema summary, irreversible?, confirmation gate>
### 7.4 Retrieval (if any)
<corpus, chunking, index, query strategy, k, filters, citation ids, retrieval-axis measurement>
### 7.5 Verification step
<what is checked against what; action on unsupported claims>

## 8. Lever plan
| Order | Lever | Applies to rows | Gate status | Conditional on |
|-------|-------|-----------------|-------------|----------------|
| 1 | Prompt engineering | all | always | — |
| 2 | Few-shot | D… | pass/fail (reason) | baseline run |
| 3 | Retrieval | D… | … | baseline run; retrieval-axis eval |
| 4 | Fine-tune | D… | G6.1–G6.5 status | levers 1–3 evaluated |
| 5 | Combine | — | … | … |

## 9. Eval spec
Set size: <n> (≥ 20)     Source: <existing / to produce / from logs>     Hold-out: <n> (if fine-tuning)
Metric: …   Grid: retrieval + answer (if retrieval)   Context sizes: <list> (if long context)
Loop owner: <who runs evaluate → hypothesis → change → re-evaluate>

## 10. Good-enough
### Business worksheet
<table from 03 § 8 with the user's figures; break-even p*>
### Realistic accuracy estimate and the gap to p*
### Handoff policy
| Failure type | Pattern (clarify / return / human) | Threshold / trigger | Owner |

## 11. Changes (optimize mode)
| Change | Artifact | Targets failure | Expected effect | How we will know (eval item ids) |

## 12. Artifacts emitted
| File | Artifact kind | Serves rows |

## 13. Rollout
Milestone 1: baseline (prompt + eval) → results decide milestones 2+.
Milestone 2: <conditional lever> …
Monitoring: <trace fields; pilot metrics: CSAT / decision accuracy / time to resolution>

## 14. Rejected options
<levers considered and the gate or rule that rejected them, e.g. "retrieval rejected: no context-axis rows (R5.3)" or "split into steps rejected: Q22(a) = no; expected cost: lost-in-the-middle risk at step 4 remains, see § 6">

## 15. Out-of-scope findings
| Row | Layer | Lever | Recommended scope widening | Accuracy forgone if scope is kept |
```

## Artifact file conventions

- `NN-<step>-prompt.md` — system prompt with E2 positioning and the manifest header (E3).
- `NN-<step>-agent.<md|py|ts>` — agent definition in native form (see `04-framework-targets.md`).
- `tools/<name>.json` or inline in the agent file — tool schema.
- `retrieval.md` — retrieval spec.
- `schemas/<boundary>.json` — structured output schema per boundary.
- `eval/set.jsonl`, `eval/judge-prompt.md`, `eval/README.md` — eval spec.
- `finetune/README.md`, `finetune/format-example.jsonl` — only if lever 4 passes its gates.
- `handoff-policy.md` — the decision table.

## Quality bar for a produced design (review checklist)

- [ ] Every diagnosis row has evidence, not just a tag.
- [ ] Lever 1 is present and the baseline precedes every other lever.
- [ ] Eval set ≥ 20 or an explicit plan to reach 20 before milestone 2.
- [ ] Break-even accuracy computed, or the symmetric placeholder is flagged in § 2.
- [ ] Every chain step has a budget, a manifest, an abstain output, and a typed output schema.
- [ ] A verification step exists whenever the output makes factual claims from sources.
- [ ] Every irreversible tool has a confirmation gate.
- [ ] Rejected options section names the rule that rejected each, including Q21/Q22 refusals with their expected accuracy cost.
- [ ] No lever in the design contradicts a Q21 fixed item or a Q22 `no` unless flagged as a conflict.
- [ ] Every intake row has a provenance tag; profile-sourced answers older than the staleness window were re-confirmed.
- [ ] § 4a has a row for every prompt read and every prompt emitted; every emitted prompt is `lean`; if an eval exists and passes, restructuring is justified by cost or maintainability, not accuracy.
- [ ] Every asked question has a reason it could not be derived; no question outside the scope's blocks was asked; no permission item was confirmed that the design does not rely on.
- [ ] Every diagnosis row names a layer; every out-of-scope row appears in § 15; no emitted artifact belongs to an out-of-scope layer.
- [ ] In `skill-assignment` scope: matrix, ledger, gaps and overlaps are present, and no user-invoked skill is assigned to an agent (AS3).
- [ ] Switching the target in § 0 would change only § 12 files.
