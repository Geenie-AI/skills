# 02 — Fixed intake question set

This is the fixed set of **facts** the skill needs. It is not a questionnaire the user always fills in. The skill answers as many as it can by itself and asks the user only what is still unknown and would change the design. Each question names the decision it feeds in `03-decision-framework.md`. Only Q1, Q2 and Q25 can block, and only when they cannot be derived.

## Asking policy: derive first, ask only what is uncertain and needed

A question is put to the user only when **all three** hold:

1. **In scope.** Its block is required for the run's scope (matrix in `07-layers-and-scope.md`).
2. **Underived.** No source below answered it with confidence. Low-confidence derivations are shown as a pre-filled guess for a yes/no confirmation, which is cheaper than an open question.
3. **Decision-relevant.** At least one design decision would differ depending on the answer. If every plausible answer leads to the same design, the default is recorded in § 2 Assumptions and the question is skipped.

Derivation sources, tried in order before asking:

| Source | Typically answers | Confidence rule |
|---|---|---|
| The user's request text | Q1 (mode), Q3 (task), Q25 (scope), often Q2, Q6, Q9, Q11 | High when stated explicitly; a guess otherwise |
| Pasted or referenced artifacts (Q1, Q26) | Q2 (SDK imports, file layout), Q9 (schemas), Q10 (steps), Q13 (context size, measured), Q16 (tool list), Q21 (what is fixed, if annotated), and every prompt-audit measure in `03` § 4a | High for anything measurable from the artifact |
| Profile (by ID, or the previous `architecture.md` in the working directory) | Any question it stores, subject to the staleness window and the "may not answer" table below | High if fresh; stale → confirmation |
| The working directory / repo | Q2 (`.claude/`, `openai` or `anthropic` imports, `AGENTS.md`), Q6/Q8 (docs folders, data stores named in config), Q17 (logging present) | Medium; shown as a guess |
| Default (last resort) | Everything else | Recorded in § 2 as an assumption, not asked |

Two timings for the questions that survive:

- **Up front**: questions whose answers shape the diagnosis itself (Blocks A, I, B, C, D, E as scoped). Asked in one batch, fewest possible.
- **At the decision point (lazy)**: questions that only bind when a specific lever is about to be chosen. The skill asks them at that moment, with the decision it affects stated in the same message, instead of up front. Lazy by default: Q15 (only if a chain or model choice could violate a ceiling), Q17 (only when a lever needs logs: eval growth, prompt baking), Q18/Q19 (when the break-even or handoff section is about to be filled and no profile figure exists), Q20 (only if fine-tuning or an external retrieval location is about to be proposed), Q22 (only the items whose lever the diagnosis actually calls for; the rest are recorded as not needed), Q23 (only when retrieval or fine-tuning is on the table), Q24 (only when two designs pass the gates).

Confirmation rule for permissions: the skill shows back only the Q21/Q22 items it is about to rely on, never the whole block. If the diagnosis calls for no lever that Q22 gates, nothing is shown.

Budget: a typical `prompt`-scope optimize run with a pasted prompt and three failures should need **zero to three** user questions up front; a `system`-scope design run from a one-paragraph request should need **five to eight**, with two or three more lazy ones. The skill states, with each batch, why each question could not be derived.

The architecture document records for every question whether it was derived (and from what), asked, deferred-then-asked, or defaulted.

## Principle: facts and permissions, never architecture choices

The user may not know whether they need retrieval, several prompts, several agents, tools, or a fine-tuned model, and may be anchored on the shape they already have (for example one agent chaining its own prompts). So the questions ask about **the task, the knowledge, the failures, the risk, and the operating envelope** in plain language, and the skill decides the shape from the diagnosis. Architecture words appear in one place only, Block H, and there they are **permissions**: which shapes the skill may introduce if the diagnosis calls for them. Each permission is explained in one plain sentence so the user can answer without knowing the technique.

Format rule for the skill: present the surviving questions as a numbered list with the derived guess or default in brackets, and a one-line reason the answer is needed. Accept free text. Echo back the full filled table (derived + asked + defaulted) before diagnosing, so the user can correct a derivation without having been asked about it.

## Block A — Mode and target (blocking)

| # | Question | Feeds | Default if unknown |
|---|---|---|---|
| Q1 | Are we **designing** a new solution or **optimizing** an existing one? If optimizing, paste every existing artifact verbatim (prompts, instructions, agent definitions, tool schemas, any configuration, and the order things run in). | Mode switch; in optimize mode the skill reads the current shape from the artifacts, not from the user's description | Blocking; ask again |
| Q2 | Which platform will run this: Claude Code, Claude Agent SDK, Claude API, OpenAI Agents SDK, OpenAI Responses API, or other (name it)? Which model(s) are allowed? | Emit step; model limits for context budget | Blocking; ask again |

## Block I — Scope and given layers (always asked; see `07-layers-and-scope.md`)

| # | Question | Feeds | Default |
|---|---|---|---|
| Q25 | Which **layers** may this run produce or change: a single prompt, a skill or set of skills, the assignment of skills to agents, one or more agents, the knowledge/tool layer, or the complete system? Name the pieces (e.g. "the prompt of the drafting step", "the three review agents"). | Scope; which intake blocks are asked; which sections of the architecture document are filled | `system` in design mode; smallest scope containing the pasted artifacts in optimize mode |
| Q26 | For every layer that is **not** in scope but that the work must fit: paste it or point at it (agent list and definitions, existing prompts, available skills, tool list, step order). | Given layers (rule SC4); required in `skill-assignment` scope: both the agents and the skills | Nothing given → the skill treats the layer as absent and says so in § 2 |

## Block B — Task and accuracy definition

| # | Question | Feeds | Default |
|---|---|---|---|
| Q3 | In one or two sentences, what does the system take in and what must it produce? | Task statement; detects known zero-shot-strong tasks (summarize, translate, code) | — |
| Q4 | Describe a **correct** output and an **incorrect** one for the same input. What makes the difference? | Defines "accurate"; chooses the eval metric type: exact / schema / judge rubric | Rubric-graded by an LLM judge |
| Q5 | How many **examples of ideal output** (input → ideal output) exist today, and how many could you produce within a week? | Eval-set gate (20+), fine-tune gate (50+), few-shot availability | 0 today; assume 20 obtainable |

## Block C — Knowledge the task depends on (facts, not mechanism)

| # | Question | Feeds | Default |
|---|---|---|---|
| Q6 | Does the task depend on information the model would not know by itself: private data, recent events, internal policies, product catalogues, code? List each source. | Context-axis trigger | None |
| Q7 | For each source: roughly how large is it (pages / rows / files), how often does it change, and must the answer point back to where it came from? | Static inclusion (small, stable) vs runtime retrieval (large or changing); citation requirement | Small, stable, no citation |
| Q8 | Where does each source live today and how do people get at it (files, wiki, database, API, internal search)? For a sample question, could you say which document or record holds the answer? | Tool vs retrieval choice; whether the retrieval axis can be measured (03 § 3, R5.1) | Files; cannot trace sample questions |

## Block D — Consistency the task demands

| # | Question | Feeds | Default |
|---|---|---|---|
| Q9 | What must be the **same every time**: output format or schema, tone, language, length, the way the reasoning is laid out, what the system must refuse? | Behavior-axis trigger; structured-output and few-shot design | JSON schema if a downstream system consumes it; otherwise free text |
| Q10 | Walk through how a skilled person does this task today, start to finish. What do they look up, decide, draft, and check? | The skill infers the step graph and where knowledge enters (R4.3, R9.2); the user is describing work, not proposing steps | One pass, no lookups |

## Block E — Observed failures (optimize mode only; design mode answers "none yet")

| # | Question | Feeds | Default |
|---|---|---|---|
| Q11 | Give at least three concrete failures: the input, what the system produced, what it should have produced. If you have none and want a review, say so. | Diagnosis table rows; with no failures, the prompt audit (03 § 4a) supplies the rows (R4a.3) | Blocking in optimize mode unless the request is a review or audit, or a trace export can supply failures |
| Q12 | For each failure: was the information needed for the right answer **already in front of the model** at the time? (yes / no / unsure) | Axis classification: present-but-misused → behavior; absent → context | unsure → skill inspects the artifact |
| Q13 | For each failure: at which point in the existing process did it first go wrong, and roughly how much text was in play at that point? | Lost-in-the-middle and error-compounding diagnosis | Unknown → skill estimates from artifacts |
| Q14 | What have you already tried (prompt edits, examples, different model, anything else) and what happened? | Avoids repeating failed levers; evidence of a saturated axis | Nothing |

## Block F — Operating envelope

| # | Question | Feeds | Default |
|---|---|---|---|
| Q15 | Expected volume (requests/day), latency ceiling per request, cost ceiling per request? | Chain depth, model choice, fine-tune-for-efficiency, tool-call count | Low volume; 30 s; no cost ceiling |
| Q16 | Which systems may the solution read from or act on (search, database, code execution, email, files, ticketing)? Which of those actions cannot be undone? | Tool design; confirmation gates; human handoff on irreversible actions | Read-only access only |
| Q17 | Are inputs and outputs logged today, or could they be in a pilot? | Prompt baking data source; eval set growth; monitoring | No |

## Block G — Risk and good-enough

| # | Question | Feeds | Default |
|---|---|---|---|
| Q18 | What is one **correct** outcome worth, and what does each kind of **wrong** outcome cost (e.g. an unnecessary escalation, a wrong answer accepted, an action taken wrongly)? Rough figures are fine. | Break-even accuracy worksheet (`good-enough.md`) | Symmetric: success +1, failure −1 → break-even 50 %, flagged as a placeholder |
| Q19 | What happens on a wrong answer today: who catches it, how fast, and can it be undone? | Handoff policy; graceful-failure pattern | A human reviews everything |
| Q20 | Are there hard constraints on data leaving your environment, on training models with your data, or on which vendors may see which data? | Fine-tune gate; retrieval location; model choice | No constraints |

## Block H — Degrees of freedom (permissions, in plain language)

This is the only block that names techniques. The skill proposes a technique only when a diagnosis row calls for it **and** the permission here allows it. A `no` is recorded in the architecture document as a rejected option with the accuracy cost it implies; an `ask first` becomes a conditional milestone that waits for the user's confirmation.

| # | Question | Feeds | Default |
|---|---|---|---|
| Q21 | What is **fixed** and may not change: a single agent, a single call, the current prompt wording, the output format, the model, the vendor, anything else? | Constraint set the design must respect; forgone levers go to doc § 14 | Nothing fixed |
| Q22 | For each item below, answer **yes / no / ask first**. If the analysis shows it is needed, may the skill: (a) split the work into several smaller prompts or steps that pass results to each other; (b) use more than one agent, each with its own job; (c) look up documents at run time and hand only the relevant parts to the model, instead of pasting everything in; (d) call tools, APIs, or databases to fetch facts or take actions; (e) add a checking step that verifies the draft against its sources before answering; (f) let the system ask the user a clarifying question when unsure; (g) route a case to a human when unsure or when the action is risky; (h) train a model on your examples; (i) switch to a different model; (j) change the output format? | Lever gates: (a)(b) → R4.3–R4.5, R9.2; (c) → 03 § 5; (d) → R9.1; (e) → R4.6; (f)(g) → 03 § 8 patterns; (h) → G6.5; (i) → model choice; (j) → R9.4 | All `ask first` |
| Q23 | Who will maintain the solution, and how much ongoing upkeep can they absorb (refreshing an index when documents change, curating training examples, monitoring evals)? | Retrieval vs static inclusion; fine-tune feasibility; the guide's iteration-speed trade-off | One part-time maintainer; low upkeep |
| Q24 | Do you have a preference between the **simplest** solution that meets the break-even accuracy and the **most accurate** solution within the cost ceiling? | Tie-break when two designs pass the gates | Simplest that meets break-even |

## Intake profiles (auto-answering by ID)

A caller may hand the skill a **profile ID** instead of answering every question by hand. A profile is a stored record of answers to Q1–Q24, keyed by ID, with a provenance tag and a timestamp on each answer. The skill loads it, fills the table, and asks only what is missing or stale.

### Invocation

- `/agentic-architect --profile <id>` or the user naming the ID in the prompt ("use profile acme-helpdesk").
- With no profile, the skill still checks the working directory for a previous `architecture.md` and offers to reuse its doc § 1 Intake as a profile (see `01-skill-plan.md`, open decisions).

### Where profiles come from (resolution order)

| Source | Form | Lookup |
|---|---|---|
| Repo profile store | `profiles/<id>.yaml` beside the skill or in the project | File read |
| Previous run | `architecture.md doc § 1 Intake` of a run whose `profile_id` matches | File read |
| External system | A tool or MCP server that returns the record for an ID (customer, site, tenant, product) with a field-to-question mapping declared in `profiles/mappings/<source>.yaml` | Tool call; the mapping says which field answers which Q |

Resolution stops at the first source that returns the ID. A profile may itself name a `parent` profile; child answers override parent answers.

### Profile record

```yaml
profile_id: acme-helpdesk
parent: acme-defaults          # optional
updated: 2026-11-14
answers:
  Q2: { value: "OpenAI Agents SDK; gpt-5", source: user, at: 2026-11-10 }
  Q6: { value: "HR policy pages (~400)", source: external:crm.kb_summary, at: 2026-11-14 }
  Q18: { value: "+15 / -200 wrong accepted / -10 ticket", source: user, at: 2026-09-01 }
  Q22: { value: "a:yes b:yes c:yes d:yes e:yes f:yes g:yes h:ask i:no j:yes", source: user, at: 2026-09-01 }
```

`source` is one of `user`, `profile:<id>` (inherited), `artifact` (derived from pasted material), `external:<system.field>`, or `default`.

### What a profile may and may not answer

| Block | Profile may fill | Rule |
|---|---|---|
| I Scope | Q26 yes (paths or tool references to the given layers); Q25 scope **no** | Scope is per run, like mode |
| A Mode and target | Q2 yes; Q1 mode **no** | Mode is per run. Artifacts for optimize mode may be fetched by the profile (a path or a tool) but the user confirms the mode |
| B Task | yes | — |
| C Knowledge | yes | External sources are preferred here: size and change frequency drift, and a system of record knows them |
| D Consistency | yes | — |
| E Observed failures | **no** | Failures are per run; Q11–Q14 are always asked fresh in optimize mode. A profile may point at a log or trace export the skill reads to *propose* failure rows, which the user confirms |
| F Envelope | yes | — |
| G Risk | yes | Q18 figures older than the staleness window are re-confirmed |
| H Permissions | yes, **shown back for confirmation** | Permissions gate levers; the skill prints Q21–Q22 and asks for a one-word confirm before diagnosing |

Staleness window: default 90 days, configurable in the profile. An answer older than the window is shown with its date and asked again; the user may say "keep".

### Procedure the skill follows with a profile

1. Resolve the ID through the sources above; stop with a clear message if none returns it.
2. Fill the intake table; tag every row with `source` and `at`. Then apply the asking policy: derive Q1 and Q25 from the request where possible.
3. Ask, in one batch, only what survives the policy: Q1/Q25 if underived, every in-scope decision-relevant question with no answer, every stale answer that is decision-relevant, and in optimize mode Q11–Q14 if not derivable from a trace export the profile points at.
4. Show back only the Q21–Q22 items the diagnosis will rely on, if any, and wait for confirmation.
5. Continue to diagnosis. The filled table, with provenance, goes to `architecture.md doc § 1`.
6. At the end of the run, offer to write back any answers the user gave or changed to the profile store (never to an external system).

## How the answers are stored

The skill writes the filled table to `architecture.md § Intake` (see `05-output-spec.md`), with a provenance column, so that every later section can cite `Q<n>` and a reviewer can see whether the evidence came from the user, a profile, an artifact, an external system, or a default. Unknowns and their defaults are listed in `architecture.md § Assumptions`, which is the first thing the user should correct on review. Q21–Q22 answers populate `architecture.md doc § 14 Rejected options` whenever a lever is skipped because of them.

## Why a fixed set

- **Reproducibility.** The guide's method is a loop of evaluate → hypothesise → change → re-evaluate. A fixed set of *facts* makes the "evaluate" input identical across runs so differences in output reflect differences in the scenario, not in what was gathered. Which facts are *asked* versus derived varies per run; which facts are *known* does not.
- **Coverage of both axes.** Blocks C and D force the user to describe missing knowledge and required consistency separately, which is the central move of the guide. They describe the world; the skill maps it onto the axes.
- **The user is asked as little as possible.** Each question costs the user attention and invites anchoring. Deriving from artifacts and the repo is also more accurate than asking (context size is measured, not estimated).
- **The user is never asked to design.** Blocks A–G collect facts; Block H collects permissions. A user anchored on "one agent, one chained prompt" can still get a multi-step, retrieval-backed design, because the skill reads the need from Q6–Q13 and the permission from Q22.
- **Good-enough is asked up front.** Block G exists so the skill cannot finish without a break-even target; the guide treats this as the condition for production readiness.
