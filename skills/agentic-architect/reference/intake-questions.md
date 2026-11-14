# Intake: the fixed fact set

The skill needs a fixed set of **facts** about the task. It is not a questionnaire. Answer as many as you can yourself, from the sources below, and put to the user only what is still unknown and would change the design. Each question names the decision it feeds in `decision-framework.md`.

Blocking questions (the run stops if they stay unanswered): Q1, Q2, Q11 in optimize mode unless the request is a review or audit, Q26 in `skill-assignment` scope. Every other question has a default.

## Asking policy

Put a question to the user only when **all three** hold:

1. **In scope.** Its block is eligible for the run's scope (matrix in `layers-and-scope.md`).
2. **Underived.** No source below answered it with confidence. A low-confidence derivation is shown as a pre-filled guess for a yes/no confirmation, which is cheaper than an open question.
3. **Decision-relevant.** At least one design decision would differ depending on the answer. If every plausible answer leads to the same design, record the default under § 2 Assumptions and skip the question.

Derivation sources, tried in this order before asking:

| Source | Typically answers | Confidence |
|---|---|---|
| The request text | Q1, Q3, Q25; often Q2, Q6, Q9, Q11 | High when stated explicitly; otherwise a guess |
| Pasted or referenced artifacts | Q2 (SDK imports, file layout), Q9 (schemas), Q10 (steps), Q13 (context size, measured), Q16 (tool list), Q21 (if annotated), every audit measure P1–P15 | High for anything measurable |
| Profile (by ID, or a previous `architecture.md` in the output root) | Any question it stores, subject to staleness and the "may not answer" table | High if fresh; stale → confirm |
| The working directory | Q2 (`.claude/`, `.agents/`, `AGENTS.md`, `openai` or `anthropic` imports), Q6/Q8 (docs folders, data stores in config), Q17 (logging present) | Medium; shown as a guess |
| Default | Everything else | Recorded in § 2, not asked |

**Measurement rule.** Measure sizes by reading the artifact: count tokens with a tool when one exists, otherwise estimate as bytes ÷ 4 and tag the value `estimated:`. For a corpus or folder, sample up to 20 files, extrapolate from file count, and tag `estimated:`. Never load a corpus into your own context to measure it.

**Timing.** Questions that survive are asked at one of two moments:

- **Up front**, in one batch, fewest possible: questions whose answers shape the diagnosis (Blocks A, I, B, C, D, E as scoped, plus Q21).
- **At the decision point (lazy)**: questions that bind only when a lever is about to be chosen. Ask them then, in the same message as the decision they affect ("I want to add runtime retrieval over the policy pages to fix D1 and D4; may the system look documents up at run time?"). Lazy by default: Q15 (whenever the design proposes more than one sequential call, a verify step, or retrieval), Q17 (when a lever needs logs: eval growth, prompt baking), Q18/Q19 (when § 10 is about to be filled and no profile figure exists), Q20 (when fine-tuning or an external retrieval location is proposed), Q22 (only the items the diagnosis relies on; the rest are recorded as not needed), Q23 (when retrieval or fine-tuning is on the table), Q24 (when two designs pass the gates).

**Confirm-default rule.** When a derived tool list (Q16) contains any action that writes or sends, the irreversibility part of Q16 and the Q19 answer become confirm-default questions, never silent defaults.

**Unanswered rule.** If no answer arrives, or the run is non-interactive and the answer file lacks the question: a blocking question stops the run with the unanswered Q-IDs listed; any other takes its default, tagged `default (unanswered)`.

**Budget.** A `prompt`-scope optimize run with a pasted prompt and three failures needs zero to three questions up front. A `system`-scope design run from a one-paragraph request needs five to eight up front and two or three lazy ones. With each batch, state why each question could not be derived.

**Format.** Present surviving questions as a numbered list, each with its Q-ID, the derived guess or default in brackets, and a one-line reason the answer is needed. Accept free text. Echo back the full filled table (derived + asked + defaulted, with provenance) before diagnosing so the user can correct a derivation they were never asked about.

**Provenance tags** (one enum, used in doc § 1 and in profiles): `derived:request`, `derived:artifact`, `derived:repo`, `profile:<id>`, `external:<system.field>`, `asked`, `asked (deferred)`, `default`, `default (unanswered)`.

## Principle: facts and permissions, never architecture choices

The user may not know whether they need retrieval, several prompts, several agents, tools, or a fine-tuned model, and may be anchored on the shape they already have. So the questions ask about **the task, the knowledge, the failures, the risk, and the operating envelope** in plain language, and the skill decides the shape from the diagnosis. Architecture words appear in Block H only, as **permissions**: which shapes the skill may introduce if the diagnosis calls for them.

## Block A — Mode and target (blocking)

| # | Question | Feeds | Default |
|---|---|---|---|
| Q1 | Are we **designing** a new solution or **optimizing** an existing one? If optimizing, paste or point at every existing artifact verbatim: prompts, instructions, agent definitions, tool schemas, configuration, and the order things run in. | Mode switch; in optimize mode the current shape is read from the artifacts, not from the user's description | Blocking |
| Q2 | Which platform will run this: Claude Code, Claude Agent SDK, Claude API, OpenAI Agents SDK, OpenAI Responses API, OpenAI Codex, or another framework (name it: LangGraph, CrewAI, AutoGen, Microsoft Agent Framework, Semantic Kernel, Pydantic AI, Mastra, LlamaIndex, Google ADK, Vercel AI SDK, …)? Which model(s) are allowed? | Emit step (the named framework's parameter names from `../targets/generic-target.md`); model context limits for the budget | Blocking |

## Block I — Scope and given layers

| # | Question | Feeds | Default |
|---|---|---|---|
| Q25 | Which **layers** may this run produce or change: a single prompt, a skill or set of skills, the assignment of skills to agents, one or more agents, the knowledge/tool layer, or the complete system? Name the pieces. | Scope; which blocks are eligible; which document sections are filled | `system` in design mode; smallest scope containing the pasted artifacts in optimize mode; two scopes named at once → union |
| Q26 | For every layer that is **not** in scope but that the work must fit: paste it or point at it (agent list and definitions, existing prompts, available skills, tool list, step order, always-on instruction files). | Given layers (SC4); blocking in `skill-assignment` scope, which needs both the agents and the skills | Nothing given → the layer is treated as absent and § 2 says so |

## Block B — Task and accuracy definition

| # | Question | Feeds | Default |
|---|---|---|---|
| Q3 | In one or two sentences, what does the system take in and what must it produce? | Task statement; detects zero-shot-strong tasks (summarize, translate, code) | — |
| Q4 | Describe a **correct** output and an **incorrect** one for the same input. What makes the difference? | Defines "accurate"; chooses the metric: exact / schema / judge rubric | Rubric-graded by an LLM judge |
| Q5 | How many **examples of ideal output** (input → ideal output) exist today, and how many could you produce within a week? | Eval-set gate (20+), fine-tune gate (50+), few-shot availability | 0 today; 20 obtainable |

## Block C — Knowledge the task depends on

| # | Question | Feeds | Default |
|---|---|---|---|
| Q6 | Does the task depend on information the model would not know by itself: private data, recent events, internal policies, product catalogues, code? List each source. | Context-axis trigger | None |
| Q7 | For each source: roughly how large is it (pages / rows / files), how often does it change, and must the answer point back to where it came from? If the task is multi-turn, how long do conversations run? | Static inclusion (small, stable) vs runtime retrieval (large or changing); citation requirement; history budget (R4.8) | Small, stable, no citation, single turn |
| Q8 | Where does each source live today and how do people get at it (files, wiki, database, API, internal search)? For a sample question, could you say which document or record holds the answer? | Tool vs retrieval choice (R9.1); whether the retrieval axis can be measured (R5.1) | Files; cannot trace sample questions |

## Block D — Consistency the task demands

| # | Question | Feeds | Default |
|---|---|---|---|
| Q9 | What must be the **same every time**: output format or schema, tone, language, length, the way reasoning is laid out, what the system must refuse? | Behavior-axis trigger; structured-output and few-shot design; output language for examples, rubric, and eval set | JSON schema if a downstream system consumes it; otherwise free text |
| Q10 | Walk through how a skilled person does this task today, start to finish. What do they look up, decide, draft, and check? | The step graph and where knowledge enters (R4.3, R9.2); the user describes work, never proposes steps | One pass, no lookups |

## Block E — Observed failures (optimize mode; design mode answers "none yet")

| # | Question | Feeds | Default |
|---|---|---|---|
| Q11 | Give at least three concrete failures: the input, what the system produced, what it should have produced. If you have none and want a review, say so. | Diagnosis rows; with no failures the prompt audit supplies the rows (R4a.3) | Blocking in optimize mode unless the request is a review or audit, or a trace export supplies failures |
| Q12 | For each failure: was the information needed for the right answer **already in front of the model** at the time? (yes / no / unsure) | Axis classification: present-but-misused → behavior; absent → context; present but beyond the effective window → context | unsure → inspect the artifact and answer it yourself |
| Q13 | For each failure: at which point in the process did it first go wrong, and roughly how much text was in play (including conversation history)? | Lost-in-the-middle and error-compounding diagnosis | Unknown → estimate from the artifacts |
| Q14 | What have you already tried (prompt edits, examples, a different model, anything else) and what happened? | Avoids repeating failed levers; evidence of a saturated axis | Nothing |

## Block F — Operating envelope

| # | Question | Feeds | Default |
|---|---|---|---|
| Q15 | Expected volume (requests/day), latency ceiling per request, cost ceiling per request? | Chain depth, model choice, fine-tune-for-efficiency, tool-call count, latency rule R9.8 | Low volume; 30 s; no cost ceiling |
| Q16 | Which systems may the solution read from or act on (search, database, code execution, email, files, ticketing)? Which of those actions cannot be undone? | Tool design; confirmation gates (R9.3); human handoff on irreversible actions | Read-only access only |
| Q17 | Are inputs and outputs logged today, or could they be in a pilot? | Prompt-baking data source; eval-set growth; monitoring | No |

## Block G — Risk and good-enough

| # | Question | Feeds | Default |
|---|---|---|---|
| Q18 | What is one **correct** outcome worth, and what does each kind of **wrong** outcome cost (an unnecessary escalation, a wrong answer accepted, an action taken wrongly)? Rough figures are fine. | Break-even worksheet (`good-enough.md`) | Symmetric +1 / −1 → break-even 50 %, flagged as a placeholder |
| Q19 | What happens on a wrong answer today: who catches it, how fast, and can it be undone? | Handoff policy; graceful-failure pattern | A human reviews everything |
| Q20 | Are there hard constraints on data leaving your environment, on training models with your data, or on which vendors may see which data? | Fine-tune gate G6.5; retrieval location; model choice | No constraints |

## Block H — Degrees of freedom (permissions, in plain language)

The only block that names techniques. Propose a technique only when a diagnosis row calls for it **and** the permission allows it. A `no` becomes a rejected option in doc § 14 with its accuracy cost; an `ask first` becomes a conditional milestone.

| # | Question | Feeds | Default |
|---|---|---|---|
| Q21 | What is **fixed** and may not change: a single agent, a single call, the current prompt wording, the output format, the model, the vendor, anything else? | Constraint set; forgone levers go to doc § 14 | Nothing fixed |
| Q22 | For each item, answer **yes / no / ask first**. If the analysis shows it is needed, may the skill: (a) split the work into several smaller prompts or steps that pass results to each other; (b) use more than one agent, each with its own job; (c) look up documents at run time and hand only the relevant parts to the model; (d) call tools, APIs, or databases to fetch facts or take actions; (e) add a checking step that verifies the draft against its sources; (f) let the system ask the user a clarifying question when unsure; (g) route a case to a human when unsure or when the action is risky; (h) train a model on your examples; (i) switch to a different model; (j) change the output format? | Lever gates: (a)(b) → R4.3–R4.5, R9.2; (c) → `rag.md`; (d) → R9.1; (e) → R4.6; (f)(g) → `good-enough.md` patterns; (h) → G6.5; (i) → model choice; (j) → R9.4 | All `ask first` |
| Q23 | Who will maintain the solution, and how much upkeep can they absorb (refreshing an index, curating training examples, monitoring evals)? | Retrieval vs static inclusion; fine-tune feasibility; iteration-speed trade-off | One part-time maintainer; low upkeep |
| Q24 | Do you prefer the **simplest** solution that meets the break-even accuracy, or the **most accurate** solution within the cost ceiling? | Tie-break when two designs pass the gates | Simplest that meets break-even |

Show back only the Q21/Q22 items the design is about to rely on, at the moment the lever is chosen in step 3, never the whole block. If no lever Q22 gates is needed, show nothing.

## Profiles

A caller may hand the skill a **profile ID** instead of answering by hand: `--profile <id>` or "use profile <id>" in the request. Record format, resolution order, and staleness rules are in `../profiles/README.md`. Procedure:

1. Resolve the ID (repo store → previous run → external source via a declared mapping). If no source returns it, say so, continue with the normal intake, and offer to create the profile at the end. An unreachable external source counts as "no profile", not an error.
2. Fill the table; tag every row `profile:<id>` with its date. Then apply the asking policy: derive Q1 and Q25 from the request where possible.
3. Ask, in one batch, only what survives the policy: Q1/Q25 if underived, every in-scope decision-relevant question with no answer, every stale decision-relevant answer (shown with its date; "keep" is a valid reply), and in optimize mode Q11–Q14 unless a trace export the profile points at supplies failure rows, which the user then confirms one by one.
4. Continue to diagnosis. Permissions are shown back lazily in step 3, same as without a profile.
5. At the end of the run, offer to write back answers the user gave or changed to the repo profile store, never to an external system.

What a profile may fill: Q2–Q10, Q15–Q24, Q26. Never Q1, Q25, or Q11–Q14 (mode, scope, and failures are per run).
