# agentic-architect — planning documents

These are the design documents the `skills/agentic-architect` skill was built from. The repository layout in `08 § 3` describes the skill's original stand-alone repository; it has since moved into the Geenie-AI skills repository, whose shared layout, tooling and conventions are documented in [`docs/skill-pattern.md`](../../docs/skill-pattern.md). Everything else in these documents still holds.

Planning set for building `agentic-architect`: a skill that designs a new agentic solution, or optimizes an existing one, for any target framework (Claude Code / Claude Agent SDK / Claude API, OpenAI Agents SDK / Responses API, or a generic framework such as LangGraph). Every design decision it makes follows the method in OpenAI's *Optimizing LLM Accuracy* guide (https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy).

| File | What it holds | Read it when |
|---|---|---|
| `01-skill-plan.md` | Goal, scope, skill file layout, build phases, acceptance criteria | Starting the build, or checking what "done" means |
| `02-intake-questions.md` | The fixed question set the skill asks, and which decision each answer feeds | Writing the intake step of the skill |
| `03-decision-framework.md` | The accuracy method encoded as rules: axes, lever order, diagnosis, long-context rules, RAG grid, fine-tune gates, good-enough maths, graceful failure | Writing the design/optimize steps of the skill |
| `04-framework-targets.md` | How each abstract artifact (prompt, skill, agent, retrieval, context, eval) is emitted for each target framework | Writing the emit step and the per-framework reference files |
| `05-output-spec.md` | The architecture document and artifact templates the skill produces | Writing templates; reviewing a produced design |
| `06-scenarios.md` | Worked scenarios (including the "massive chained prompt that hallucinates" and "brand-new situation" cases) used as the skill's acceptance tests | Validating the skill end to end |
| `08-portability-and-distribution.md` | Making the skill itself host-agnostic (Agent Skills format, capability verbs, overlays per host), repo layout, static validation and scenario eval workflows, semver tagging and releases, README plan, language-agnostic emission | Packaging, CI, releasing, or installing on a new host |
| `07-layers-and-scope.md` | The layer model (system, agents, skills, prompts, knowledge/tools, evals), named scopes, per-scope intake and output, and the skill-assignment rules | Writing the scope handling; running the skill on a single prompt, a skill set, or an assignment task |

## The one-paragraph version

The skill works at any layer: one prompt, one agent's skills, the assignment of skills to agents, an agent, the knowledge/tool layer, or the complete system. The skill runs four steps: **intake** (a fixed fact set, derived from the request, artifacts, profile and repo first; the user is asked only what is still unknown and would change the design, and lever-specific questions are deferred to the moment the lever is chosen), **diagnose** (classify every requirement or observed failure onto the two optimization axes: *context* vs *behavior*), **design** (pull the cheapest lever that fits, in the order prompt → examples → retrieval → fine-tune → combine, and always ship an eval set and a graceful-failure path), **emit** (write the artifacts in the target framework's native form). It refuses to recommend RAG or fine-tuning without a baseline eval, and it refuses to call a design done without a break-even accuracy target.

## Reference conventions

- `03 § n` means a section of `03-decision-framework.md`; `doc § n` means a section of the produced `architecture.md` (template in `05-output-spec.md`). Inside `03` itself, a bare `§ n` is a section of `03`.
- Rule IDs: `R` long-context/retrieval/agentic rules and `G` fine-tune gates (`03`), `P` prompt-audit measures (`03 § 4a`), `SC` scope rules and `AS` assignment rules (`07`), `E` emit rules (`04`), `H` host-portability rules (`08`). Diagnosis rows are `D<n>` (requirements/failures) and `A<n>` (audit findings); scenarios are `S<n>`.

## Source of truth

The OpenAI guide is the method. Where this plan paraphrases it, `03-decision-framework.md` cites the section. Where the plan goes beyond the guide (e.g. framework-specific emit rules, chain-of-steps context budgeting), it says so explicitly under a "Beyond the guide" marker so the two can be kept apart.
