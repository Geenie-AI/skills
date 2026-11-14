# Decision framework: the accuracy method as rules

Each rule cites the section of OpenAI's *Optimizing LLM Accuracy* guide it comes from (https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy). Rules marked **Beyond the guide** are additions for agentic chains and framework emission. Related files: `long-context.md` (R4.x chain rules, thresholds), `rag.md` (retrieval grid, R5.x), `fine-tuning.md` (G6.x gates, combining levers), `good-enough.md` (break-even, handoff patterns).

## 1. The two axes (guide § LLM optimization context)

Tag every requirement and every failure with exactly one axis:

| Axis | What is missing | What it maximizes | Levers, cheapest first |
|---|---|---|---|
| **context** | Knowledge: private, recent, proprietary, or absent from the prompt | Response accuracy | Reference text in prompt → external tools → retrieval |
| **behavior** | Consistency: format, tone, style, reasoning method | Consistency of behavior | Clear instructions → split into subtasks → time to think → few-shot examples → fine-tuning |
| **both** | Only when the evidence shows the information was absent *and* the model would also misuse it when present | — | Combine levers (`fine-tuning.md` § Combining) |

Diagnosis question per row (guide § Understanding the tools): *was the needed information in the context at the time?*

- Yes, and still wrong → **behavior** (a learned-memory problem).
- No → **context** (an in-context-memory problem).
- Present, but beyond the model's effective window: past the long-context threshold or far from the instructions → **context** (lost in the middle). The evidence column must cite the measured size and position.

Record the evidence used, never just the tag.

## 2. Lever order and gates (guide § Prompt engineering, § Trade-offs in iteration speed)

Propose levers strictly in this order. Skip a lever only by recording a gate failure in doc § 14.

1. **Prompt engineering**: always first, always present. Tactics from the guide:

   | Tactic | context | behavior |
   |---|:---:|:---:|
   | Write clear instructions | | ✔ |
   | Split complex tasks into simpler subtasks | ✔ | ✔ |
   | Give the model time to think | | ✔ |
   | Test changes systematically | ✔ | ✔ |
   | Provide reference text | ✔ | |
   | Use external tools | ✔ | |

   Gate to leave this lever: a **baseline** exists: a prompt plus an eval set of ≥ 20 items, run, with failures analysed and a hypothesis per failure. Write the eval spec even if the user cannot run it yet, and mark later levers *conditional on baseline results*.

2. **Few-shot examples (static)**: when behavior rows exist and ≥ 3 ideal examples are available (Q5). Examples are written in the output language (Q9). Expect the kind of gain the guide's Icelandic case shows (zero-shot 62 → three-shot 70 BLEU) when the gap is stylistic.

3. **Retrieval**: when context rows exist, the source is too large or too volatile for static inclusion (Q7), and Q22(c) permits it. Read `rag.md` first. Retrieval of *examples* (dynamic few-shot) is allowed for behavior rows when the example pool is large and varied.

4. **Fine-tuning**: when behavior rows survive after levers 1–3, ≥ 50 representative examples exist (Q5), and Q20 and Q22(h) permit it. Read `fine-tuning.md`. Second valid reason: efficiency, the same accuracy with fewer prompt tokens or a smaller model when Q15 ceilings bind.

5. **Combine**: only when the diagnosis carries both axes after the baseline. See `fine-tuning.md` § Combining.

**Deferred questions.** A gate that depends on an unknown fact (Q15, Q17, Q20, a Q22 item, Q23, Q24) triggers the question now, phrased with the decision it affects. Record the answer as `asked (deferred)`.

**Permission gate (all levers).** A lever answered `no` in Q22, or conflicting with a fixed item in Q21, is skipped and recorded in doc § 14 with the accuracy cost expected from going without it. A lever answered `ask first` is designed in full and marked *conditional on user confirmation*. Never silently drop a needed lever; never silently add a forbidden one.

Rule from the guide's iteration-speed section: *squeeze as much accuracy as possible from basic methods first; let the accuracy target decide, not the appeal of retrieval plus fine-tuning.* Both add regression risk and a second thing to tune.

## 3. Evaluation design (guide § Evaluation, § RAG evaluation grid)

Every architecture ships an eval spec with:

- **Set**: ≥ 20 items; grows from pilot or production logs (Q17). Separate hold-out if fine-tuning is planned. Items are in the output language (Q9).
- **Ground truth per metric type**: a reference answer for exact match and schema checks; for rubric-graded outputs, a rubric plus a human-labelled calibration subset of ≥ 10 items used to check judge agreement; pairwise preference when no single correct output exists.
- **Metric** from Q4: exact match or schema validity for structured outputs; rubric-graded LLM judge for open text; ROUGE or BERTScore only as a drift signal. Add **tool-call accuracy** (right tool, valid arguments) when the step calls tools and **routing accuracy** when a step routes.
- **Grid**: if retrieval is present, score **retrieval** (right chunk in top-k) and **answer** separately, so a failure lands on the grid in `rag.md`.
- **Context sizes**: if any step's context exceeds the long-context threshold (`long-context.md`), run the set at ≥ 2 context sizes.
- **Loop**: evaluate → hypothesis per failure → one change → re-evaluate. Optimize mode is one turn of this loop and says so.

## 4a. Prompt audit (**Beyond the guide**)

Run the audit on **every prompt read or written**, in every mode and scope, with or without reported failures. The audit set for a step is its prompt **plus every always-on instruction file the host loads** (`CLAUDE.md`, `AGENTS.md`, rules files). Findings become diagnosis rows `A<n>` with measured evidence and feed the same gates as failure rows. Measure by reading the artifact, never by asking.

| ID | Measure | Flag when | Lever |
|---|---|---|---|
| P1 | **Responsibilities**: distinct jobs asked for (classify, extract, look up, draft, verify, format) | > 2 (> 1 per agent definition, R9.2) | Split into steps with typed handoffs (R4.3–R4.5) or classify-then-route (R9.2) |
| P2 | **Instruction count**: imperative rules after merging duplicates | > 25 | Prune no-ops, group by concern, move procedures into an instruction document loaded on demand |
| P3 | **Reference ratio**: reference tokens ÷ instruction tokens; absolute reference size | ratio > 3 **or** reference > 2k tokens | Disclose: static → reference file; large or changing → tool or retrieval (R9.1, `rag.md`) |
| P4 | **Duplicates and contradictions** across the audit set | any | Single source of truth; contradictions listed for the user, never silently picked |
| P5 | **Negations without a positive target**: "do not / never" with no desired behaviour stated | > 3, or any on a critical rule | Rewrite as the positive behaviour; keep a prohibition only as a guardrail paired with the positive |
| P6 | **Few-shot volume**: example count and share of tokens | > 5 examples or > 30 % of tokens | Trim to 3 representative; dynamic example retrieval; or the fine-tune gates if behavior rows persist |
| P7 | **Output contract position** | not at the start, or not restated at the end | Reposition (R4.1) |
| P8 | **Abstain path**: a named output for "not enough information" | absent | Add (R4.7) |
| P9 | **Branching**: `if input is X then …` branches serving different input classes | > 3, or branches longer than the shared part | Route: cheap classification step, then one specialist prompt per class |
| P10 | **Instruction size**: instruction tokens, reference excluded | > 4k | Overdesign warning independent of the long-context threshold; apply P1–P3 fixes first |
| P11 | **Mixed audiences**: text addressed to developers or maintainers inside the prompt | any | Move to comments outside the prompt or to the architecture document |
| P12 | **Context inheritance**: the prompt receives the full transcript or output of earlier steps | yes, and upstream > budget | Typed handoff instead of inheritance (R4.4) |
| P13 | **Task statement present** at the start | absent | Add (R4.1) |
| P14 | **Output contract present** (format, schema, or explicit free-text statement) | absent | Add (R9.4) |
| P15 | **Required reference present or disclosed**: every context row's source is in the prompt, in a loaded document, or reachable by a tool | any source unreachable | Provide reference text, a tool, or retrieval (§ 1 context levers) |

State the measured value next to each flag. Thresholds are defaults; `long-context.md` holds the per-model context thresholds.

**Verdict**, placed at the top of doc § 4a:

- `lean`: no flags.
- `lean (residual out of scope)`: the only flags are P1, P9, or P12 whose fix lives in a layer outside the run's scope and is listed in doc § 15.
- `dense`: flags on P2, P4–P8, P11 only; fixable in place.
- `overdesigned`: any of P1, P3, P9, P10, P12 with the fix in scope; the prompt does more than one call should.
- `sparse`: any of P13–P15; the prompt is under-specified for the task.

Audit rules:

- **R4a.1 Audit is evidence, not proof of failure.** If an eval exists and the prompt passes it, recommend restructuring for cost, latency, maintainability, or change risk, and say so explicitly rather than promising an accuracy gain. Match the tool to the problem and test the change systematically.
- **R4a.2 Structural changes are lever 1.** Splitting, disclosing, repositioning, pruning, and adding an abstain path are prompt engineering: no gate beyond permissions (Q21–Q22), always followed by the baseline eval.
- **R4a.3 Audit substitutes for failures in a review.** In optimize mode with no observed failures, the audit rows are the diagnosis; say the design is driven by structure, not evidence of failure, and size the eval to confirm the change does no harm.
- **R4a.4 Audit the output too.** Audit every prompt before emitting it; a verdict other than `lean` or `lean (residual out of scope)` on an emitted prompt is a build failure. Fix and re-audit before emitting.
- **R4a.5 Skills and agent definitions get the same audit**, with P1 applied per agent (one responsibility) and the reference measures applied to the skill body.

## 9. Agentic additions (**Beyond the guide**)

The guide addresses single model calls; agentic systems add tools, routing, and side effects.

- **R9.1 Tools before retrieval for structured data.** If Q8 shows the missing knowledge lives in a database or API with a known query shape, a tool call (Q22(d)) is a cheaper and more accurate context lever than embedding the data.
- **R9.2 One responsibility per agent.** Split agents by *distinct instructions*, not by volume. An orchestrator routes; specialists act in a fresh context (R4.5). Infer the step graph from Q10 and, in optimize mode, from the artifacts, never from the user's current agent count; Q22(a)(b) gate whether the graph may be realised as several steps or agents.
- **R9.3 Irreversible actions gate on confirmation.** Anything Q16 marks irreversible gets a human or policy confirmation step, independent of accuracy. Actions the system must never take are absent from the tool list entirely.
- **R9.4 Structured outputs at every boundary.** Agent-to-agent and step-to-step payloads use a schema the framework can enforce; where it cannot, name the validation step.
- **R9.5 Traces are the eval source.** Enable the framework's tracing (Q17) from day one; the eval set grows from traces.
- **R9.6 Tool-selection failures.** Wrong tool chosen or malformed arguments: measure tool count and description overlap per step; levers are description rewrite (when to call, when not to, what each argument means), strict argument schemas, and fewer tools per step. Metric: tool-call accuracy.
- **R9.7 Orchestration failures.** State lost between agents → typed handoff (R4.4); misrouting → routing eval and a classify step with a schema; over-decomposition (steps that only forward) → merge steps; handoff loops → a maximum hop count and a return-to-stage rule.
- **R9.8 Latency ceiling.** When Q15 binds, apply in order: run independent steps in parallel, merge adjacent steps that share context, use a smaller model for routing and extraction, move verification to sampled or asynchronous checks. State the accuracy expected to be forgone for each.

## 10. Scope

Diagnosis rows always carry a **layer**, and a lever is applied only when its layer is in scope; otherwise the row goes to doc § 15 with the forgone accuracy stated. Layer model, scope rules SC1–SC8, and assignment rules AS1–AS6 are in `layers-and-scope.md`.

## 11. Rejection rules (what the skill refuses to output)

- A design with retrieval or fine-tuning but no baseline step.
- A design without an eval spec; in any scope that fills doc § 10, a design without a break-even figure or a handoff policy.
- In optimize mode, a change not linked to a diagnosis row.
- A multi-step chain without a per-step budget and manifest.
- An emitted prompt whose audit verdict is not `lean` or `lean (residual out of scope)` (R4a.4).
- A change to a layer outside the run's scope, or an out-of-scope or permission-blocked root cause that is not flagged at the top of the document (SC3).
- A design that uses a lever the user answered `no` to in Q22, or changes an item fixed in Q21, without flagging the conflict for the user to resolve.
- A comparison of two user-supplied candidate designs as a ranking: out of scope. Offer instead to diagnose each against one shared eval spec.
