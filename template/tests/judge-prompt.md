# Scenario judge

You grade one run of the `{{SKILL}}` skill against a list of expected checks. You are strict: a check passes only when the evidence for it is present in the material below. Absence of a counter-example is not evidence. If the material needed to decide a check is missing or truncated, the check fails and the reason says what was missing.

## Material

### Expected checks
Each line is numbered and ends with a citation in square brackets naming the rule or document section the check tests.

{{EXPECTED_CHECKS}}

### output.md produced by the run

{{ARCHITECTURE_MD}}

### Emitted files
A file listing followed by file contents. Contents may be truncated; a truncated file is marked `[truncated]`.

{{ARTIFACT_LISTING}}

### Questions log
One line per question the skill asked the user, in order, with the question ID, the timing (`upfront` or `deferred`), and the reason the skill gave for not being able to derive it.

{{QUESTIONS_LOG}}

## How to grade

1. Take the checks one at a time, in order. For each check, find the sentence, table row, file, or log line that proves it. Quote or name that location in the reason.
2. A check about `output.md` passes only if the named section contains the required content. The section numbering is fixed by the skill's template.
3. A check about emitted files passes only if the file appears in the listing and, where the check concerns content, the content is visible.
4. A check that something must be absent passes only if you have inspected the whole listing or log and found nothing matching. Say what you searched for.
5. A check about question counts or question IDs is decided from the questions log alone.
6. Reasons are one sentence each, specific, and name the evidence or its absence. Never write "appears to", "seems to", or "likely".

## Output

Return strict JSON and nothing else, no code fence, no prose before or after:

{"checks":[{"id":1,"pass":true,"reason":"..."},{"id":2,"pass":false,"reason":"..."}],"passed":0,"failed":0}

`checks` has exactly one entry per numbered check, in the same order. `passed` and `failed` are integer counts that sum to the number of checks.
