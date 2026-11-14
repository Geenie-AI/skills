# SDK loaders

A custom agent built on the Claude Agent SDK or the OpenAI Agents SDK has no
skills directory. These samples load any skill from `../../skills/<name>` into
the agent in the same shape a host would:

1. `SKILL.md` becomes (part of) the system prompt or instructions.
2. One small tool, `read_skill_file`, returns any file the skill references by
   relative path (`reference/...`, `templates/...`), so the skill's progressive
   disclosure keeps working. The tool refuses paths that escape the skill folder.

| File | SDK | Language |
|---|---|---|
| `claude_agent_sdk_loader.py` | Claude Agent SDK (`pip install claude-agent-sdk`) | Python |
| `claude_agent_sdk_loader.ts` | Claude Agent SDK (`npm install @anthropic-ai/claude-agent-sdk zod`) | TypeScript |
| `openai_agents_loader.py` | OpenAI Agents SDK (`pip install openai-agents`) | Python |
| `openai_agents_loader.ts` | OpenAI Agents SDK (`npm install @openai/agents zod`) | TypeScript |

Each sample takes the skill name and the user's request on the command line,
points the skill at the current working directory as the project, and prints
the agent's final message:

```bash
python adapters/sdk/claude_agent_sdk_loader.py agentic-architect "Design an HR helpdesk agent"
npx tsx adapters/sdk/openai_agents_loader.ts agentic-architect "Design an HR helpdesk agent"
```

The skill writes its output where its `SKILL.md` says (relative to the
project), so the agent needs file-write access: the Claude samples allow the
built-in `Write` and `Edit` tools; the OpenAI samples add minimal
`read_project_file` and `write_file` tools because the Agents SDK has no
built-in file tools.

Set `SKILL_DIR` to point at a skill folder directly when the samples are
copied out of this repository.

Signatures were checked on 2026-11-14 against
https://code.claude.com/docs/en/agent-sdk/python and
https://code.claude.com/docs/en/agent-sdk/typescript. The OpenAI samples use the
`agents` / `@openai/agents` packages; `verify:` their import names against
https://openai.github.io/openai-agents-python/tools/ and
https://openai.github.io/openai-agents-js/guides/tools/ before relying on them.
