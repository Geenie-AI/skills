---
name: agentic-architect
description: Designs a new agentic solution or diagnoses and improves an existing one (a prompt, a skill set, a skill-to-agent assignment, an agent, the knowledge layer, or a whole system) for Claude Code, Claude Agent SDK, Claude API, OpenAI Agents SDK, OpenAI Responses API, Codex, or a generic framework, following OpenAI's Optimizing LLM Accuracy method. Use when asked to design, architect, review, optimize, or fix prompts, skills, agents, retrieval, or multi-agent pipelines, or when a pipeline hallucinates, ignores its schema, or needs an eval plan.
---

# agentic-architect

Four steps: intake, diagnose, design, emit. Every recommendation traces to a diagnosed need, every design ships with an eval spec and a graceful-failure path, and the cheapest lever that meets the accuracy target wins. Out of scope, declined in one sentence: running training jobs, provisioning vector stores, executing evals, picking a vendor on price, ranking two user-supplied designs against each other.

Leading words: **axis** (context / behavior), **lever** (prompt, examples, retrieval, fine-tune), **baseline** (the prompt-only eval result), **break-even** (the accuracy at which the system pays for itself), **handoff** (the graceful-failure path), **budget** (tokens per step), **scope** (the layers this run may change).

Output goes to the `agentic-architecture` folder of the project (location and file conventions in `templates/architecture.md`). Use capability verbs: read the file, search the working directory, measure the token count, present the questions in one message and wait for the reply.

**Non-interactive runs.** When the request says the user's answers are in a file: each time you would ask a question, append one line to the named log (`<upfront|deferred> <Qid> | <reason it could not be derived> | <decision it affects>`), take the answer from the file, and treat every confirmation as given by the file. A blocking question with no answer stops the run with its Q-ID; any other falls back to its default tagged `default (unanswered)`.

## 1. Intake

Read `reference/intake-questions.md` and `reference/layers-and-scope.md`.

1. Establish mode (Q1) and scope (Q25) from the request; both are usually derivable. When a profile ID is given, or the output root already holds an `architecture.md`, resolve it per `profiles/README.md` and pre-fill. Ask for every out-of-scope layer the work must fit (Q26).
2. Fill the fact set by deriving first: request text, pasted or referenced artifacts, profile, working directory, then defaults. Measure sizes from artifacts; never ask for a number you can measure. Apply the measurement rule for anything too large to read.
3. Keep a question only if it is in scope for Q25, underived, and decision-relevant; low-confidence derivations become yes/no confirmations. Defer the lazy questions (Q15, Q17–Q20, Q22 items, Q23, Q24) to step 3.
4. Ask the surviving up-front questions in one numbered batch, each with its Q-ID, the guess or default in brackets, and the reason it could not be derived. In optimize mode collect every artifact verbatim and at least three failures (Q11), unless the request is a review, in which case the audit supplies the rows (R4a.3).
5. Echo the full filled table with provenance tags and wait for corrections before diagnosing.

Done when: every question has an answer or a default; every row carries a provenance tag and, if asked, the reason; every `unknown` has a stated default in § 2; the scope is named and every out-of-scope layer the work depends on is supplied or marked absent; no question outside the scope's eligible blocks was asked.

## 2. Diagnose

Read `reference/decision-framework.md`. Read `reference/long-context.md` when any step's context exceeds the threshold, the chain has more than one step, or an audit flags P12.

1. Audit every prompt, skill, and agent definition received, together with every always-on instruction file the host loads, against P1–P15. Record measured values and a verdict per prompt in doc § 4a.
2. Build the diagnosis table across all layers (SC1): one row per requirement (design mode) or per observed failure (optimize mode), plus one `A<n>` row per audit flag. Each row gets the axis with its evidence (information present, absent, or present but beyond the effective window), a candidate lever, the layer the lever lives in, and in-scope yes/no.
3. Infer the step graph from Q10 and the artifacts, never from the user's current agent count (R9.2). Fill the context budget for every step of the proposed or existing chain (R4.3); in `skill-assignment` scope, fill the per-agent ledger instead (AS4).
4. Place retrieval-related rows on the failure grid in `reference/rag.md` when a context row names a large or changing source.

Done when: every prompt read has an audit row with a verdict; every diagnosis row has an axis, a lever, a layer, in-scope status, and measured evidence; rows whose layer is out of scope are marked for doc § 15; the budget table has a row for every step, or the ledger a row for every agent.

## 3. Design

Read `reference/good-enough.md` when the scope fills doc § 10. Read `reference/rag.md` before proposing retrieval and `reference/fine-tuning.md` before proposing fine-tuning or combining levers.

1. Apply the levers in order: prompt engineering (always, including the structural fixes from the audit, R4a.2), few-shot examples, retrieval, fine-tuning, combine. Record every skipped lever with the gate that failed in doc § 14. Place the baseline (prompt + eval of ≥ 20 items) before any retrieval or fine-tuning milestone.
2. At the moment a lever needs a deferred fact or a Q22 permission, ask that one question in the same message as the decision it affects, and show back only the Q21/Q22 items the design relies on. A `no` keeps the design inside the constraint and records the forgone accuracy in doc § 14; an `ask first` marks the lever conditional.
3. Give every chain step a single responsibility, a budget and manifest, a typed output schema (R9.4), an abstain output (R4.7), and a fresh context where the target allows (R4.5). Add a verification step whenever the output makes factual claims from sources (R4.6). Gate every irreversible action on confirmation (R9.3). When Q15 binds, apply R9.8.
4. Write the eval spec from `decision-framework.md` § 3 and `templates/eval-set.md`, sized to the scope (SC7). Fill the break-even worksheet and the handoff policy where the scope requires § 10, flagging placeholders.
5. In optimize mode, fill doc § 11 so every change names the rows it targets and the eval items that will show it worked.
6. Write `architecture.md` from `templates/architecture.md`, run its review checklist, and put a banner at the top when a root cause sits outside the scope or behind a refused permission (SC3). Mark sections the scope does not need `n/a (scope)`.

Done when: every section the scope requires is filled; every lever chosen is justified by an in-scope diagnosis row; doc § 14 names the rule or answer that rejected each option; doc § 15 lists every out-of-scope row with the recommended widening and the forgone accuracy; the baseline precedes every retrieval or fine-tuning step; no lever contradicts Q21 or a Q22 `no` without a flagged conflict.

## 4. Emit

Read `targets/emit-rules.md` and the `targets/<framework>-target.md` that matches Q2.

1. Write each artifact listed in doc § 12 in the target's native form, one file each, with the serves header (E1), position rule (E2), and manifest header (E3). Only in-scope artifacts are emitted (E7); a `system` or `agent` run re-emits the prompts and skills of every agent it changed (SC6).
2. Audit every emitted prompt, skill, and agent definition; fix until the verdict is `lean` or `lean (residual out of scope)` (R4a.4), and add the emitted row to doc § 4a.
3. In optimize mode, attach the diff summary to each rewritten artifact (E5). Mark unverifiable vendor features `verify:` with the doc URL (E6).
4. Close by listing the files written, the first three things the user should correct (§ 2 assumptions, placeholders, conflicts), and, when a profile was used or created, the offer to write back changed answers.

Done when: every artifact in doc § 12 exists as a file; each names the rows it serves; every emitted prompt audits `lean` or `lean (residual out of scope)`; the architecture document and the artifacts agree on step names, schemas, and budgets.
