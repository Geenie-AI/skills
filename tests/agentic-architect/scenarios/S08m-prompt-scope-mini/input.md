Fix the drafting prompt. It is step 4 of our HR reply pipeline on Claude Code (Claude Sonnet). The drafting prompt is in `artifacts/drafting-prompt.md`; it is the task 4 section of the big system prompt plus the conduct rules and category guidance it uses. Three failures with what we wanted instead are in `artifacts/failures.md`. The manual clauses those tickets needed are in `artifacts/policy-excerpt.md`; the full manual is about 90k tokens and I have not attached it.

For context, the other steps are (we are not changing them this sprint):
- Step 1 extract: pulls question, facts, missing facts and tone out of the employee email.
- Step 2 classify: picks a category, sub-category, urgency and the manual sections to consult.
- Step 3 enrich: the full policy manual is pasted into the context and the model lists relevant clauses verbatim.
- Step 5 format: converts the draft into our JSON schema.
All five steps run in one call with one system prompt, so by step 4 the model has the whole manual and steps 1 to 3 in context (about 100k tokens).

Just the drafting prompt, please, plus a way to test it.
