# Intake profiles

A profile is a stored record of intake answers keyed by ID, with a provenance tag and a date on each answer. A run that names a profile loads it, fills the intake table, and asks only what is missing, stale, or per-run (procedure in `../reference/intake-questions.md` § Profiles).

## Resolution order

| Source | Form | Lookup |
|---|---|---|
| Skill store | `profiles/<id>.yaml` beside this README | read the file |
| Project store | `<project>/.agentic-architect/profiles/<id>.yaml` | read the file |
| Previous run | `<project>/agentic-architecture/**/architecture.md` whose header shows `Profile: <id>` | read its § 1 Intake |
| External system | A tool or MCP server the user has configured that returns a record for an ID, with a mapping in `mappings/<source>.yaml` | call the tool; apply the mapping |

Resolution stops at the first source that returns the ID. A profile may name a `parent`; child answers override parent answers. If no source returns the ID, report it, continue with the normal intake, and offer to create the profile at the end. An unreachable external source counts as "no profile".

## Record format

```yaml
profile_id: acme-helpdesk
parent: acme-defaults            # optional
updated: 2026-11-14
staleness_days: 90               # optional; default 90
answers:
  Q2:  { value: "OpenAI Agents SDK; gpt-5", source: user, at: 2026-11-10 }
  Q6:  { value: "HR policy pages (~400)", source: "external:crm.kb_summary", at: 2026-11-14 }
  Q18: { value: "+15 / -200 wrong accepted / -10 ticket", source: user, at: 2026-09-01 }
  Q22: { value: "a:yes b:yes c:yes d:yes e:yes f:yes g:yes h:ask i:no j:yes", source: user, at: 2026-09-01 }
```

`source` is one of `user`, `artifact`, `profile:<id>` (inherited), `external:<system.field>`, `default`. When loaded into a run, every row is shown in doc § 1 as `profile:<id>` with its `at` date.

## What a profile may answer

| Block | May fill | Rule |
|---|---|---|
| I Scope | Q26 yes; Q25 no | Scope is per run |
| A Mode and target | Q2 yes; Q1 no | Mode is per run; a profile may point at artifacts for optimize mode, the user confirms the mode |
| B Task, C Knowledge, D Consistency, F Envelope | yes | External sources are preferred for C: size and change frequency drift |
| E Failures | no | Q11–Q14 are per run; a profile may point at a trace export the skill reads to *propose* failure rows, which the user confirms |
| G Risk | yes | Q18 figures older than the staleness window are re-confirmed |
| H Permissions | yes | Still shown back lazily, item by item, when a lever relies on them |

Staleness: an answer older than `staleness_days` is shown with its date and asked again; "keep" is a valid reply.

## Write-back

At the end of a run, offer to write answers the user gave or changed to the project store (`.agentic-architect/profiles/<id>.yaml`), or to the skill store when the skill folder is writable. Never write to an external system.
