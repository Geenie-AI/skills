# Contributing to `ledgerd`

`ledgerd` is the double-entry posting service. These conventions are enforced in review; please read them before opening a pull request.

## Branches and commits

- Branch from `main`; name branches `feat/<ticket>-<slug>`, `fix/<ticket>-<slug>` or `chore/<slug>`.
- One logical change per commit. The subject line is imperative, under 60 characters, and starts with the package it touches: `posting: reject zero-amount lines`.
- Every commit that changes behaviour references the ticket in the body: `Refs: LGR-1234`.

## Code

- Go 1.23. `gofmt` and `goimports` are mandatory; CI rejects unformatted code.
- Errors are wrapped with `fmt.Errorf("<what we were doing>: %w", err)`. Never return a bare `err` from a function that adds context, and never log and return the same error.
- Every exported function has a doc comment that starts with the function name.
- No `panic` outside `main` and test helpers.
- Money is `decimal.Decimal` from `github.com/shopspring/decimal`. Never `float64`. Never `int64` cents.
- Database access goes through the `store` package. Handlers and services never import `database/sql` or `pgx` directly.
- Context is the first parameter of any function that does I/O, named `ctx`.
- Table-driven tests with `t.Run`; test names describe the case in words: `"rejects posting with unbalanced legs"`.
- Interfaces are defined in the package that uses them, not the package that implements them.
- Feature flags are read once at startup through `config.Flags`; never read an environment variable elsewhere.

## Posting rules

- A journal must balance to zero per currency before it is persisted; this check lives in `posting.Validate` and nowhere else.
- Account codes are validated against the chart of accounts in `chart/`; adding an account code requires a migration in `migrations/` and an entry in `chart/accounts.yaml`.
- Reversals create a new journal with `reverses_journal_id` set; they never mutate the original.

## Pull requests

- Fill in the template. Link the ticket. State how you tested it.
- A PR that touches `migrations/` needs a reviewer from the `@ledger-core` team.
- Keep PRs under 400 changed lines; split otherwise.
