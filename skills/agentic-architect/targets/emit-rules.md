# Emit rules (all targets)

The diagnosis and architecture are framework-neutral. Only the emit step reads this file and the matching `targets/<framework>-target.md`. Each abstract artifact maps to one native form per target; where a target lacks a native form, the generic form applies and the gap is noted in doc § 12.

## Abstract artifacts

| Artifact | Layer | Purpose | Serves |
|---|---|---|---|
| System prompt | L3 | Instructions, output contract, abstain rule, position of critical content | lever 1, R4.1, R4.7 |
| Instruction document | L2 | A procedure the agent loads on demand: steps plus disclosed reference | R4.3 (keeps the prompt small) |
| Agent definition | L1 | One responsibility, own context, named tools, model | R9.2, R4.5 |
| Orchestration | L0 | Routing between agents or steps, typed handoff payloads | R4.4, R4.5, R9.4 |
| Tool definition | L4 | Schema and description; marks irreversible actions | R9.1, R9.3, R9.6 |
| Retrieval component | L4 | Corpus, chunking, search, k, filters; per-step injection | `rag.md`, R5.2 |
| Context budget plan | L0/L1 | Per-step budget and manifest; caching strategy | R4.3 |
| Structured output schema | L1/L3 | Enforced output shape at boundaries | R9.4, Q9 |
| Eval spec | L5 | Items, metric, grid, context sizes, loop | `decision-framework.md` § 3 |
| Fine-tune spec | L5 | Dataset format, size, hold-out, baking source | `fine-tuning.md` |
| Handoff policy | L0 | Clarify / return / human, thresholds, confirmation gates | `good-enough.md`, R9.3 |
| Tracing | L5 | What is recorded for eval growth | R9.5, Q17 |

## Rules

- **E1 Serves header.** Every emitted artifact starts with a comment or header naming the diagnosis rows it serves (`serves: D3, D7, A1`).
- **E2 Position.** R4.1 is applied to every prompt: task and output contract first, reference in the middle, restated contract and abstain rule last.
- **E3 Manifest header.** Every chain step's artifact includes its manifest (sees / shielded from) and budget as a header comment.
- **E4 One file each.** The architecture document is emitted on every run; artifacts are emitted alongside it, one file each, named `NN-<step>-<artifact>.<ext>` (conventions in `../templates/architecture.md`).
- **E5 Diff summary.** In optimize mode, each rewritten artifact carries a short diff summary: what moved, what was removed, what was split out, and which failure each change targets.
- **E6 Verify markers.** Features that need verification at emit time (model context limits, availability of fine-tuning or structured outputs for a given model) are marked `verify:` with the doc URL rather than asserted.
- **E7 Scope-bound emission.** Only artifacts in the run's scope are emitted; for `skill-assignment` the emitted artifacts are the updated agent definitions (skill lists or loader tools) and the rewritten skill descriptions, never the skill bodies.
- **E8 Skill assignment per target.** Claude Code: the subagent definition names the skills it preloads and the skills live where that agent loads them. OpenAI: the agent holds the loader function tool or the search store containing the instruction document, and its instructions say when to load it. Generic: a declared list per agent.

## Procedure

1. Read `targets/<framework>-target.md` for the target in Q2. Codex counts as OpenAI; an unlisted framework uses `generic-target.md`.
2. For each artifact listed in doc § 12, produce the native form with the E1 header and, for prompts, the E2 positioning and E3 manifest.
3. Audit every emitted prompt, skill, and agent definition (R4a.4). Fix and re-audit until the verdict is `lean` or `lean (residual out of scope)`; add the emitted row to doc § 4a.
4. Code artifacts (SDK targets only): detect the project's language from the repository (lockfiles, imports); if none is found and an SDK agent definition is about to be emitted, ask once which language, stating that only this artifact depends on it. Python and TypeScript have templates; other languages get the generic declarative form plus a note.
5. If the host can delegate to a sub-agent with its own context, the emit step for each target may run in one; otherwise run it inline. Correctness never depends on delegation.
