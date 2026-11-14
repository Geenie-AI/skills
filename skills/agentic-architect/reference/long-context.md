# Long context and chains

Read this when any step's context exceeds the threshold below, when the chain has more than one step, or when a prompt audit flags P12. Guide section: *Long context*. Chain rules R4.3–R4.8 are **Beyond the guide**.

From the guide: long-context models extend prompt engineering but suffer **lost in the middle**; needle-in-a-haystack tests show that dumping everything into context trades simplicity for accuracy. Pair long context with evaluation at multiple sizes.

## Thresholds

| Setting | Default | Source |
|---|---|---|
| Long-context threshold per step | 32k tokens | Override from Q2 when the model's documented effective window differs; cite the doc URL with `verify:` |
| Per-step budget | ≤ 8k tokens for instructions + inputs; retrieved items extra, bounded by k × chunk size | R4.3 |
| Always-loaded budget per agent (ledger, AS4) | 8k tokens | Raise only with a Q15 cost figure that allows it |
| Conversation history budget | Counted inside the step budget; summarise or retrieve past turns beyond it | R4.8 |
| Multi-size eval | Same set at ≥ 2 sizes, e.g. 8k and the full context | R4.2 |

## Rules

- **R4.1 Position.** Critical instructions, the task statement, and the output contract go at the start and are restated at the end. Reference material sits between.
- **R4.2 Multi-size eval.** Any step whose context exceeds the threshold gets the multi-size eval from `decision-framework.md` § 3, with accuracy recorded at each size.
- **R4.3 Budget per step.** Each step of a chain gets a token budget and a manifest: *what it sees* (instructions, the inputs it needs, retrieved items) and *what it is shielded from* (everything else). The default move for a step over budget is to retrieve into it rather than inherit the whole upstream context.
- **R4.4 Structured handoff between steps.** A step passes a typed, minimal intermediate result (a schema) to the next step, never its full transcript. This stops error compounding and keeps each step's context readable.
- **R4.5 Fresh context per step.** Where the framework supports it (subagents, handoffs or agents-as-tools, separate API calls), each step runs in its own context window. One monolithic prompt becomes a graph of small prompts.
- **R4.6 Verify at the end.** The final step receives the sources (or citations to them) and the draft, and checks each claim against a source; unsupported claims are removed or flagged. This is the guide's "add fact-checking to reduce hallucinations" made concrete.
- **R4.7 Permission to abstain.** Each step's instructions name the output for "not enough information", so the model has a correct answer other than invention.
- **R4.8 History is a context source.** In multi-turn systems the transcript counts against the step budget. Beyond the budget, summarise earlier turns into a typed state object or retrieve past turns on demand; run the multi-size eval over history length as well as reference size.

## Budget table procedure

For every step of the proposed or existing chain, fill one row of doc § 6:

1. Name the step and its single responsibility.
2. List what it sees: instructions (measured tokens), inputs from upstream (by schema name, with size), retrieved items (k × chunk size), history (turns or tokens).
3. List what it is shielded from: upstream transcripts, the corpus, other agents' instructions.
4. Set the budget and compare with the measured or estimated total; mark over-budget rows and the fix (retrieve into the step, typed handoff, split).
5. Mark whether the step runs in a fresh context on the target.

In `skill-assignment` scope the table becomes the per-agent context-load ledger (AS4): prompt + tool descriptions + descriptions of every model-invoked skill assigned, against the always-loaded budget.
