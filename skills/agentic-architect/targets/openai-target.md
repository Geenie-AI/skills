# Target: OpenAI (Agents SDK, Responses API, Codex)

Pick the column that matches Q2. Codex is an OpenAI host for instruction documents; its agents and prompts follow the Responses column. Doc URLs are listed so each form can be re-verified (E6); the platform is retiring some features, so check the dated notes below before emitting.

| Artifact | Agents SDK (Python / TypeScript) | Responses API | Codex |
|---|---|---|---|
| System prompt | `instructions` on the agent object (string or callable); stable prefix first for prompt caching | `instructions` parameter (not carried over with `previous_response_id`); stable prefix first | `AGENTS.md` for always-on repo conventions (concatenated root → cwd, 32 KiB default cap) |
| Instruction document | A Markdown file loaded by a `read_document` function tool, or a `FileSearchTool` store holding it; the instructions say when to load it | Same, as a function tool or `file_search` | **Skill**: `.agents/skills/<name>/SKILL.md` with `name` and `description`; optional `scripts/`, `references/`, `assets/` |
| Agent definition | Python: an Agent object with `name, instructions, tools, handoffs, output_type, model, model_settings, input_guardrails, output_guardrails`; TypeScript: `new Agent({ name, instructions, tools, handoffs, outputType, model })` built from the same fields. `output_type` enforces the typed handoff (R4.4, R9.4) | One call per step with its own `instructions`; orchestration in the caller | n/a |
| Orchestration | **Handoffs** (control passes; `handoffs=[...]`, default tool `transfer_to_<agent>`) for routing to a specialist that owns the rest of the conversation; **agents-as-tools** (`agent.as_tool(tool_name, tool_description, max_turns)`) when the orchestrator needs the result back (chains); `Runner.run(agent, input, max_turns=10)` | `previous_response_id` or `conversation` for state; typed payloads between calls | n/a |
| Tool definition | `@function_tool` (typed signature, `strict_mode=True`, `needs_approval=True` or callable for R9.3); TS `tool({name, description, parameters, execute, needsApproval})`; hosted: `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool` | `tools[]`: `function` with JSON schema and `strict: true`; `file_search`, `web_search`, `code_interpreter`, `mcp` (`require_approval`) | MCP servers in `~/.codex/config.toml` |
| Retrieval component | `FileSearchTool(vector_store_ids, max_num_results (1–50), include_search_results, ranking_options, filters)` attached to the one agent that needs it (R5.2) | `file_search` tool with `vector_store_ids`, `max_num_results`, `filters` (comparison or compound on file attributes), `ranking_options {ranker, score_threshold, hybrid_search}` | `file_search` through the API, or a script in the skill |
| Vector store | `chunking_strategy: {type: "static", static: {max_chunk_size_tokens (100–4096, default 800), chunk_overlap_tokens (≤ half)}}`; file `attributes` (≤ 16 keys) for metadata filters; search endpoint `POST /v1/vector_stores/{id}/search` with `query`, `filters`, `max_num_results`, `ranking_options`, `rewrite_query` | same | same |
| Context budget plan | One agent per step; `max_turns`; `model_settings` reasoning effort per step; prompt caching from the stable prefix (min cacheable prefix depends on model) | `reasoning.effort` (`none … max`), `prompt_cache_key`, breakpoints via `prompt_cache_options` on newer models (`verify:` per model) | n/a |
| Structured output | `output_type=PydanticModel` / `outputType: zodSchema` | `text.format: {type: "json_schema", name, schema, strict: true}`; all properties `required`, `additionalProperties: false`, root an object | `--output-schema` on `codex exec` |
| Eval spec | JSONL set + judge prompt run through the SDK, or OpenAI Evals (`POST /v1/evals` with `data_source_config` and `testing_criteria`: `string_check`, `text_similarity`, `label_model`, `score_model`, `python`; runs from a JSONL `file_id`). **Dated note:** the Evals platform is announced as read-only from 2026-10-31 and shut down 2026-11-30; prefer the JSONL + judge form and mark Evals `verify:` | same | same |
| Fine-tune spec | Fine-tuning API: `POST /v1/fine_tuning/jobs` with `training_file`, `validation_file` (hold-out, G6.4), `method.type: supervised | dpo | reinforcement`; JSONL lines `{"messages": [{"role": "system", …}, {"role": "user", …}, {"role": "assistant", …}]}` including the production system prompt and retrieved context (G6.3). **Dated note:** the fine-tuning platform is winding down; new users cannot access it and existing customers can create jobs until 2027-01-06 (`verify:`). Record availability in doc § 12 as an emit gap; the lever plan is unchanged | same | n/a |
| Handoff policy | Guardrail tripwires (`@input_guardrail` / `@output_guardrail` returning `GuardrailFunctionOutput(tripwire_triggered=…)`); a `transfer_to_human` function tool; a handoff back to the triage agent (return-to-stage); `needs_approval` interruptions resumed with `Runner.run(agent, state)` | A branch in the caller; `require_approval` on MCP tools | n/a |
| Tracing | `with trace(workflow_name)`; spans per agent, generation, function, guardrail, handoff; processors via `add_trace_processor()` | Store responses (`store: true`) and log `usage` | `codex exec --json` event stream |

Doc URLs: Agents SDK Python https://openai.github.io/openai-agents-python/ (agents, handoffs, tools, guardrails, human_in_the_loop, tracing); TypeScript https://openai.github.io/openai-agents-js/ ; Responses API reference https://developers.openai.com/api/reference/resources/responses/methods/create ; structured outputs https://developers.openai.com/api/docs/guides/structured-outputs ; prompt caching https://developers.openai.com/api/docs/guides/prompt-caching ; retrieval https://developers.openai.com/api/docs/guides/retrieval ; vector stores https://developers.openai.com/api/reference/resources/vector_stores/methods/create ; model optimization and fine-tuning https://developers.openai.com/api/docs/guides/model-optimization ; evals https://developers.openai.com/api/docs/guides/evals ; Codex skills https://learn.chatgpt.com/docs/build-skills ; Codex non-interactive https://learn.chatgpt.com/docs/non-interactive-mode ; AGENTS.md https://learn.chatgpt.com/docs/agent-configuration/agents-md .

## Templates

### Agent (Python)

```python
# serves: D1, D3 | budget: 6k | sees: ClassifiedRequest, retrieved clauses (k=5) | shielded from: corpus, upstream transcript
from agents import Agent, FileSearchTool
from pydantic import BaseModel

class Draft(BaseModel):
    status: str                      # "ok" | "no_supporting_clause"
    claims: list[dict]               # each {text, clause_id}
    reply: str

draft_agent = Agent(
    name="draft",
    instructions=DRAFT_PROMPT,       # E2 positioning: contract first, retrieved clauses middle, contract + abstain last
    tools=[FileSearchTool(vector_store_ids=[POLICY_STORE], max_num_results=5,
                          filters={"type": "eq", "key": "policy_area", "value": "{{area}}"})],
    output_type=Draft,
    model=MODEL,                     # verify: context limit for MODEL
)
```

### Orchestrator with agents-as-tools and a human handoff

```python
from agents import Agent, Runner, function_tool

@function_tool(needs_approval=True)   # R9.3: paused run surfaces result.interruptions
def create_ticket(summary: str, employee_id: str) -> str:
    """Open an HR ticket. Reversible: the ticket can be closed. Call when the answer confidence is below threshold or status is no_supporting_clause."""
    ...

orchestrator = Agent(
    name="triage",
    instructions=TRIAGE_PROMPT,
    tools=[draft_agent.as_tool(tool_name="answer_policy_question", tool_description="…"), create_ticket],
    output_type=FinalReply,
)
result = await Runner.run(orchestrator, user_input, max_turns=6)
```

Emit each boundary schema as `schemas/<boundary>.json`, the vector store spec as `retrieval.md`, the eval as `eval/` (JSONL + judge prompt), and the fine-tune format as `finetune/format-example.jsonl` only when the gates pass.
