# Template: eval set

Emit three files under `eval/`. Sizes and metric come from doc § 9.

## `eval/README.md`

```markdown
# Eval: <solution> / <step or system>
serves: D…, A…
Set: <n> items in `set.jsonl` (target ≥ 20; plan to reach <n> from <source> by milestone <k>)
Metric: <exact | schema | judge-rubric | pairwise>; tool-call accuracy / routing accuracy: <yes/no>
Grid: retrieval axis (right chunk id in top-k) and answer axis scored separately: <yes/no>
Context sizes: <e.g. 8k, 32k, full> (only when a step exceeds the long-context threshold)
Calibration: <n ≥ 10> human-labelled items; report judge agreement before trusting the judge
Hold-out: <n> items kept apart (only when fine-tuning is planned)
Language: <Q9>
Loop: run → list failures → one hypothesis per failure → one change → re-run. Owner: <Q23>
Do-no-harm gate (when an eval already passes): the restructured prompt must match or beat <x %> on the same items.
```

## `eval/set.jsonl`

One object per line. Fields depend on the metric; keep ids stable so doc § 11 can cite them.

```json
{"id": "E001", "input": "<the user input or step payload>", "expected": "<reference answer or schema-valid object>", "expected_chunk_ids": ["POL-7.3.2"], "class": "<routing label if any>", "expected_tool": "<tool name if any>", "notes": "<why this item is in the set>"}
```

## `eval/judge-prompt.md`

```markdown
<!-- serves: D…; metric: judge-rubric -->
You grade one output of <solution> against the rubric below. Output JSON only.

Rubric (score each 0–2, then overall pass when every critical criterion scores 2):
1. <criterion, critical> — e.g. every cited clause id exists in the provided sources and supports the claim
2. <criterion> — e.g. the answer states what it could not answer instead of guessing
3. <criterion> — format matches the schema

Input: {{input}}
Sources provided to the model: {{sources}}
Output under test: {{output}}
Reference (if any): {{expected}}

Return: {"scores": {"1": n, "2": n, "3": n}, "pass": true|false, "reason": "<one sentence>"}
```

Write the rubric in the output language (Q9), with one criterion per line of Q4's correct/incorrect description.
