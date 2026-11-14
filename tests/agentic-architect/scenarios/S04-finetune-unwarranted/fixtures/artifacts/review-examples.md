# Code review examples (8) and the reviewer's misses

Each example is a diff hunk, what the current reviewing prompt produced, and what a senior maintainer wrote. The current reviewer runs in Claude Code with a short prompt: "Review this diff for bugs and style issues in a Go service."

## E1

```go
func (s *Service) Post(ctx context.Context, j Journal) error {
	if err := s.store.Insert(ctx, j); err != nil {
		log.Printf("insert failed: %v", err)
		return err
	}
	return nil
}
```
Reviewer produced: "Looks fine. Consider adding a comment."
Maintainer wrote: "Logs and returns the same error (CONTRIBUTING: errors). Wrap instead: `return fmt.Errorf("inserting journal %s: %w", j.ID, err)`. Also, `Validate` is not called before `Insert`; the balance check must run first (posting rules)."

## E2

```go
amount := float64(line.Cents) / 100
```
Reviewer produced: "Fine."
Maintainer wrote: "Money as float64 is forbidden (CONTRIBUTING: code). Use `decimal.NewFromInt(line.Cents).Div(decimal.NewFromInt(100))`, or better, carry `decimal.Decimal` from the input."

## E3

```go
import "database/sql"

func (h *Handler) List(w http.ResponseWriter, r *http.Request) {
	rows, err := h.db.QueryContext(r.Context(), "select ...")
```
Reviewer produced: "Check that rows are closed."
Maintainer wrote: "Handlers never import `database/sql` (CONTRIBUTING: code). Move the query into `store` and call it from here. Rows closing is secondary."

## E4

Commit subject: `Fixed the bug in reversal`
Reviewer produced: nothing about the subject.
Maintainer wrote: "Subject line: imperative, package-prefixed, under 60 characters: `posting: set reverses_journal_id on reversal`. Add `Refs: LGR-1402`."

## E5

```go
func process(j Journal, ctx context.Context) error {
```
Reviewer produced: "Fine."
Maintainer wrote: "`ctx` is the first parameter (CONTRIBUTING: code)."

## E6

Migration adds account code `7120` without touching `chart/accounts.yaml`.
Reviewer produced: "Migration looks correct."
Maintainer wrote: "New account codes need both the migration and an entry in `chart/accounts.yaml` (posting rules). Also, this PR touches `migrations/` so it needs a `@ledger-core` reviewer."

## E7

```go
if os.Getenv("LEDGERD_FAST_PATH") == "1" {
```
Reviewer produced: "Consider using a constant for the env var name."
Maintainer wrote: "Flags are read once at startup through `config.Flags`; read it from there (CONTRIBUTING: code)."

## E8

```go
func TestPost(t *testing.T) {
	// case 1
	...
	// case 2
```
Reviewer produced: "Add more test cases."
Maintainer wrote: "Table-driven with `t.Run` and descriptive names (CONTRIBUTING: code): `"rejects posting with unbalanced legs"`, `"accepts balanced multi-currency journal"`."

In all eight, the reviewer missed a convention that is written in `CONTRIBUTING.md`. The reviewer prompt does not include or point at that file.
