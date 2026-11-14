Our HR reply pipeline hallucinates. It runs on Claude Code (the main session calls Claude with one system prompt and the employee message; model is Claude Sonnet, we can use Opus if needed). The prompt is about 9k tokens and does five things in a row: extract the facts, classify the request, find the policy clauses, draft the reply, then format it as JSON. The whole policy manual (around 90k tokens) is pasted into the prompt, and the five tasks all run in one call. We also tried running it as five calls where each call gets the full transcript so far; same results.

The problem: the drafted reply cites policy clauses that do not exist, and the JSON formatting step sometimes ignores the schema and just writes prose. We added "do not hallucinate" and a stronger instruction at the top and it changed nothing.

The production prompt with the manual pasted in is at `artifacts/pipeline-system-prompt.full.md` (the prompt alone, with a placeholder where the manual goes, is `fixtures/artifacts/pipeline-system-prompt.md`; the manual alone is `artifacts/policy-corpus.md`). Three failure examples with what we wanted instead, and what we have tried, are in `artifacts/failures.md`.

Please fix the whole thing; nothing about the current shape is sacred.
