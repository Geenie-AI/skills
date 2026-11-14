# Target: generic (any other framework)

Use for any platform not covered by `claude-target.md` or `openai-target.md`, and as the fallback form whenever a target lacks a native artifact. Everything here is declarative; emit a LangGraph-style or other framework sketch only when the user names that framework in Q2.

| Artifact | Native form |
|---|---|
| System prompt | Plain text file per step with E2 positioning and the E3 manifest header |
| Instruction document | Markdown procedure file; the loader (how and when the agent reads it) described in prose at the top |
| Agent definition | YAML block: name, responsibility, model, inputs schema, outputs schema, tools, budget, abstain output, documents it may load |
| Orchestration | A step graph in Markdown (nodes = agents or steps, edges = typed payloads) plus a short pseudo-code runner |
| Tool definition | JSON schema + description; `irreversible: true` and the confirmation gate named |
| Retrieval component | Prose spec from `../reference/rag.md`: corpus, chunking, index, query strategy, k, filters, citation ids, measurement |
| Structured output | JSON schema per boundary; the validation step named in the runner |
| Eval spec | JSONL set + judge prompt + metric definition (`../templates/eval-set.md`) |
| Fine-tune spec | Vendor-neutral JSONL chat format (`messages` with system, user, assistant) + the gates that passed |
| Handoff policy | Decision table (`../reference/good-enough.md`) |
| Tracing | Fields to log per step: step name, input hash, retrieved ids, output, abstain flag, latency, model |

## Common frameworks

When Q2 names one of these, keep the generic artifacts and use the framework's own parameter names in the agent definition and the runner sketch, so the user can paste them in. Names checked 2026-11-14 against each framework's docs; mark anything else `verify:`.

| Framework | System prompt / instructions | Structured output at a boundary | Instruction documents | Doc |
|---|---|---|---|---|
| LangChain / LangGraph (Python) | `create_agent(model, tools, system_prompt=…)` | `response_format=ToolStrategy(Model)` or `ProviderStrategy(schema)`; read `result["structured_response"]` | A tool that returns the document text | https://docs.langchain.com/oss/python/langchain/agents |
| CrewAI | `Agent(role=, goal=, backstory=)`; `system_template` for the full prompt | `Task(output_pydantic=Model)` → `.pydantic`; `agent.kickoff(response_format=Model)` | Knowledge sources or a tool | https://docs.crewai.com/en/concepts/agents |
| AutoGen / AG2 | `AssistantAgent(system_message=…)` | `LLMConfig(response_format=Model)` | A tool | https://docs.ag2.ai/latest/docs/user-guide/basic-concepts/structured-outputs |
| Microsoft Agent Framework | `client.as_agent(name=, instructions=…)` | `agent.run(q, options={"response_format": Model})` → `response.value`; .NET `RunAsync<T>()` | A tool | https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs |
| Semantic Kernel | `ChatCompletionAgent(instructions=…)` | `OpenAIChatPromptExecutionSettings(response_format=Model)` via `KernelArguments(settings=…)`; .NET `ResponseFormat = typeof(T)` | A plugin function | https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-types/chat-completion-agent |
| Pydantic AI | `Agent(model, instructions=…)` (preferred over `system_prompt`, which persists in history) | `output_type=Model` | A tool | https://pydantic.dev/docs/ai/core-concepts/agent/ |
| Mastra | `new Agent({ instructions })` | `agent.generate(msg, { structuredOutput: { schema } })` | A tool | https://mastra.ai/en/reference/agents/agent |
| LlamaIndex | `FunctionAgent(tools=, llm=, system_prompt=…)` | `output_cls=Model` → `response.structured_response` | A tool or an index | https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/ |
| Google ADK | `LlmAgent(instruction=…)` | `output_schema=Model`, `output_key` stores it in state | Native: `load_skill_from_dir` + `SkillToolset` in `tools` (Agent Skills format) | https://adk.dev/agents/llm-agents/ |
| Vercel AI SDK | `new ToolLoopAgent({ model, instructions, tools })` | `output: Output.object({ schema })` → `result.output` | Cookbook pattern: scan `.agents/skills`, inject descriptions, `loadSkill` tool | https://ai-sdk.dev/docs/agents/building-agents |

Orchestration stays the declarative step graph below; a LangGraph `StateGraph` or CrewAI `Crew`/`Flow` sketch is added only when the user asks for runnable code (`emit-rules.md` § Procedure, step 4).

## Templates

### Agent definition (`NN-<step>-agent.yaml`)

```yaml
# serves: D1, D3
name: draft
responsibility: write the reply from the retrieved clauses
model: <from Q2>            # verify: context limit
budget_tokens: 8000
sees: [ClassifiedRequest, RetrievedClauses]
shielded_from: [corpus, upstream transcripts]
inputs_schema: schemas/classified-request.json
outputs_schema: schemas/draft.json
abstain_output: {status: no_supporting_clause}
tools: []
documents: [reference/style-guide.md]   # loaded on demand
```

### Step graph (`00-step-graph.md`)

```markdown
extract --ExtractedFields--> classify --ClassifiedRequest--> enrich --RetrievedClauses--> draft --Draft--> verify_format --FinalReply--> out
Loops: verify_format --unsupported claims > 0--> enrich (once, widened query) --> human
```

```text
runner(input):
  f = call(extract, input)            # validate schemas/extracted.json
  c = call(classify, f)
  r = retrieve(c.area, c.query, k=5)   # tool, returns clause ids
  d = call(draft, c, r)
  v = call(verify_format, d, fetch(d.claims[*].clause_id))
  if v.unsupported: retry once with widened query, else handoff(human)
  return v.reply
```
