# {{SKILL}} — planning documents

Design documents the `skills/{{SKILL}}` skill is built from. Write these
first; the skill, its scenarios and the validator share the rule IDs defined
here.

| File | What it holds | Read it when |
|---|---|---|
| `01-skill-plan.md` | Goal, scope, what the skill declines, file layout, acceptance criteria | Starting the build, or checking what "done" means |
| `02-rules.md` | The rules the skill encodes, with IDs and the source section each comes from | Writing the reference files |
| `03-output-spec.md` | The document and artifacts the skill produces, with numbered sections | Writing the templates; reviewing a produced result |
| `04-scenarios.md` | Worked scenarios used as the acceptance tests | Writing `tests/{{SKILL}}/scenarios/` |

## Reference conventions

- `doc § n` means a section of the produced `output.md` (template in `03-output-spec.md`).
- Rule IDs: `Q` for intake questions, `R` for rules. Add families as needed and list them here.

## Source of truth

TODO: name the method, guide or standard the skill encodes. Where a rule goes
beyond it, say so explicitly so the two can be kept apart.
