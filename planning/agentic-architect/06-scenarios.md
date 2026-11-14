# 06 — Scenarios (acceptance tests for the skill)

Each scenario names its scope (`07-layers-and-scope.md`); S1–S7 run in `system` scope unless stated. Each scenario gives the input the skill receives, the diagnosis it must reach, the design it must produce, and the checks a reviewer runs. S1 and S2 are the two cases named in the original request.

## S1 — Massive chained prompt with very large context hallucinates at the end (optimize mode)

**Input.** One system prompt of ~9k tokens containing instructions for five sequential tasks (extract → classify → enrich from policy documents → draft response → format). The whole policy corpus (~90k tokens) is pasted into the prompt. Everything runs in a single call, or as five calls that each inherit the entire prior transcript. Failures: the final drafted response cites policy clauses that do not exist, and the formatting step sometimes ignores the schema. User tried "adding 'do not hallucinate' and a stronger instruction at the top"; no improvement.

**Expected intake findings.** The artifacts pasted in Q1 reveal five tasks inside one prompt, and Q10 (how a person does it) confirms five distinct activities with a lookup in the middle; Q22 answers `yes` to (a)–(e) and (g), `ask first` to (h)–(j); Q21 fixes nothing; Q13 shows the failure first appears at step 4 with ~100k tokens in context; Q12 answers "the information was present" for the invented clauses (the real clause was in the corpus) and "n/a" for the format failures; Q5 gives 0 ground-truth examples; Q7 says the corpus changes monthly and answers must cite clause ids.

**Expected diagnosis.**

| ID | Failure | Present? | Axis | Lever | Evidence |
|---|---|---|---|---|---|
| D1 | Invented clause citations in step 4 | yes, buried | context (lost in the middle) | split + retrieval into step 3/4 (R4.3, R5.2) | 100k-token context; needle far from instructions |
| D2 | Same, model also ignores "do not hallucinate" | yes | behavior | prompt: quote-then-answer, abstain output (R4.7), verify step (R4.6) | negated instruction had no effect; no abstain path existed |
| D3 | Format step ignores schema | n/a | behavior | structured output at boundary (R9.4), fresh context (R4.5) | schema was 8k tokens upstream of the output |
| D4 | No eval exists; cannot tell if changes help | — | — | baseline eval of ≥ 20 items with clause-id ground truth (03 § 3) | Q5 = 0 |

**Expected design.**

- Split into five steps, each its own agent/call with a fresh context and a typed output schema (R4.4, R4.5). Step graph: extract → classify → retrieve-and-enrich → draft → verify-and-format.
- Policy corpus moves out of the prompt into a retrieval component queried **by step 3 only**, with clause ids returned as citation keys; k small, filtered by the classification from step 2 (R5.2, R5.4).
- Step 4 prompt: contract first, retrieved clauses in the middle with ids, contract restated last; output requires `claims[]` each with `clause_id`; abstain value `"no_supporting_clause"` (R4.1, R4.7).
- New step 5 verify: for each claim, the clause text is fetched by id and the claim is checked; unsupported claims removed; then format with enforced schema (R4.6, R9.4).
- Per-step budget table with each step ≤ ~8k tokens; multi-size eval scheduled for step 4 (R4.2).
- Eval spec: 20+ items with ground-truth clause ids; retrieval axis scored separately (does the right clause appear in top-k?) and answer axis (are all cited clauses real and relevant?).
- Lever plan: prompt + split (now), retrieval (now, because the corpus is large and changing: a context-axis row), few-shot (conditional on baseline), fine-tuning (rejected: G6.1 no baseline, G6.2 no examples).
- Good-enough: break-even from Q18; handoff: unsupported claim count > 0 after verification → return to step 3 with a widened query once, then human review.

**Checks.** Diagnosis contains at least one row tagged context with the lost-in-the-middle evidence and one tagged behavior; the design has five fresh-context steps; retrieval is attached to one step only; a verify step exists; the eval has a retrieval axis; fine-tuning is in doc § 14 with the gates that failed; every change in doc § 11 maps to D1–D4.

## S1b — Same scenario, permissions refused (constraint handling)

**Input.** S1, but Q21 fixes "one agent, one call" and Q22 answers `no` to (a), (b) and (c), `yes` to (d), (e), (g).

**Expected.** Diagnosis identical to S1. Design stays in one call: corpus moved out of the prompt into a tool the model calls for clause text by id (Q22(d), R9.1), instruction position fixed (R4.1), abstain output added (R4.7), in-call self-check using the tool (R4.6 within the constraint), structured output enforced. doc § 14 records: split and runtime retrieval rejected by Q22(a)(c), with the expected cost that step-4 context remains large and multi-size eval (R4.2) is mandatory. The lever plan marks "split into steps" as the first recommendation should the user relax Q22.

**Checks.** No multi-agent or multi-step artifact emitted; doc § 14 cites Q22(a)(c); the accuracy cost is stated; multi-size eval is in the eval spec.

## S2 — New situation: internal helpdesk agent for an HR policy portal (design mode)

**Input.** No existing artifacts. Employees ask HR questions in chat; the agent should answer from ~400 policy pages that change quarterly, open a ticket when it cannot answer, and never change payroll data. Target: OpenAI Agents SDK. ~2,000 questions/day. Value of a correct self-service answer ≈ $15; a wrong answer accepted by an employee ≈ −$200 (rework, complaints); an unnecessary ticket ≈ −$10. 30 examples exist from past tickets. The user's own description is "a chatbot with one big prompt"; Q22 is all `yes` except (h) `ask first` and (i) `no`.

**Expected diagnosis.** Context rows (policy knowledge: large, quarterly → retrieval, permitted by Q22(c); ticket creation → tool, Q22(d)). The user's "one big prompt" framing is not a constraint (Q21 empty) and does not appear in the design. Behavior rows (answer format with citation, consistent refusal on payroll changes, tone). No failures yet.

**Expected design.** Triage agent → `policy_answer` agent (file_search over a vector store with metadata by policy area, k ≈ 5, structured output with citations and `confidence`) → `ticket` agent (function tool; irreversible? no: ticket creation is reversible, no gate) ; payroll actions absent from the tool list entirely (R9.3 by omission) plus an output guardrail. Baseline: prompt + the 30 examples as the first eval set (grow to 50 from traces). Break-even: with failure split estimated 70 % ticket / 30 % wrong-answer-accepted, p\* computed and shown; if p\* > realistic accuracy, the design routes low-confidence answers to a ticket (clarify-then-handoff pattern) and recomputes. Fine-tuning: deferred to milestone 3, conditional on behavior failures surviving few-shot and on 50+ examples from traces (G6.2).

**Checks.** Architecture has three agents with one responsibility each; retrieval attached only to the answering agent; eval spec sizes 30 now with a plan to reach 50; break-even table filled with the given figures; handoff policy includes a confidence threshold; doc § 14 lists fine-tuning as deferred with the gate.

## S3 — Behavior gap with plenty of examples (optimize mode, fine-tune path)

**Input.** A translation-and-style agent produces correct content but inconsistent house style across 1,200 logged outputs, 600 of which have been human-corrected. Few-shot with 5 examples helped but the prompt is now 6k tokens and latency/cost ceilings bind (Q15). Target: OpenAI Responses API.

**Expected.** All rows behavior; lever 2 already applied; G6.1–G6.5 pass (600 corrected pairs, representative, hold-out reserved). Design recommends supervised fine-tuning on the corrected pairs in the exact production format, replacing the few-shot block (efficiency reason from § 2 lever 4), with the prompt-baking pipeline described and an eval before/after on the hold-out. Retrieval is explicitly rejected (R5.3: no context rows; the Icelandic −4 point example cited).

**Checks.** Fine-tune spec file is emitted; retrieval appears in doc § 14 with R5.3; the eval spec has a hold-out.

## S4 — Fine-tuning requested but not warranted (design mode)

**Input.** User asks for "a fine-tuned model" for a code-review agent on a private repo; 8 examples exist; the misses are all about repository conventions that are written in a `CONTRIBUTING.md`.

**Expected.** Rows are context (conventions absent from the prompt). Design: include the conventions document as reference text (small, stable → static inclusion, Q7), tools for reading the repo, baseline eval. Fine-tuning rejected on G6.1 (rows are context) and G6.2 (8 < 50). Target Claude Code → emits a `CLAUDE.md` pointer and a reviewing skill with disclosed reference.

**Checks.** No fine-tune spec emitted; doc § 14 cites G6.1 and G6.2; Claude artifacts follow `writing-for-agents` shape.

## S5 — Same design, different target (emit isolation)

**Input.** S2 rerun with target = Claude Agent SDK, then target = generic.

**Expected.** Sections 1–11 identical to S2 except § 0 target; doc § 12 changes: subagents instead of Agents SDK agents, a retrieval tool/MCP server instead of `file_search`, fine-tuning marked "not available on this target" with lever 4 replaced by examples/retrieval, generic target emits the step graph and schemas.

**Checks.** Diff of `architecture.md` between runs touches only § 0 and doc § 12.

## S6 — Missing answers (robustness)

**Input.** S2 with Q18 and Q19 answered `unknown`.

**Expected.** Skill proceeds; § 2 lists the symmetric placeholder for Q18 and "human reviews everything" for Q19; § 10 shows a 50 % break-even flagged as placeholder and tells the user it is the first thing to replace.

**Checks.** Run completes; placeholders are flagged, not silently used.

## S7 — Profile ID auto-answers the intake (provenance and reproducibility)

**Input.** `/agentic-architect --profile acme-helpdesk`, where the profile holds the S2 answers for Q2–Q10 and Q15–Q24, with Q18 dated 100 days ago and a 90-day staleness window. Mode is not in the profile.

**Expected.** The skill resolves the profile from the repo store, fills the table with `source: profile:acme-helpdesk` on each row, derives Q1 = design from the request wording ("design the helpdesk agent"), and asks only Q18 (stale, shown with its date, deferred to the good-enough step). When it is about to propose retrieval and a ticket tool, it shows back Q22(c) and (d) only, and asks for confirmation. After the user answers "keep" and "confirm", the resulting `architecture.md` is identical to S2's in §§ 3–14; doc § 1 differs only in the provenance column and § 0 shows the profile ID. At the end, the skill offers to write the confirmed Q18 date back to the profile.

**Variant.** Same profile, mode = optimize. The skill additionally asks Q11–Q14 fresh, even though the profile could in principle point at a trace export; if it does, the skill proposes failure rows from the export and asks the user to confirm each.

**Checks.** Diagnosis table identical to S2; every doc § 1 row carries `source` and `at`; Q1 was derived, not asked; only Q22(c)(d) were confirmed; Q18 was re-asked; in the optimize variant Q11–Q14 were asked; no write to any external system occurred.

## S8 — Prompt-only scope with an out-of-scope root cause

**Input.** Optimize mode, scope `prompt`: "fix the drafting prompt" of the S1 pipeline. The user pastes only that prompt (Q26: the other steps are described in one line each; the corpus is still pasted upstream). Failures as in S1.

**Expected.** Diagnosis identical to S1 across all layers. The document opens with the S3 banner: root cause is L0 (step 4 inherits ~100k tokens; split and per-step retrieval are out of scope). In-scope work still delivered: the prompt rewritten with R4.1 positioning, an abstain output (R4.7), a quote-then-cite contract, and a step-level eval of ≥ 20 items. doc § 15 lists D1 and D3 with the recommended widening to `system` (or `agent` for steps 3–5) and the forgone accuracy. No agent, retrieval, or orchestration artifact is emitted.

**Checks.** Only prompt and eval files emitted; banner present; doc § 15 has the L0 rows; intake asked Blocks A, I, B, C, D, E, Q16, Q19, Q21 only.

## S9 — Skill assignment for an existing agent set

**Input.** Scope `skill-assignment`, target Claude Code. Q26 supplies four subagent definitions (triage, researcher, drafter, reviewer) and nine skills, two of them user-invoked, three with overlapping trigger wording ("summarize", "summarise the findings", "condense"). Design mode; no failures.

**Expected.** Agents × skills matrix with one owner per skill (AS1); the three overlapping skills merged into one model-invoked skill reachable by researcher and drafter (AS2, AS5); the two user-invoked skills reported as unreachable by any agent with a fix (make model-invoked, or leave for the human) (AS3); a context-load ledger per agent, with the reviewer shown over budget and one skill moved to a sub-agent (AS4); rewritten descriptions whose trigger words match the owning agent's prompt vocabulary (AS6). Emitted artifacts: four updated subagent files (skill lists) and the rewritten skill descriptions. No skill bodies, prompts beyond the skill-list lines, or orchestration changes.

**Checks.** Matrix, ledger, gap/overlap lists present; doc § 15 empty or limited to L0/L1 observations; no `SKILL.md` body emitted; E8 applied for Claude Code.

## S10 — Agent scope inside a frozen system

**Input.** Scope `agent`, OpenAI Agents SDK: "the researcher agent is unreliable". Q26 gives the orchestrator, the other agents, and the handoff graph as frozen. Failures: the researcher returns unsupported claims and sometimes the wrong output shape.

**Expected.** Diagnosis across layers; the handoff graph is found adequate (L0 rows none). In-scope changes: the researcher's instructions (R4.1, R4.7), its `output_type` schema (R9.4), a `file_search` tool attached to it with k and filters (R5.2, Q22(c)), a verification sub-step inside the agent (R4.6), its instruction documents re-emitted (SC6), and an eval for the researcher's step with a retrieval axis. Orchestrator and sibling agents untouched.

**Checks.** Only researcher artifacts and the eval emitted; the handoff graph in § 7.1 is marked `given`; doc § 15 empty.

## S11 — Minimal asking (derivation and lazy questions)

**Input A.** Optimize mode, scope `prompt`, no profile. The request: "This drafting prompt cites policy clauses that don't exist. Here is the prompt [9k tokens pasted] and three examples of bad output with what we wanted. We're on Claude Code." Working directory contains `.claude/agents/` and a `policies/` folder of ~400 Markdown files.

**Expected.** Derived without asking: Q1 (optimize), Q2 (Claude Code, from request and `.claude/`), Q3 (from the prompt's own task statement), Q6/Q7 size (policies folder measured), Q9 (output contract read from the prompt), Q11 (three failures given), Q12 (skill checks whether the cited clauses exist in `policies/` → answers "present but misused" or "absent" itself), Q13 (context size measured from the artifact), Q16 (tools named in the prompt), Q25 (`prompt`, from "this drafting prompt"). Asked up front: at most Q4 (what makes a draft correct beyond real citations) and Q5 (examples available) if not inferable from the three failures. Asked lazily: none, unless the skill is about to recommend a verify step that needs tool access (then Q22(d) for that item only). Q15, Q17, Q18, Q20, Q23, Q24 not asked (not decision-relevant in `prompt` scope); Q19 defaulted and listed in § 2.

**Checks.** ≤ 3 questions up front; each carries a reason; Q12 and Q13 rows show `derived:artifact`; § 2 lists the defaults; the filled table was echoed for correction before diagnosis.

**Input B.** Design mode, scope `system`, one-paragraph request: "We want an agent that answers employee HR questions from our policy pages and opens a ticket when it can't. OpenAI Agents SDK." No profile, empty working directory.

**Expected.** Derived: Q1, Q2, Q3, Q6 (policy pages), Q16 partly (ticket system implied), Q25 (`system`). Asked up front (5–8): Q4, Q5, Q7 (size/change rate/citation), Q8 (where the pages live), Q9 (format/refusals), Q10 (how HR does it today), Q11 n/a, Q16 (which systems, irreversible?). Asked lazily: Q18/Q19 at the good-enough step; Q22(c)(d)(g) when retrieval, the ticket tool, and human handoff are proposed; Q15 only if the chain depth threatens a latency ceiling the user mentioned; Q20/Q23 only if fine-tuning reaches its gates (it will not: Q5 < 50).

**Checks.** 5–8 up front, ≤ 4 deferred; no question outside the scope matrix; no Q22 item confirmed that the design does not use; the final document's doc § 1 shows the split between derived, asked, deferred, and defaulted.

## S12 — Overdesigned prompt, no failures, under the long-context threshold (audit-driven review)

**Input.** Optimize mode, scope `prompt`, Claude API target. Request: "Can you review this prompt? It works but feels like too much." One 6.2k-token system prompt: it classifies the request into one of four types, then has a branch per type with its own drafting rules, embeds a 2.5k-token style guide, has 34 imperative rules including "never guess", "do not invent", "do not be verbose", the JSON output schema sits in the middle, three worked examples, and a paragraph that starts "Note to devs:". No failures reported; an eval of 40 items exists and passes at 93 %.

**Expected.** No Block E questions asked (R4a.3, Q11 derived as "review"). Audit row: verdict `overdesigned`: P1 = 5 (classify + four drafting jobs), P9 = 4 branches longer than the shared part, P3 ratio ≈ 1.2 but reference 2.5k (flag on size), P2 = 34, P5 = 3 negations with no positive, P7 contract mid-prompt, P8 absent, P11 present, P10 = 3.7k. Diagnosis rows A1–A8 from the audit; no D rows. Design: classify step with structured output → one of four specialist prompts (each `lean`), style guide disclosed into a skill or reference file each specialist loads (Claude target: a skill with the guide as reference), negations rewritten positive, contract at start and end, abstain output added, dev note removed. Because the eval passes, § 4a states the justification as cost, latency, and change-risk, not accuracy (R4a.1), and the eval spec reuses the 40 items as a do-no-harm gate with a two-context-size run. The split is an L0 change: in `prompt` scope it goes to doc § 15 with the recommendation to widen to `agent`, while the in-scope deliverable is the pruned, repositioned single prompt (verdict `dense` at worst, with P1/P9 noted as the residual). Lazy questions: Q22(a) only if the user widens scope.

**Checks.** Zero up-front questions beyond a scope confirmation; § 4a input row `overdesigned` with the measured values; emitted single prompt audits `lean` or `dense` with only P1/P9 residual and doc § 15 names the split; justification text cites cost/maintainability; eval reused as do-no-harm.
