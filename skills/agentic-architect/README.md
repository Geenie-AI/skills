<p align="center">
  <a href="https://github.com/Geenie-AI/skills"><img src="https://raw.githubusercontent.com/Geenie-AI/.github/main/profile/assets/geenie-ai-logo.png" alt="Geenie-AI logo" width="96"></a>
</p>

<h1 align="center">agentic-architect</h1>

<p align="center">A <a href="https://github.com/Geenie-AI/skills">Geenie-AI skill</a>: design or optimize agentic solutions for any framework, by the Optimizing LLM Accuracy method.</p>

<p align="center">
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml"><img src="https://github.com/Geenie-AI/skills/actions/workflows/eval.yml/badge.svg" alt="eval"></a>
  <a href="https://github.com/Geenie-AI/skills/releases/latest"><img src="https://img.shields.io/github/v/release/Geenie-AI/skills?display_name=tag&sort=semver" alt="latest release"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f" alt="Agent Skills compatible"></a>
</p>

A portable agent skill that designs new agentic solutions, or diagnoses and improves existing ones, for any framework. It follows the method in OpenAI's [Optimizing LLM Accuracy](https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy) guide, so every recommendation it makes is traceable to a diagnosed need, comes with an evaluation plan, and stops at the cheapest lever that meets your accuracy target.

Part of the [Geenie-AI skills](../../README.md) collection; it follows the repository's [skill pattern](../../docs/skill-pattern.md) and is installed with the shared tooling described there.

## What it does

Point it at anything from a single prompt to a whole multi-agent system and it will:

- **Diagnose** each requirement or observed failure onto the two optimization axes from the guide: missing *context* (knowledge the model lacks) or inconsistent *behavior* (format, tone, method the model does not hold). Every prompt it reads is also audited for overdesign and underdesign with measured values.
- **Design** using the cheapest lever that fits, in order: prompt engineering, few-shot examples, retrieval, fine-tuning, then combinations. It never proposes retrieval or fine-tuning without a baseline evaluation, and never calls a design done without a break-even accuracy and a graceful-failure path.
- **Emit** the artifacts in your target framework's native form: Claude Code skills and subagents, Claude Agent SDK, Claude API, OpenAI Agents SDK, OpenAI Responses API, Codex, or a framework-agnostic form.

Typical requests:

- "This 9k-token prompt chains five tasks over a 90k-token corpus and hallucinates citations at the end. Fix it."
- "Design an HR helpdesk agent that answers from policy pages and opens a ticket when unsure."
- "Here are my four agents and nine skills. Who should load what?"
- "Can you review this prompt? It works but feels like too much."

## Install

The skill is a plain folder in the open [Agent Skills](https://agentskills.io) format, so it runs unchanged in any host that loads skills. Pick one:

```bash
# Claude Code, as a plugin from this repository's marketplace
claude plugin marketplace add Geenie-AI/skills
claude plugin install agentic-architect@geenie-ai-skills      # then /agentic-architect:agentic-architect

# Any host, from a clone of this repository
scripts/install.sh --skill agentic-architect --host <claude|codex|copilot|gemini|cursor|kiro|agents|generic> [--project|--user]

# Community skills CLI (verify: resolves skills/<name> in this repository)
npx skills add Geenie-AI/skills --skill agentic-architect
```

Per-host paths, invocation forms and SDK loaders are in [`adapters/`](../../adapters/README.md). The copy made for Claude Code gains `disable-model-invocation: true`, so only you trigger it.

## How it works

1. **Intake.** The skill needs a fixed set of facts about your task, the knowledge it depends on, the consistency it demands, observed failures, risk, and operating limits. It derives as many as it can from your request, pasted artifacts, a saved profile, and the repository, and asks you only what is still unknown and would change the design. Questions that bind to a specific lever are asked at the moment that lever is proposed. You are never asked to choose an architecture; you are asked for permission to use one.
2. **Diagnose.** Every row gets an axis, a lever, the layer the lever lives in, and the evidence. Every prompt gets an audit row with measured values and a verdict.
3. **Design.** Levers are applied in order with explicit gates. The output includes a per-step context budget, an eval spec, a break-even accuracy worksheet, a handoff policy, and a list of rejected options with the rule that rejected each.
4. **Emit.** Artifacts are written for the target framework, each one naming the diagnosis rows it serves, and each emitted prompt is audited before it is written.

## Scopes

A run can be confined to one layer of your solution. Diagnosis always covers every layer; changes stay inside the scope, and anything found outside it is reported with the accuracy you forgo by leaving it.

| Scope | Touches |
|---|---|
| `prompt` | One or more system prompts and their evals |
| `skill` | The instruction documents an agent loads |
| `skill-assignment` | Which agent loads which skill, with a context-load ledger and a gap/overlap matrix |
| `agent` | One or more agents, including their prompts, skills, and the tools and retrieval bound to them |
| `knowledge` | Retrieval components and tool definitions |
| `system` | Everything, including orchestration, handoff policy, and rollout |

## What you get

An `architecture.md` with a constant shape across modes and scopes, written to `./agentic-architecture/`, plus one file per artifact: prompts, skill folders, agent definitions, tool schemas, retrieval spec, structured-output schemas, eval set and judge rubric, fine-tune spec when warranted, and a handoff policy. In optimize mode, each rewritten artifact carries a short diff summary tied to the failures it addresses.

## Usage

```
/agentic-architect Design an HR helpdesk agent that answers from ~400 policy pages and opens a ticket when unsure. Target: OpenAI Agents SDK.
/agentic-architect Review this prompt; it works but feels like too much. [paste]   # optimize mode, prompt scope
/agentic-architect Here are my four agents and nine skills. Who should load what?   # skill-assignment scope
/agentic-architect --profile acme-helpdesk Design the helpdesk agent.               # pre-fill the intake from a saved profile
```

The request can name the mode (design or optimize), the scope (one prompt, a skill, an assignment, an agent, the knowledge layer, the whole system), and the target. Anything not stated is derived from the request, the pasted artifacts and the working directory, and you are asked only what is still unknown and would change the design.

Profiles are YAML records of intake answers keyed by ID, stored in the skill's `profiles/`, in the project's `.agentic-architect/profiles/`, or resolved through an MCP server you configure with a field mapping. Each answer carries its source and date; stale answers are re-confirmed, and per-run questions such as observed failures are always asked fresh. See [`profiles/README.md`](profiles/README.md).

### Naming the target framework

Say which platform will run the solution; the diagnosis and architecture are the same for every target, and only the emitted artifacts change.

| Say | Emitted as | Native forms used |
|---|---|---|
| "Claude Code" | Claude target | Skill folders, `.claude/agents/*.md` subagents, `CLAUDE.md` pointers, `PreToolUse` hooks for confirmation gates |
| "Claude Agent SDK" or "Claude API" | Claude target | System prompts with cache breakpoints, tool schemas, `AgentDefinition` subagents, JSON-schema `output_config`, judge prompts |
| "OpenAI Agents SDK", "Responses API" or "Codex" | OpenAI target | Agents with `output_type`, handoffs or agents-as-tools, function tools, `file_search` vector store spec, Structured Outputs schemas, Codex skills, fine-tuning JSONL when gated in |
| "LangGraph" / "LangChain", "CrewAI", "AutoGen" / "AG2", "Microsoft Agent Framework", "Semantic Kernel", "Pydantic AI", "Mastra", "LlamaIndex", "Google ADK", "Vercel AI SDK" | Generic target, with the framework's parameter names from the mapping table in `targets/generic-target.md` | Declarative step graph, one prompt file per step, JSON schema per boundary, tool schemas, retrieval spec, eval set, handoff decision table |
| Anything else, or no framework yet | Generic target | Same, framework-neutral |

## How it decides

- **Axes.** Was the needed information in front of the model? Absent, or present but beyond the effective window: *context*. Present and still wrong: *behavior*.
- **Lever order.** Prompt engineering (including splitting, repositioning, pruning, and an abstain output), then few-shot examples, retrieval, fine-tuning, and combinations. Each later lever has a gate, and the gate that fails is recorded.
- **Permissions, not architecture questions.** The skill infers whether you need several steps, several agents, retrieval, tools, verification, or human handoff, and asks only whether it may use them.
- **Good enough.** A break-even accuracy from your value and cost figures, a realistic accuracy estimate, and a handoff policy with measurable triggers.

The rules live in [`reference/`](reference/), each citing the section of the guide it comes from, with additions for agentic systems marked "Beyond the guide".

## Layout

```
skills/agentic-architect/        the host-neutral skill (the only thing a host needs)
  SKILL.md                       the four steps
  reference/                     intake questions, decision framework, long context, retrieval, fine-tuning, good-enough, layers and scope
  targets/                       emit rules and the per-framework artifact forms
  templates/                     architecture document and eval set skeletons
  profiles/                      profile format and external-source mappings
tests/agentic-architect/         config, judge prompt, preamble and acceptance scenarios S01–S12
planning/agentic-architect/      design documents the skill is built from
```

## Contributing

- Read [`planning/agentic-architect/00-README.md`](../../planning/agentic-architect/00-README.md) first; it indexes the design and defines the rule IDs (`R`, `P`, `G`, `SC`, `AS`, `E`, `H`, `Q`) that the skill, the scenarios and the validator share.
- Run `python3 scripts/validate.py --skill agentic-architect` before opening a pull request.
- Changes to rules or scopes need a scenario in [`tests/agentic-architect/scenarios/`](../../tests/agentic-architect/) with expected checks, and an entry under `Unreleased` in the repository [`CHANGELOG.md`](../../CHANGELOG.md).
- Releases are repository-wide tags `vX.Y.Z`; see [`docs/releasing.md`](../../docs/releasing.md).

## Scenario eval results

Every scenario is run through the skill on each host that has an API key configured, then graded against its `expected-checks.md` by a judge prompt. The weekly and manually dispatched runs of the eval workflow refresh this table; pull-request runs post the same table as a comment instead.

<!-- eval-results:start -->
**1/1 passed** on claude.

| Scenario | Host | Result | Up-front q | Deferred q | Judge checks |
|---|---|---|---|---|---|
| S08m-prompt-scope-mini | claude | pass | 3/3 | 2/2 | 8/8 |

Last run: 2026-11-14 · trigger: workflow_dispatch · [workflow run](https://github.com/Geenie-AI/skills/actions/runs/43634860512).

Non-blocking. Full output is in the workflow artifacts.
<!-- eval-results:end -->
