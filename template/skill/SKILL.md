---
name: {{SKILL}}
description: TODO one or two sentences that say what the skill does and when a host should use it (this text is what hosts match requests against; 1–1024 characters).
---

# {{SKILL}}

TODO: one paragraph. What the skill produces, in how many steps, and the
requests it declines in one sentence.

Leading words: **TODO** (the first term the skill uses throughout), **TODO**.

Output goes to the `{{SKILL}}-output` folder of the project (file conventions in
`templates/output.md`). Use capability verbs: read the file, search the working
directory, present the questions in one message and wait for the reply.

**Non-interactive runs.** When the request says the user's answers are in a
file: each time you would ask a question, append one line to the named log
(`<upfront|deferred> <Qid> | <reason it could not be derived> | <decision it
affects>`), take the answer from the file, and treat every confirmation as
given by the file. A question with no answer falls back to its default, tagged
`default (unanswered)`.

## 1. Intake

Read `reference/rules.md`.

1. Derive every fact you can from the request and the working directory (Q1).
2. Ask the remaining questions in one numbered batch, each with its ID, the guess in brackets, and the reason it could not be derived.

Done when: every question has an answer or a default, each tagged with its source.

## 2. Produce

1. Apply R1 to every input.
2. Write `output.md` from `templates/output.md` and run its checklist.

Done when: every section of the template is filled or marked `n/a`, and every decision cites the rule that made it.
