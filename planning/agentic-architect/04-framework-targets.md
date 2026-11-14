# 04 — Framework targets (emit rules)

The diagnosis and architecture are framework-neutral. Only the **emit** step reads this file. Each abstract artifact in the architecture document maps to one native form per target. Where a target lacks a native form, the generic form is used and the gap is noted in the architecture document.

Verification note for the build: every API/feature name below must be checked against the vendor's current documentation at build time (P3) and the `targets/*.md` files should carry the doc URL next to each feature. Names drift.

## Abstract artifacts

| Artifact | Layer | Purpose | Serves rule |
|---|---|---|---|
| **System prompt** | L3 | Instructions, output contract, abstain rule, position of critical content | § 2 lever 1, R4.1, R4.7 |
| **Instruction document** (skill / reusable procedure) | L2 | A procedure the agent loads on demand; steps + disclosed reference | R4.3 budget (keeps prompt small), writing-for-agents |
| **Agent definition** | L1 | One responsibility, own context, named tools, model | R9.2, R4.5 |
| **Orchestration** | L0 | Routing between agents/steps, typed handoff payloads | R4.4, R4.5, R9.4 |
| **Tool definition** | L4 | Schema + description; marks irreversible actions | R9.1, R9.3 |
| **Retrieval component** | L4 | Corpus, chunking, search, k, filters; per-step injection | § 5, R5.2 |
| **Context budget plan** | L0/L1 | Per-step token budget and manifest; caching strategy | R4.3 |
| **Structured output schema** | L1/L3 | Enforced output shape at boundaries | R9.4, Q9 |
| **Eval spec** | L5 | Items, metric, grid, context sizes, loop | § 3 |
| **Fine-tune spec** | L5 | Dataset format, size, hold-out, baking source | § 6 |
| **Handoff policy** | L0 | Clarify / return / human, thresholds, confirmation gates | § 8, R9.3 |
| **Tracing/logging** | L5 | What is recorded for eval growth | R9.5, Q17 |

## Target: Claude (Claude Code, Claude Agent SDK, Messages API)

| Artifact | Native form | Emit notes |
|---|---|---|
| System prompt | `system` parameter (Messages API / Agent SDK); `CLAUDE.md` for always-on project instructions in Claude Code | Keep `CLAUDE.md` to conventions and pointers; task instructions go in a skill. Mark stable prefix for prompt caching |
| Instruction document | Claude Code **skill**: `SKILL.md` with `name`, `description` frontmatter; `disable-model-invocation: true` for user-only; reference files beside it | Follow `writing-for-agents`: steps in `SKILL.md`, reference disclosed. Description carries trigger branches if model-invoked |
| Agent definition | Claude Code **subagent**: `.claude/agents/<name>.md` with `name`, `description`, `tools`, `model` frontmatter and the body as its system prompt; Agent SDK: `agents` option / custom subagents | One subagent per responsibility; subagent runs in a fresh context (R4.5) and returns a summary, which is the typed handoff (R4.4) |
| Orchestration | Main session delegating via the Agent tool; Agent SDK programmatic loop; hooks for deterministic gates | Put the per-step manifest in each subagent's prompt. Use hooks (PreToolUse) for R9.3 confirmation gates |
| Tool definition | Messages API `tools` with JSON schema; MCP servers for external systems; Claude Code built-in tools | Describe when to call and when not to; name irreversibility in the description |
| Retrieval component | Tool call to the user's search/vector store, or an MCP server; or the Files/search features where available | Retrieval is a tool the step calls (R5.2); the tool returns chunk ids for citation |
| Context budget plan | Prompt caching breakpoints on the stable prefix; subagents for isolation; extended thinking budget per step | Record cache boundaries in the architecture doc |
| Structured output | JSON-schema tool call used as the output channel, or the structured-output feature where available | One schema per boundary |
| Eval spec | Harness-agnostic: a JSONL set + a judge prompt as a Claude call; or `claude plugin eval` suites when the artifact is a Claude Code skill/plugin | Judge rubric emitted as a prompt file |
| Fine-tune spec | Not a native Claude feature | Emit as "not available on this target"; keep lever 4 as prompt/examples/retrieval and say so |
| Handoff policy | Hooks + subagent return codes in Claude Code; explicit branch in Agent SDK loop | Human handoff = stop and report, with the trace id |
| Tracing | Session transcripts; Agent SDK message stream; hooks writing JSONL | Point the eval growth step at the log path |

## Target: OpenAI (Agents SDK, Responses API, platform features)

| Artifact | Native form | Emit notes |
|---|---|---|
| System prompt | `instructions` on an Agent (Agents SDK) or on a Responses API call; developer message | Prompt caching favours a stable prefix; put variable content last |
| Instruction document | `AGENTS.md` for Codex-style repo instructions; otherwise a Markdown procedure the agent loads as a tool result or a `file_search` document | OpenAI has no skill primitive; the generic form applies with a loader tool |
| Agent definition | Agents SDK `Agent(name, instructions, tools, handoffs, output_type, model)` | `output_type` enforces the typed handoff (R4.4, R9.4) |
| Orchestration | **Handoffs** (control passes) and **agents-as-tools** (orchestrator keeps control) in the Agents SDK; `Runner` loop | Prefer agents-as-tools when the orchestrator needs the result back (chains); handoffs when routing to a specialist that owns the rest of the conversation |
| Tool definition | `@function_tool` with typed signature; hosted tools (`web_search`, `file_search`, `code_interpreter`, computer use); MCP servers | Guardrails (input/output) for policy; `needs_approval` style patterns for R9.3 |
| Retrieval component | `file_search` over a **vector store** (chunking, `max_num_results`, metadata filters, ranking options); or a custom function tool | Expose retrieval as a tool on the step that needs it (R5.2). Emit chunk size/overlap and filter design |
| Context budget plan | Separate agents per step; `max_turns`; prompt caching via stable prefix; reasoning effort per step on reasoning models | Record budget per agent |
| Structured output | Structured Outputs (`response_format` / `text.format` JSON schema with `strict: true`); Agents SDK `output_type` | One schema per boundary |
| Eval spec | OpenAI **Evals** (datasets + graders: string check, model grader, custom) | Emit the grader config and the JSONL set |
| Fine-tune spec | Fine-tuning API: supervised (SFT), direct preference optimization (DPO), reinforcement fine-tuning (RFT) where available for the model | JSONL chat format including the production system prompt and any retrieved context (G6.3). Hold-out file (G6.4) |
| Handoff policy | Guardrail tripwires; a `transfer_to_human` tool; a handoff back to the triage agent (return-to-stage pattern) | Thresholds live in the architecture doc, not scattered in code |
| Tracing | Agents SDK tracing (traces/spans) | Point eval growth at the trace export |

## Target: generic (any other framework)

| Artifact | Native form |
|---|---|
| System prompt | Plain text file per step, with position rules applied |
| Instruction document | Markdown procedure file; loader described in prose |
| Agent definition | YAML/Markdown block: name, responsibility, inputs schema, outputs schema, tools, model, budget |
| Orchestration | A step graph in Markdown (nodes = agents, edges = typed payloads) with a short pseudo-code runner; optional LangGraph-style sketch if the user names it |
| Tool definition | JSON schema + description |
| Retrieval component | Prose spec: corpus, chunking, index, query strategy, k, filters, citation ids |
| Structured output | JSON schema per boundary; validation step named |
| Eval spec | JSONL set + judge prompt + metric definition |
| Fine-tune spec | Vendor-neutral JSONL chat format + gates |
| Handoff policy | Decision table |
| Tracing | Fields to log per step |

## Emit rules common to all targets

- **E1** Every emitted artifact starts with a comment or header naming the diagnosis rows it serves (`serves: D3, D7`).
- **E2** Position rule R4.1 is applied to every prompt: task and output contract first, reference in the middle, restated contract and abstain rule last.
- **E3** Every chain step's artifact includes its manifest (sees / shielded from) and budget as a header comment.
- **E4** The architecture document is emitted on every run; artifacts are emitted alongside it, one file each, named `<step>-<artifact>.<ext>`.
- **E5** In optimize mode, each rewritten artifact is accompanied by a short diff summary: what moved, what was removed, what was split out, and which failure each change targets.
- **E7** Only artifacts in the run's scope are emitted; for `skill-assignment` the emitted artifacts are the updated agent definitions (their skill lists or loader tools) and the rewritten skill descriptions, never the skill bodies.
- **E8** Skill assignment per target: Claude Code: the subagent prompt names the skills it may use and the skills live where that agent loads them; OpenAI: the agent holds the loader function tool or the `file_search` store containing the instruction document, and its instructions say when to load it; generic: a declared list per agent.
- **E6** Features that need verification at emit time (model context limits, availability of fine-tuning or structured outputs for a given model) are marked `verify:` with the doc URL rather than asserted.
