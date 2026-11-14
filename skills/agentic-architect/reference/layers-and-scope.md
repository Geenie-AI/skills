# Layers and scope

A run may produce or change a single prompt, the skills one agent loads, the assignment of skills to agents, the agent set, the knowledge layer, or the complete system. The **layer model** names the levels; the **scope** of a run is the set of layers it may touch. Diagnosis always looks at every layer; change is confined to the scope.

## Layer model

| Layer | Contains | Typical artifacts | Governed by |
|---|---|---|---|
| **L0 System** | Step graph, orchestration, handoff policy, break-even target, rollout | step graph, handoff policy, rollout plan | `good-enough.md`, R9.x, R4.3–R4.5 |
| **L1 Agents** | Agent definitions: responsibility, model, tools, budget, input/output schema, which skills it may load | agent definition files | R9.2, R4.5, R9.4 |
| **L2 Skills** | Instruction documents an agent loads on demand, and the **assignment** of skills to agents | skill folders (Claude Code); instruction documents + loader (OpenAI, generic) | AS1–AS6 |
| **L3 Prompts** | System prompts, few-shot blocks, output contracts, position rules, abstain outputs | prompt files | levers 1–2, R4.1, R4.7 |
| **L4 Knowledge and tools** | Retrieval components, tool schemas, static reference text, context sources | retrieval spec, tool schemas | `rag.md`, R9.1, R9.3 |
| **L5 Evals and operations** | Eval set, metric, judge, tracing, fine-tune spec | eval files, fine-tune spec | `decision-framework.md` § 3, `fine-tuning.md`, R9.5 |

Layers depend downward: an L0 change usually implies L1–L3 changes; an L3 change never requires L0. A prompt-only run can be correct without touching anything above it, but a system run must regenerate the layers below.

## Scopes

| Scope | Layers touched | Typical request |
|---|---|---|
| `prompt` | L3 (+ L5 eval for that prompt) | "Fix this prompt", "write the system prompt for step 3" |
| `skill` | L2 content (+ L5) | "Write the skill this agent should load", "optimize this SKILL.md" |
| `skill-assignment` | L2 assignment only | "Here are my agents and my skills; who should load what?" |
| `agent` | L1 + L2 + L3 for the named agents, plus the L4 tools and retrieval bound to them (+ L5) | "Design the review agent", "this agent is unreliable" |
| `knowledge` | L4 (+ L5) | "Set up retrieval for the policy corpus", "my tools are misused" |
| `system` | L0–L5 | "Design the whole solution", "this pipeline hallucinates" |
| custom | any subset; two named scopes at once = the union of their rows in every table below | "Prompts and tools only; agents are frozen" |

Default scope: `system` in design mode; in optimize mode, the smallest scope that contains every pasted artifact.

## Scope rules

- **SC1 Diagnose everywhere, change in scope.** The diagnosis table covers all layers regardless of scope, because the root cause of a prompt failure may sit in L0. Changes are emitted only for in-scope layers.
- **SC2 Out-of-scope findings are reported, never applied.** Every diagnosis row whose lever lives outside the scope goes to doc § 15 with the recommended scope widening and the accuracy expected to remain forgone if the scope is kept.
- **SC3 Root cause outside reach is flagged first.** If no in-scope lever can address a diagnosed row, or the lever is blocked by Q21/Q22, say so in the banner at the top of the architecture document before presenting the in-scope work, and still deliver the best in-scope improvement.
- **SC4 Out-of-scope layers are inputs.** Ask for the out-of-scope layers as given (Q26) so the in-scope work fits them. In `skill-assignment` scope both the agent definitions and the skill files are required.
- **SC5 Scope intersects permissions.** Q21–Q22 still apply inside the scope; a `system` scope with Q22(a) = `no` still cannot split steps.
- **SC6 Lower layers regenerate with upper ones.** A `system` or `agent` run re-emits the prompts and skills of the agents it changes; it never leaves a changed agent with a stale prompt.
- **SC7 Evals follow the scope.** Every scope emits an eval spec sized to what changed: a prompt run gets an eval for that prompt's step; a system run gets the full grid.
- **SC8 Audit is scope-independent.** The prompt audit runs on every prompt read in any scope; in `prompt` scope it is the primary diagnostic, and a P1/P9/P12 flag whose fix is a split or a route is an L0 finding reported in doc § 15 when L0 is out of scope.

## Intake eligibility per scope

A ✔ means the block **may** be asked (first of the three asking conditions), not that it will be. Block A and Q25 are always needed and usually derived.

| Block | `prompt` | `skill` | `skill-assignment` | `agent` | `knowledge` | `system` |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| A Mode and target | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| I Scope and given layers | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| B Task and accuracy | ✔ (for the step) | ✔ (for the procedure) | summary only | ✔ (for the agent) | ✔ | ✔ |
| C Knowledge | ✔ | ✔ | — | ✔ | ✔ | ✔ |
| D Consistency | ✔ | ✔ | — | ✔ | — | ✔ |
| E Failures (optimize) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| F Envelope | Q16 only | Q16 only | — | ✔ | ✔ | ✔ |
| G Risk | Q19 only | Q19 only | — | ✔ | Q19 only | ✔ |
| H Permissions | Q21 up front; Q22 items lazily, only those a chosen lever needs (every scope) | same | same | same | same | same |

Questions outside the scope's set are filled from a profile if one is given, otherwise defaulted and listed in § 2 Assumptions.

## Skill assignment (L2)

- **AS1 Match responsibility.** A skill is assigned to the agent whose responsibility its steps serve. A skill whose steps span two responsibilities is reported for splitting before assignment.
- **AS2 Shared reference stays shared.** Reference needed by several agents becomes one model-invoked skill (or one instruction document) that each agent can reach; it is never duplicated into each agent's prompt.
- **AS3 Invocation decides reach.** User-invoked skills cannot be reached by agents; assigning one to an agent is a mistake the skill reports with a fix (make it model-invoked, or leave it for the human). A skill an agent must reach on its own is model-invoked and pays always-loaded context for its description.
- **AS4 Context-load ledger.** For each agent, sum the always-loaded cost: its prompt, its tool descriptions, every always-on instruction file, and the descriptions of every model-invoked skill assigned to it. Compare with the always-loaded budget in `long-context.md`. An agent over budget sheds skills to a sub-agent (an L1 recommendation for doc § 15) or merges skills with overlapping triggers.
- **AS5 Gap and overlap matrix.** Produce an agents × skills matrix. Empty rows (an agent with a responsibility and no procedure) are gaps; columns with two owners and the same trigger are overlaps. List both with a fix. In `skill-assignment` scope, a merge is delivered as one consolidated description, with the body merge listed in doc § 15 as a `skill`-scope follow-up (E7).
- **AS6 Trigger wording is part of assignment.** For a model-invoked skill, rewrite the description's trigger branches so they match the vocabulary of the assigned agent's prompt (leading words shared across prompt and pointer).

## Output per scope

| Scope | `architecture.md` sections filled | Artifacts |
|---|---|---|
| `prompt` | 0–4a, 5 (rows for this step), 6 (this step), 8, 9, 11, 12, 14, 15 | the prompt file(s), eval for the step |
| `skill` | 0–4a, 5, 8, 9, 11, 12, 14, 15 | skill folder or instruction documents |
| `skill-assignment` | 0–4a, 5, 6 (ledger), 7.2a, 11, 12, 14, 15 | updated agent definitions (skill lists) and rewritten skill descriptions |
| `agent` | 0–4a, 5, 6, 7.2–7.5 (for the agent), 8, 9, 10 (handoff for this agent), 11, 12, 14, 15 | agent definition, its prompt, its skills, its tools, its retrieval |
| `knowledge` | 0–4a, 5, 6, 7.3–7.5, 8, 9, 11, 12, 14, 15 | retrieval spec, tool schemas, verify-step prompt |
| `system` | all | all |

Sections 4 and 11 are filled in optimize mode and marked `n/a (design)` otherwise. Sections not filled are marked `n/a (scope)` so the document shape is constant.
