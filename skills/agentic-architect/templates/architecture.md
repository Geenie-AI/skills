# Template: `architecture.md`

Every run produces `architecture.md` in the output root plus one file per artifact. The document has the same shape in both modes and every scope. Mark sections the scope does not need `n/a (scope)`; mark §§ 4 and 11 `n/a (design)` in design mode. Copy the skeleton below and fill it.

## Output location

- Output root: the `agentic-architecture` folder in the project, unless the request names another place.
- If the root already holds an `architecture.md`, read it first (its § 1 can serve as a profile), then write this run to a dated subfolder `agentic-architecture/<YYYY-MM-DD>-<scope>` instead of overwriting, and say where the files went.
- Artifact files beside the document: `NN-<step>-prompt.md`, `NN-<step>-agent.<md|yaml|py|ts>`, `tools/<name>.json`, `schemas/<boundary>.json`, `retrieval.md`, `eval/set.jsonl`, `eval/judge-prompt.md`, `eval/README.md`, `finetune/README.md` and `finetune/format-example.jsonl` (only when the fine-tune gates pass), `handoff-policy.md`.

## Skeleton

```markdown
# <solution name> — agentic architecture

## 0. Header
Mode: design | optimize    Scope: <prompt | skill | skill-assignment | agent | knowledge | system | custom: L…>    Target: <framework> / <model(s)>    Date: <ISO>    Profile: <id or none>

> Root cause outside reach: <one line naming the layer or the Q21/Q22 item, or "none"> (SC3)

## 1. Intake
| Q | Answer | Source | At | Reason asked |
|---|---|---|---|---|
| Q1 | … | derived:request | <date> | |
| Q22 | a:yes b:yes c:yes d:yes e:ask … | asked (deferred) | <date> | gates retrieval for D1 |
Asked this run: <n> up front + <n> deferred. Permissions relied on and confirmed: <Q22 items, or none>.

## 2. Assumptions
<every default taken, with the question it stands in for; the user corrects these first>

## 2a. Constraints and permissions
Fixed (Q21): <list>    Permissions (Q22): <a–j with yes / no / ask first / not needed>    Upkeep (Q23): …    Tie-break (Q24): …

## 3. Accuracy definition
Correct output: <Q4>    Incorrect output: <Q4>
Metric: <exact | schema | judge-rubric | pairwise>    Rubric: <eval file>    Language: <Q9>

## 4. Current state (optimize)
Artifacts received: <list with measured tokens>    Chain: <steps with context size each>
Failures received: <count>    Review without failures: yes | no (R4a.3)    Eval status: none | exists and passes at <x %> | exists and fails

## 4a. Prompt audit
| Prompt | Verdict | P1 | P2 | P3 ratio / size | P4 dup / contra | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | P13 | P14 | P15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <name> (input) | overdesigned | 5 | 31 | 9.8 / 90k | 2 / 1 | 6 | 0 | end only | no | 1 | 3.1k | yes | yes | yes | yes | yes |
| <name> (emitted) | lean | 1 | 9 | 0.4 / 1.2k | 0 / 0 | 0 | 2 | start+end | yes | 0 | 0.9k | no | no | yes | yes | yes |
Restructuring justified by: <accuracy | cost, latency, maintainability, change risk> (R4a.1)

## 5. Diagnosis table
| ID | Requirement / failure | Info present in context? | Axis | Lever | Layer | In scope? | Evidence |
|---|---|---|---|---|---|---|---|
| D1 | … | yes / no / beyond window / n/a | context / behavior / both | prompt / examples / tool / retrieval / fine-tune / split / route / merge / assign / schema | L0–L5 | yes / no → § 15 | <measured> |
| A1 | audit P1: 5 responsibilities in one prompt | n/a | behavior | split | L0/L3 | yes | measured in § 4a |
| D<n> | missing eval (optimize, none exists) | n/a | both | baseline eval ≥ 20 items | L5 | yes | Eval status in § 4 |

## 6. Context budget
| Step | Budget (tokens) | Sees | Shielded from | Retrieval into step | Fresh context? |
|---|---|---|---|---|---|
(in `skill-assignment` scope: the per-agent ledger, AS4)

## 7. Architecture
### 7.1 Step graph
<nodes and typed edges; one responsibility per node; mark `given` for frozen parts>
### 7.2 Agents
<per agent: responsibility, model, tools, input schema, output schema, abstain output, skills it may load>
### 7.2a Skill assignment
| Agent \ Skill | skill-a | skill-b |
|---|---|---|
| agent-1 | owner | reach |
Gaps: …    Overlaps: …    Ledger: <per agent, tokens, vs budget>
### 7.3 Tools
<per tool: purpose, schema summary, irreversible?, confirmation gate>
### 7.4 Retrieval
<the retrieval spec table from rag.md, or "none: <rule>">
### 7.5 Verification step
<what is checked against what; action on unsupported claims>

## 8. Lever plan
| Order | Lever | Applies to rows | Gate status | Conditional on |
|---|---|---|---|---|
| 1 | Prompt engineering | all | always | — |
| 2 | Few-shot | D… | pass / fail (reason) | baseline run |
| 3 | Retrieval | D… | … | baseline run; retrieval-axis eval |
| 4 | Fine-tune | D… | G6.1–G6.5 status | levers 1–3 evaluated |
| 5 | Combine | — | … | … |

## 9. Eval spec
Set size: <n> (≥ 20)    Source: <existing / to produce / from logs>    Hold-out: <n> (if fine-tuning)    Calibration subset: <n ≥ 10> (if judge)
Metric: …    Grid: retrieval + answer (if retrieval)    Tool-call / routing accuracy: <if applicable>    Context sizes: <list> (if long context)
Loop owner: <who runs evaluate → hypothesis → change → re-evaluate>

## 10. Good-enough
### Business worksheet
<table from good-enough.md with the user's figures; break-even p*; placeholder flagged if Q18 defaulted>
### Realistic accuracy estimate and the gap to p*
### Handoff policy
| Failure type | Pattern (clarify / return / human) | Threshold / trigger | Owner |
|---|---|---|---|

## 11. Changes (optimize)
| Change | Artifact | Targets rows | Expected effect | How we will know (eval item ids) |
|---|---|---|---|---|

## 12. Artifacts emitted
| File | Artifact kind | Serves rows | Emit gap |
|---|---|---|---|

## 13. Rollout
Milestone 1: baseline (prompt + eval) → results decide milestones 2+.
Milestone 2: <conditional lever> …
Monitoring: <trace fields; pilot metrics: CSAT / decision accuracy / time to resolution>

## 14. Rejected options
<lever considered → the gate, rule, or Q21/Q22 answer that rejected it → expected accuracy cost>

## 15. Out-of-scope findings
| Row | Layer | Lever | Recommended scope widening | Accuracy forgone if scope is kept |
|---|---|---|---|---|
```

## Review checklist (run before writing the document)

- [ ] Every diagnosis row has measured evidence, not just a tag.
- [ ] Lever 1 is present and the baseline precedes every other lever.
- [ ] Eval set ≥ 20 or an explicit plan to reach 20 before milestone 2.
- [ ] Break-even computed, or the symmetric placeholder flagged in § 2 and § 10 (where § 10 is filled).
- [ ] Every chain step has a budget, a manifest, an abstain output, and a typed output schema.
- [ ] A verification step exists whenever the output makes factual claims from sources.
- [ ] Every irreversible tool has a confirmation gate; forbidden actions are absent from the tool list.
- [ ] § 14 names the rule that rejected each option, including Q21/Q22 refusals with their accuracy cost.
- [ ] No lever contradicts a Q21 fixed item or a Q22 `no` unless flagged as a conflict.
- [ ] Every intake row has a provenance tag; stale profile answers were re-confirmed.
- [ ] § 4a has a row for every prompt read and emitted; emitted prompts are `lean` or `lean (residual out of scope)`; a passing eval means restructuring is justified by cost or maintainability.
- [ ] Every asked question has a reason; no question outside the scope's blocks; no permission confirmed that the design does not rely on.
- [ ] Every diagnosis row names a layer; every out-of-scope row is in § 15; no emitted artifact belongs to an out-of-scope layer.
- [ ] `skill-assignment`: matrix, ledger, gaps and overlaps present; no user-invoked skill assigned to an agent (AS3).
- [ ] Switching the target in § 0 would change only § 12.
