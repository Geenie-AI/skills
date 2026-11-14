# 03 — Decision framework (the accuracy method as rules)

This file is the content of the skill's `reference/decision-framework.md`, `long-context.md`, `rag.md`, `fine-tuning.md`, and `good-enough.md`, planned together so the rules do not overlap. Each rule cites the section of the OpenAI guide it comes from. Rules marked **Beyond the guide** are additions needed for agentic chains and framework emission; keep them separable.

## 1. The two axes (guide § LLM optimization context)

Every requirement and every failure is tagged with exactly one of:

| Axis | What is missing | What it maximizes | Levers, cheapest first |
|---|---|---|---|
| **context** | Knowledge: private, recent, proprietary, or simply absent from the prompt | Response accuracy | Reference text in prompt → external tools → retrieval (RAG) |
| **behavior** | Consistency: format, tone, style, reasoning method | Consistency of behavior | Clear instructions → split into subtasks → time to think → few-shot examples → fine-tuning |
| **both** | Allowed only when the failure evidence shows the information was absent *and* the model would also misuse it when present | — | Combine levers (§ 7) |

Diagnosis question per row (guide § Understanding the tools): *was the needed information in the context at the time?* Yes and still wrong → **behavior** (a "learned memory" problem). No → **context** (an "in-context memory" problem). The skill records the evidence used, never just the tag.

## 2. Lever order and gates (guide § Prompt engineering, § Trade-offs in iteration speed)

The skill proposes levers strictly in this order and may skip a lever only by recording a gate failure:

1. **Prompt engineering** — always first, always present in the design. Tactics table from the guide:

   | Tactic | context | behavior |
   |---|:---:|:---:|
   | Write clear instructions | | ✔ |
   | Split complex tasks into simpler subtasks | ✔ | ✔ |
   | Give the model time to think | | ✔ |
   | Test changes systematically | ✔ | ✔ |
   | Provide reference text | ✔ | |
   | Use external tools | ✔ | |

   Gate to leave this lever: a **baseline** exists — a prompt plus an eval set of ≥ 20 ground-truth items, run, with failures analysed and a hypothesis per failure. The skill writes the eval spec even if the user cannot run it yet; the architecture document marks later levers as *conditional on baseline results*.

2. **Few-shot examples (static)** — when behavior rows exist and ≥ 3 ideal examples are available (Q5). Expect the kind of gain the guide's Icelandic case shows (zero-shot 62 → three-shot 70 BLEU) when the gap is stylistic.

3. **Retrieval** — when context rows exist, the source is too large or too volatile for static inclusion (Q7), and Q22(c) permits it. Read § 5 before designing. Retrieval of *examples* (dynamic few-shot) is allowed for behavior rows when the example pool is large and varied.

4. **Fine-tuning** — when behavior rows survive after levers 1–3, ≥ 50 representative examples exist (Q5), and Q20 and Q22(h) permit it. Read § 6. Second valid reason: efficiency — same accuracy with fewer prompt tokens or a smaller model, when Q15 cost/latency ceilings bind.

5. **Combine** — only when the diagnosis table carries both axes after the baseline. See § 7.

**Deferred questions.** Gates that depend on a fact not yet known (Q15 ceilings, Q17 logs, Q20 data constraints, Q22 item, Q23 upkeep, Q24 tie-break) trigger the question at this point, phrased with the decision it affects ("I want to add runtime retrieval over the policy pages to fix D1 and D4; may the system look documents up at run time?"). The answer is recorded with provenance `asked (deferred)`.

**Permission gate (all levers).** A lever answered `no` in Q22, or conflicting with a fixed item in Q21, is skipped and recorded in doc § 14 with the accuracy cost the skill expects from going without it. A lever answered `ask first` is designed in full but marked *conditional on user confirmation* in the lever plan. The skill never silently drops a needed lever and never silently adds a forbidden one.

Rule from the guide's iteration-speed section, quoted into the skill: *squeeze as much accuracy as possible from basic methods first; let the accuracy target decide, not the appeal of RAG plus fine-tuning.* Both retrieval and fine-tuning add regression risk and a second thing to tune.

## 3. Evaluation design (guide § Evaluation, § RAG evaluation grid)

Every architecture ships an eval spec with:

- **Set**: ≥ 20 items with ground truth; grows from production/pilot logs (Q17). Separate hold-out if fine-tuning is planned.
- **Metric** chosen from Q4: exact match / schema validity for structured outputs; rubric-graded LLM judge (G-Eval style scorecard) for open text; ROUGE/BERTScore only as a drift signal, never as the accuracy number.
- **Grid**: if retrieval is present, score **retrieval** (right chunk in top-k for each item) and **answer** separately, so a failure can be placed on the grid in § 5.
- **Context sizes**: if any step's context exceeds the long-context threshold (§ 4), run the same set at ≥ 2 context sizes and record accuracy at each.
- **Loop**: evaluate → hypothesis per failure → one change → re-evaluate. The skill's optimize mode is one turn of this loop and says so.

## 4. Long context and chains (guide § Long context; **Beyond the guide** for chain rules)

From the guide: long-context models extend prompt engineering, but suffer **lost in the middle**; needle-in-a-haystack shows that dumping everything into context trades simplicity for accuracy. Pair long context with evaluation at multiple sizes.

Rules the skill applies (first two from the guide, rest beyond it):

- **R4.1 Position.** Critical instructions and the question go at the start and are restated at the end. Reference material sits between.
- **R4.2 Multi-size eval.** Any step whose context exceeds the threshold (default 32k tokens; configurable per model from Q2) gets the multi-size eval of § 3.
- **R4.3 Budget per step.** Each step of a chain gets a token budget and a manifest: *what it sees* (instructions, inputs it needs, retrieved items) and *what it is shielded from* (everything else). The default move for a step over budget is to retrieve into it rather than inherit the whole upstream context.
- **R4.4 Structured handoff between steps.** A step passes a typed, minimal intermediate result (schema) to the next step, not its full transcript. This stops error compounding and keeps each step's context small enough to read.
- **R4.5 Fresh context per step.** Where the framework supports it (subagents in Claude Code, handoffs/agents-as-tools in OpenAI Agents SDK, separate calls in the API), each step runs in its own context window. One monolithic prompt becomes a graph of small prompts.
- **R4.6 Verify at the end.** The final step receives the sources (or citations to them) and the draft, and checks each claim against a source; unsupported claims are removed or flagged. This is the guide's "add fact-checking to reduce hallucinations" step made concrete.
- **R4.7 Permission to abstain.** Each step's instructions name the output for "not enough information" so the model has a correct answer other than invention.

## 4a. Prompt audit (**Beyond the guide**; operationalises "split complex tasks into simpler subtasks" and the `writing-for-agents` pruning rules)

The audit runs on **every prompt the skill reads or writes**, in every mode and scope, whether or not failures were reported. It detects overdesign that sits well below the long-context threshold: a prompt carrying too many jobs, too many rules, or too much pasted reference for one call. Findings become diagnosis rows (`A<n>`) with measured evidence, and feed the same lever gates as failure rows.

| ID | Measure | Flag when | Lever |
|---|---|---|---|
| P1 | **Responsibilities**: distinct jobs the prompt asks for (classify, extract, look up, draft, verify, format) | > 2 | Split into steps with typed handoffs (R4.3–R4.5), or a classify-then-route graph (R9.2) |
| P2 | **Instruction count**: imperative rules, counted after merging duplicates | > 25 | Prune no-ops (rules the model follows by default), group by concern, move procedures into a skill the step loads on demand (L2) |
| P3 | **Reference ratio**: reference tokens ÷ instruction tokens, and absolute reference size | ratio > 3 and reference > 2k tokens | Disclose: static reference → skill/reference file; large or changing → tool or retrieval (Q7, R9.1, § 5) |
| P4 | **Duplicates and contradictions**: same rule stated twice; two rules that cannot both be obeyed | any | Single source of truth; contradictions listed for the user to resolve, never silently picked |
| P5 | **Negations without a positive target**: "do not / never" with no stated desired behaviour | > 3, or any on a critical rule | Rewrite as the positive behaviour; keep a prohibition only as a hard guardrail paired with the positive |
| P6 | **Few-shot volume**: examples count and share of prompt tokens | > 5 examples or > 30 % of tokens | Trim to 3 representative; dynamic example retrieval; or the fine-tune gate if behaviour rows persist (§ 6) |
| P7 | **Output contract position**: where the output format and task statement sit | not at the start, or not restated at the end | Reposition (R4.1) |
| P8 | **Abstain path**: a named output for "not enough information" | absent | Add (R4.7) |
| P9 | **Branching**: `if input is X then …` branches serving different input classes | > 3 branches, or branches longer than the shared part | Route: a cheap classification step, then one specialist prompt per class; every branch otherwise pays load on every call |
| P10 | **Instruction size**: tokens of instructions alone, reference excluded | > 4k | Overdesign warning independent of the long-context threshold; apply P1–P3 fixes first |
| P11 | **Mixed audiences**: text addressed to developers, reviewers, or future maintainers inside the model's prompt | any | Move to comments outside the prompt or to the architecture document |
| P12 | **Context inheritance**: the prompt is designed to receive the full transcript or output of earlier steps | yes, and upstream > budget | Typed handoff instead of inheritance (R4.4) |

Thresholds are defaults, recorded in `reference/long-context.md`, and the skill states the measured value next to each flag. Measuring is done by reading the artifact, not by asking the user.

**Verdict.** The audit ends with one of: `lean` (no flags), `dense` (flags on P2, P5–P8, P11 only: fixable in place), `overdesigned` (any of P1, P3, P9, P10, P12: the prompt is doing more than one call should). The verdict goes at the top of doc § 4a.

**Audit rules.**

- **R4a.1 Audit is evidence, not proof of failure.** If an eval exists and the prompt passes it, restructuring is recommended for cost, latency, maintainability, or future-change risk, and the document says so explicitly rather than promising an accuracy gain. The guide's lesson from adding retrieval to an already-learned task applies: match the tool to the problem, and test the change systematically.
- **R4a.2 Structural changes are lever 1.** Splitting, disclosing, repositioning, pruning and adding an abstain path are prompt engineering, so they need no gate beyond permissions (Q21–Q22) and are always followed by the baseline eval.
- **R4a.3 Audit substitutes for failures in a review.** In optimize mode with no observed failures, the audit rows are the diagnosis; the skill says the design is driven by structure, not evidence of failure, and sizes the eval to confirm the change does no harm.
- **R4a.4 Audit the output too.** Every prompt the skill emits is audited before emission; a verdict other than `lean` on an emitted prompt is a build failure for the skill (checked in the scenario evals).
- **R4a.5 Skills and agent definitions get the same audit** with the responsibility measure applied per agent (one responsibility, R9.2) and the reference measures applied to the skill body (disclosure, `writing-for-agents`).

## 5. Retrieval design and the failure grid (guide § RAG)

Retrieval = embed the corpus, embed the question, fetch the most relevant content, pass it to the model. The guide notes many large deployments used only prompt engineering plus retrieval.

Failure grid the skill uses for every retrieval-related failure row:

| Where | Symptom | Fix |
|---|---|---|
| **Retrieval** | Wrong chunks: the model cannot answer | Tune search: chunking, hybrid search, metadata filters, reranking, more context per hit |
| **Retrieval** | Too many irrelevant chunks: the real information is buried, the model hallucinates | Reduce noise: lower k, rerank, filter, deduplicate; raise relevance threshold |
| **LLM** | Right chunks present but misused | Prompt engineering on how to use context (quote-then-answer, cite chunk ids, abstain when unsupported); if examples help, fine-tune |

Design rules:

- **R5.1** Specify how the retrieval axis will be measured before specifying the retriever. Q8 tells the skill whether sample questions can be traced to the document that answers them; if not, the first eval milestone creates that trace for ≥ 20 items.
- **R5.2** Retrieve into the step that needs it (R4.3), never into a global preamble.
- **R5.3** Retrieval can *lower* accuracy on a task the model has already learned: the guide's Icelandic case lost 4 BLEU (87 → 83) when retrieved examples were added to a fine-tuned model. The skill therefore proposes retrieval only against a context-axis row and schedules an eval to confirm it helps.
- **R5.4** Citation requirement (Q7) → grounded generation: the prompt asks for claims with chunk references and the verify step (R4.6) checks them.

## 6. Fine-tuning gates and rules (guide § Fine-tuning)

Purpose: solve learned-memory (behavior) problems by training on a domain-specific set; or reach the same accuracy cheaper.

Gates (all must pass; the skill lists which failed when it declines):

- G6.1 A baseline eval exists and the failing rows are tagged **behavior**.
- G6.2 ≥ 50 high-quality examples exist or can be produced (Q5). Quality over quantity; scale up only if accuracy is still short and the errors remain behavioral.
- G6.3 Examples are **representative** of production inputs, including the system prompt and, if retrieval is present, retrieved context in the same format ("include RAG-style examples so the model does not learn to use context that is not there").
- G6.4 A hold-out set is reserved to detect overfitting.
- G6.5 Q20 and Q22(h) permit training on the data; the target framework offers fine-tuning for the chosen model (see `04-framework-targets.md`).

Dataset source of choice: **prompt baking** — log inputs/outputs from the pilot (Q17), prune to a clean, realistic set.

Expected effect, for calibration: Icelandic case, fine-tuned GPT-3.5 (78) beat few-shot GPT-4 (70); fine-tuned GPT-4 reached 87.

## 7. Combining levers (guide § All of the above)

When the post-baseline diagnosis carries both axes: fine-tuning carries the consistent behavior (and shrinks the prompt by replacing long instructions and examples), retrieval injects specialised or current context. Order of work: tune retrieval first, then retrain on the improved retrieval inputs (the guide's six-step journey, steps 5–6). The skill writes this as two separate milestones with an eval between them.

## 8. Good-enough accuracy (guide § How much accuracy is "good enough")

Off-the-shelf methods rarely reach near-perfect accuracy; the job is to decide when accuracy is sufficient and manage failure risk.

**Business worksheet** (filled from Q18). Replicate the guide's customer-service table:

| Event | Value per case | Expected share | Contribution |
|---|---|---|---|
| Success | +V_s | p | … |
| Failure type 1 (e.g. escalation) | −C_1 | (1−p)·s_1 | … |
| Failure type 2 (e.g. churn) | −C_2 | (1−p)·s_2 | … |
| **Break-even accuracy p\*** | solve contribution = 0 | | |

The guide's example: +$20 success, −$40 escalation, −$1000 churn at 5 % of failures → break-even 81.5 %. Pilot metrics to track: CSAT human vs AI, decision accuracy from retrospective review, time to resolution.

Decision rules:

- If the realistic accuracy from the levers chosen is below p\*, the design keeps the human in the lead and the model as assistant for the risky decision class, and says so.
- If failures are mostly cheap (early escalation), a lower accuracy can still be worth shipping.

**Technical worksheet** (filled from Q19): choose at least one graceful-failure pattern per failure type:

| Pattern | Mechanism | Trade |
|---|---|---|
| Ask for clarification | Model requests more information when unsure | First-attempt accuracy down, two-turn accuracy up |
| Return to an earlier stage | A later agent can send the conversation back to intent detection / routing | Latency |
| Hand off to a human | Below a confidence threshold or on an irreversible action (Q16) | Short-term savings down, churn risk down |

These trade UX speed against accuracy against human cost and feed back into the business worksheet; the skill records the chosen point.

## 9. Agentic additions (**Beyond the guide**)

Needed because the guide addresses single model calls; agentic systems add tools, multi-agent routing, and side effects.

- **R9.1 Tools before retrieval for structured data.** If Q8 shows the missing knowledge lives in a database or API with a known query shape, a tool call (Q22(d)) is a cheaper and more accurate context lever than embedding the data.
- **R9.2 One responsibility per agent.** Split agents by *distinct instructions*, not by volume. An orchestrator routes; specialists act with a fresh context (R4.5). The step graph is inferred from Q10 (how a skilled person does the work) and from the artifacts in optimize mode, never from the user's current agent count; Q22(a)(b) gate whether the inferred graph may be realised as several steps or agents.
- **R9.3 Irreversible actions gate on confirmation.** Anything in Q16 marked irreversible gets a human or policy confirmation step, independent of accuracy.
- **R9.4 Structured outputs at every boundary.** Agent-to-agent and step-to-step payloads use a schema the framework can enforce.
- **R9.5 Traces are the eval source.** Enable the framework's tracing (Q17) from day one; the eval set grows from traces.

## 10. Scope rules (**Beyond the guide**)

The layer model and scope rules SC1–SC8 live in `07-layers-and-scope.md`. The two that bind this file: diagnosis rows always carry a **layer**, and a lever is applied only when its layer is in scope; otherwise the row goes to doc § 15 with the forgone accuracy stated.

## 11. Rejection rules (what the skill refuses to output)

- A design with retrieval or fine-tuning but no baseline step.
- A design without an eval spec, a break-even figure, or a handoff policy.
- In optimize mode, a change not linked to a diagnosis row.
- A multi-step chain without a per-step budget and manifest.
- An emitted prompt whose audit verdict is not `lean` (R4a.4).
- A change to a layer outside the run's scope (Q25), or an out-of-scope root cause that is not flagged at the top of the document (SC3).
- A design that uses a lever the user answered `no` to in Q22, or that changes an item fixed in Q21, without flagging it as a conflict for the user to resolve.
