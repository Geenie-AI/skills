# 07 — Layers and scope

The skill works at any level of an agentic solution. A run may produce or change a single prompt, the skills one agent loads, the assignment of skills to agents, the agent set, or the complete system. The **layer model** names the levels; the **scope** of a run is the set of layers it may touch. Diagnosis always looks at every layer; change is confined to the scope.

## Layer model

| Layer | Contains | Typical artifacts | Governed by |
|---|---|---|---|
| **L0 System** | Step graph, orchestration, handoff policy, break-even target, rollout | step graph, handoff policy, rollout plan | 03 § 8, 03 § 9, R4.3–R4.5 |
| **L1 Agents** | Agent definitions: responsibility, model, tools, budget, input/output schema, which skills it may load | agent definition files | R9.2, R4.5, R9.4 |
| **L2 Skills** | Instruction documents an agent loads on demand: procedures, reference, templates; and the **assignment** of skills to agents | `SKILL.md` + reference files (Claude); instruction documents + loader tool (OpenAI); plain Markdown (generic) | `writing-for-agents`, "Skill assignment" below |
| **L3 Prompts** | System prompts, few-shot blocks, output contracts, position rules, abstain outputs | prompt files | 03 § 2 levers 1–2, R4.1, R4.7 |
| **L4 Knowledge and tools** | Retrieval components, tool schemas, static reference text, context sources | retrieval spec, tool schemas | 03 § 5, R9.1, R9.3 |
| **L5 Evals and operations** | Eval set, metric, judge, tracing, fine-tune spec | eval files, fine-tune spec | 03 § 3, 03 § 6, R9.5 |

Layers depend downward: an L0 change usually implies L1–L3 changes; an L3 change never requires L0. The dependency is what makes scoping safe: a prompt-only run can be correct without touching anything above it, but a system run must regenerate the layers below.

## Scopes

A scope is a named set of layers. Named scopes cover the common requests; a custom scope is any subset.

| Scope name | Layers touched | Typical request |
|---|---|---|
| `prompt` | L3 (+ L5 eval for that prompt) | "Fix this prompt", "write the system prompt for step 3" |
| `skill` | L2 content (+ L5) | "Write the skill this agent should load for X", "optimize this SKILL.md" |
| `skill-assignment` | L2 assignment only | "Here are my agents and my skills; who should load what?" |
| `agent` | L1 + L2 + L3 for one or more named agents (+ L5) | "Design the review agent", "this agent is unreliable" |
| `knowledge` | L4 (+ L5) | "Set up retrieval for the policy corpus", "my tools are misused" |
| `system` | L0–L5 | "Design the whole solution", "this pipeline hallucinates" |
| custom | any subset | "Prompts and tools only; agents are frozen" |

Default scope is `system` in design mode and, in optimize mode, the smallest scope that contains every pasted artifact.

## Rules

- **SC1 Diagnose everywhere, change in scope.** The diagnosis table covers all layers regardless of scope, because the root cause of a prompt failure may sit in L0 (the step receives too much context). Changes are emitted only for in-scope layers.
- **SC2 Out-of-scope findings are reported, never applied.** Every diagnosis row whose lever lives outside the scope goes to `architecture.md doc § 15 Out-of-scope findings`, with the recommended scope widening and the accuracy expected to remain forgone if the user keeps the scope.
- **SC3 Root cause outside scope is flagged first.** If no in-scope lever can address a diagnosed row, the skill says so at the top of the architecture document before presenting the in-scope work, and still delivers the best in-scope improvement.
- **SC4 Out-of-scope layers are inputs.** The skill asks for the out-of-scope layers as given (the agent list, the existing prompts, the available tools) so the in-scope work fits them. In `skill-assignment` scope it needs both the agent definitions and the skill files.
- **SC5 Scope intersects permissions.** Q21–Q22 still apply inside the scope; a `system` scope with Q22(a) = `no` still cannot split steps.
- **SC6 Lower layers regenerate with upper ones.** A `system` or `agent` run re-emits the prompts and skills of the agents it changes; it never leaves a changed agent with a stale prompt.
- **SC8 Audit is scope-independent.** The prompt audit (03 § 4a) runs on every prompt read in any scope; in `prompt` scope it is the primary diagnostic, and a P1/P9/P12 flag whose fix is a split or a route is an L0 finding reported in doc § 15 if L0 is out of scope.
- **SC7 Evals follow the scope.** Every scope emits an eval spec sized to what changed: a prompt run gets an eval for that prompt's step; a system run gets the full grid.

## Intake per scope

The fact set is fixed, but blocks become *eligible* by scope; eligibility is the first of the three asking conditions in `02-intake-questions.md` (in scope, underived, decision-relevant). A ✔ below means the block may be asked, not that it will be. Block A and the scope question are always needed but are usually derived from the request.

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
| H Permissions | Q21 only | Q21 only | Q21 only | ✔ | Q21–Q22(c)(d) | ✔ |

Questions outside the scope's set are filled from a profile if one is given, otherwise defaulted and listed in § 2 Assumptions.

## Skill assignment (L2)

Assignment is its own task and follows the `writing-for-agents` mechanics:

- **AS1 Match responsibility.** A skill is assigned to the agent whose responsibility its steps serve. A skill whose steps span two responsibilities is split before assignment.
- **AS2 Shared reference stays shared.** Reference needed by several agents becomes one model-invoked skill (or, for OpenAI/generic, one instruction document) that each agent can reach; it is never duplicated into each agent's prompt.
- **AS3 Invocation decides reach.** User-invoked skills (no description) cannot be reached by agents; assigning one to an agent is a mistake the skill reports. A skill an agent must reach on its own is model-invoked and pays always-loaded context for its description.
- **AS4 Context-load ledger.** For each agent, sum the always-loaded cost: its prompt, its tool descriptions, and the descriptions of every model-invoked skill assigned to it. The ledger goes in § 6 Context budget. An agent over budget sheds skills to a sub-agent or merges skills with overlapping triggers.
- **AS5 Gap and overlap matrix.** Produce an agents × skills matrix. Empty rows (an agent with a responsibility and no procedure) are gaps; columns with two owners and the same trigger are overlaps. Both are listed with a fix.
- **AS6 Trigger wording is part of assignment.** For a model-invoked skill, the description's trigger branches are rewritten so they match the vocabulary of the assigned agent's prompt (leading words shared across prompt and pointer).

Framework notes: on Claude Code, assignment is literal (a subagent's prompt names the skills it may use, and the skills live where that agent can load them). On OpenAI, "assignment" means which agent holds the loader tool or the `file_search` store that contains the instruction document, and the instructions mention when to load it. On generic targets, it is a declared list per agent.

## Output per scope

| Scope | `architecture.md` sections filled | Artifacts |
|---|---|---|
| `prompt` | 0–3, 5 (rows for this step), 6 (this step), 8, 9, 12, 14, 15 | the prompt file(s), eval for the step |
| `skill` | 0–3, 5, 8, 9, 12, 14, 15 | `SKILL.md` + reference files (or instruction documents) |
| `skill-assignment` | 0–2, 5, 6 (ledger), 7.2 (assignment matrix), 12, 14, 15 | updated agent definitions (skill lists) and rewritten skill descriptions |
| `agent` | 0–3, 5, 6, 7.2–7.3, 8, 9, 10 (handoff for this agent), 12, 14, 15 | agent definition, its prompt, its skills, its tools |
| `knowledge` | 0–3, 5, 6, 7.3–7.5, 8, 9, 12, 14, 15 | retrieval spec, tool schemas, verify-step prompt |
| `system` | all | all |

Sections not filled are marked `n/a (scope)` so the document shape is constant.
