# Target: Claude (Claude Code, Claude Agent SDK, Claude API)

Three sub-targets share a model family but not a file layout. Pick the column that matches Q2. Doc URLs are given so each form can be re-verified (E6); feature names drift.

| Artifact | Claude Code | Claude Agent SDK | Claude API (Messages) |
|---|---|---|---|
| System prompt | `CLAUDE.md` for always-on project conventions and pointers only; task instructions go in a skill. `@path` imports for shared files (max four hops). | `system_prompt` option; stable prefix first for caching | `system` parameter as content blocks; mark the stable prefix with `cache_control: {"type": "ephemeral"}` (max 4 breakpoints) |
| Instruction document | **Skill**: `<dir>/SKILL.md` with `name` and `description` frontmatter, reference files beside it; `disable-model-invocation: true` for user-only skills; description carries trigger branches when model-invoked | Same skill folder under `.claude/skills/`, loaded with `setting_sources` including `project` | No native loader: emit the document as a file plus a `read_document` tool, or as a cached `system` block when small |
| Agent definition | **Subagent**: `.claude/agents/<name>.md`, frontmatter `name`, `description`, `tools`, `disallowedTools`, `model`, `skills` (preloads up to 32), `maxTurns`; body = its system prompt. One subagent per responsibility, fresh context (R4.5), returns free text, so the caller validates it against the boundary schema (R9.4) | `agents` option: `AgentDefinition(description, prompt, tools, model, skills, maxTurns)`; include the delegation tool, named Agent, in allowed tools | Separate call per step with its own `system`; orchestration lives in the caller's code |
| Orchestration | Main session delegates to subagents; hooks for deterministic gates | Programmatic loop around `query()`; hooks via `ClaudeAgentOptions(hooks=...)` | Caller's code; typed payloads between calls |
| Tool definition | Built-in tools, MCP servers (`mcp__<server>__<tool>`), or tools declared on a subagent | `tools` and `mcpServers` options | `tools` with JSON schema; `strict: true` validates inputs; describe when to call, when not to, and irreversibility |
| Retrieval component | A tool or MCP server the step calls, returning chunk ids; or a sub-agent that searches a folder and returns ids | Same, as a custom tool or MCP server | A tool the model calls; the caller runs the search; Files API documents for small stable corpora |
| Context budget plan | Subagents for isolation; `omitClaudeMd` where a subagent must not inherit project files; effort per subagent | Same; `autoCompactWindow` per agent where available | `cache_control` breakpoints on the stable prefix; `thinking: {"type": "adaptive"}` with `output_config.effort` per step |
| Structured output | A subagent's return is text: emit the schema and a validation step in the caller | Same | `output_config: {"format": {"type": "json_schema", "schema": …}}` (objects need `additionalProperties: false`); or a tool call as the output channel |
| Eval spec | `evals/<case>/prompt.md` + `graders/*.md` for `claude plugin eval` when the artifact is a skill or plugin; otherwise JSONL set + judge prompt | JSONL set + judge prompt run through the SDK | JSONL set + judge prompt as a Messages call |
| Fine-tune spec | Not offered on the Claude API (glossary: "does not currently offer fine-tuning"). Record in doc § 12 as an emit gap; the lever plan is unchanged | same | same |
| Handoff policy | `PreToolUse` hook returning `permissionDecision: "ask"` or `"deny"` for irreversible tools (R9.3); human handoff = stop and report with the session id | Hook callback returning the same decision object | A branch in the caller; a `transfer_to_human` tool that ends the loop |
| Tracing | Session transcripts; `PostToolUse` hooks writing JSONL | Message stream to a log | Request/response logging in the caller |

Doc URLs: skills https://code.claude.com/docs/en/skills ; subagents https://code.claude.com/docs/en/sub-agents ; hooks https://code.claude.com/docs/en/hooks ; memory and imports https://code.claude.com/docs/en/memory ; plugin evals https://code.claude.com/docs/en/plugin-evals ; Agent SDK subagents https://code.claude.com/docs/en/agent-sdk/subagents ; structured outputs https://platform.claude.com/docs/en/build-with-claude/structured-outputs ; prompt caching https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; thinking https://platform.claude.com/docs/en/build-with-claude/extended-thinking ; Files API https://platform.claude.com/docs/en/build-with-claude/files .

## Templates

### Skill (`<name>/SKILL.md`)

```markdown
---
name: <kebab-name>
description: <what it does>. Use when <trigger branch 1>, <trigger branch 2>.
---
<!-- serves: D2, A3 -->
# <Title>

1. <Step with a checkable completion criterion.>
2. When <branch>, read `reference/<file>.md`.
```

Steps only in the body; reference disclosed behind pointers that name the branch reaching them. Add `disable-model-invocation: true` only for user-only skills.

### Subagent (`.claude/agents/<name>.md`)

```markdown
---
name: <name>
description: <one responsibility; when the main session should delegate to it>
tools: Read, Grep, mcp__search__find_clause
model: inherit
skills: [<model-invoked skill names>]
---
<!-- serves: D1, D3 | budget: 6k | sees: ClassifiedRequest, retrieved clauses (k=5) | shielded from: corpus, upstream transcript -->
<Task statement and output contract.>

<Procedure.>

<Reference, if small and stable.>

Return exactly: <schema or field list>. If the sources do not support an answer, return `{"status": "no_supporting_clause"}`.
```

### Hook for an irreversible tool (`.claude/settings.json`)

```json
{"hooks": {"PreToolUse": [{"matcher": "mcp__tickets__create_ticket", "hooks": [{"type": "command", "command": "scripts/confirm-gate.sh"}]}]}}
```

The command prints `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "<why>"}}`. Exit code 2 blocks outright.

### Messages API call per step (Python sketch)

```python
resp = client.messages.create(
    model=MODEL,  # verify: context limit for MODEL
    system=[{"type": "text", "text": STABLE_PREFIX, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": RETRIEVED_CLAUSES}],
    messages=[{"role": "user", "content": INPUT_PAYLOAD}],
    output_config={"format": {"type": "json_schema", "schema": DRAFT_SCHEMA}},
    max_tokens=2000,
)
```

Emit the step's schema as `schemas/<boundary>.json` and the judge as `eval/judge-prompt.md`.
