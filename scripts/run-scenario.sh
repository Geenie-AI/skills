#!/usr/bin/env bash
# Drive one acceptance scenario of one skill through a host, then grade the result.
#
# Usage:
#   scripts/run-scenario.sh --skill NAME --host claude|codex --scenario <dir-name-or-ID>
#                           [--out DIR] [--model M] [--judge-only] [--keep]
#                           [--answers FILE] [--label L] [--baseline DIR] [--dry-run]
#
#   --skill      A folder under skills/ (its scenarios live in tests/<skill>/scenarios/).
#                Optional when the repository holds exactly one skill.
#   --scenario   A directory name under tests/<skill>/scenarios/ (S02-hr-helpdesk)
#                or its ID prefix (S02).
#   --out        Where results.json, summary.md and the project live
#                (default: .eval-results/<skill>/<label>-<host>).
#   --model      Model passed to the host for the skill run (host default otherwise).
#   --judge-only Skip the skill run; grade the project already under --out.
#   --keep       Keep the temp project after grading in CI (it is always kept locally).
#   --answers    Answer file inside the scenario dir (default answers.yaml); a
#                variant rerun passes another file, e.g. answers-generic.yaml.
#   --label      Name for this run in results and paths (default: scenario name,
#                or <scenario>-<suffix> for a variant).
#   --baseline   Results dir of an earlier run whose primary document is diffed
#                against this run's; the diff is supplied to the judge. Defaults
#                to the skill's configured baseline scenario for the same host
#                when such a run exists next to --out or under .eval-results/.
#   --dry-run    Build the temp project and the prompt, then stop (no host call).
#
# Requires: python3, and `claude` (Claude Code) or `codex` (OpenAI Codex CLI).
# The runner installs the skill into a temp project, writes the scenario input
# behind the skill's non-interactive preamble (tests/<skill>/preamble.md), runs
# the host with file-write permission, then asks the host's model to judge the
# output against expected-checks.md with tests/<skill>/judge-prompt.md.
#
# Host flags were checked against the vendors' docs on 2026-11-14; items marked
# "verify:" could not be confirmed and may need adjusting. See adapters/README.md.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILL=""
HOST=""
SCENARIO=""
OUT=""
MODEL=""
JUDGE_ONLY=0
KEEP=0
ANSWERS="answers.yaml"
LABEL=""
BASELINE=""
DRY_RUN=0

die() { echo "run-scenario: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "required binary '$1' not found on PATH${2:+ ($2)}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --skill) SKILL="${2:-}"; shift 2 ;;
    --host) HOST="${2:-}"; shift 2 ;;
    --scenario) SCENARIO="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --model) MODEL="${2:-}"; shift 2 ;;
    --judge-only) JUDGE_ONLY=1; shift ;;
    --keep) KEEP=1; shift ;;
    --answers) ANSWERS="${2:-}"; shift 2 ;;
    --label) LABEL="${2:-}"; shift 2 ;;
    --baseline) BASELINE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

need python3
REPO="$SCRIPT_DIR/skillrepo.py"

if [ -z "$SKILL" ]; then
  SKILL="$(python3 "$REPO" list)"
  [ "$(printf '%s\n' "$SKILL" | grep -c .)" -eq 1 ] || die "--skill is required (more than one skill in the repository)"
fi
[ -n "$HOST" ] || die "--host is required (claude or codex)"
[ -n "$SCENARIO" ] || die "--scenario is required"
case "$HOST" in claude|codex) ;; *) die "unknown host '$HOST'" ;; esac
[ -f "$REPO_ROOT/skills/$SKILL/SKILL.md" ] || die "no skill at skills/$SKILL"

TESTS_DIR="$REPO_ROOT/tests/$SKILL"
SCENARIOS_DIR="$TESTS_DIR/scenarios"
JUDGE_TEMPLATE="$TESTS_DIR/judge-prompt.md"
PREAMBLE_FILE="$TESTS_DIR/preamble.md"
[ -f "$JUDGE_TEMPLATE" ] || die "judge template missing: $JUDGE_TEMPLATE"
[ -f "$PREAMBLE_FILE" ] || die "preamble missing: $PREAMBLE_FILE"

# Skill settings from tests/<skill>/config.yaml.
OUTPUT_DIR="$(python3 "$REPO" config "$SKILL" eval.output_dir)"
PRIMARY_DOC="$(python3 "$REPO" config "$SKILL" eval.primary_document)"
BASELINE_SCENARIO="$(python3 "$REPO" config "$SKILL" eval.baseline.scenario)"
[ -n "$OUTPUT_DIR" ] || die "eval.output_dir is not set in tests/$SKILL/config.yaml"
[ -n "$PRIMARY_DOC" ] || die "eval.primary_document is not set in tests/$SKILL/config.yaml"

# Resolve the scenario directory (full name or ID prefix).
if [ -d "$SCENARIOS_DIR/$SCENARIO" ]; then
  SCENARIO_DIR="$SCENARIOS_DIR/$SCENARIO"
else
  MATCHES="$(cd "$SCENARIOS_DIR" && ls -1d "$SCENARIO"-* 2>/dev/null || true)"
  COUNT="$(printf '%s\n' "$MATCHES" | grep -c . || true)"
  [ "$COUNT" -eq 1 ] || die "scenario '$SCENARIO' matches $COUNT directories under tests/$SKILL/scenarios/"
  SCENARIO_DIR="$SCENARIOS_DIR/$MATCHES"
fi
SCENARIO_NAME="$(basename "$SCENARIO_DIR")"
for f in input.md "$ANSWERS" expected-checks.md; do
  [ -f "$SCENARIO_DIR/$f" ] || die "scenario $SCENARIO_NAME is missing $f"
done
if [ -z "$LABEL" ]; then
  LABEL="$SCENARIO_NAME"
  if [ "$ANSWERS" != "answers.yaml" ]; then
    SUFFIX="${ANSWERS#answers-}"; SUFFIX="${SUFFIX%.yaml}"
    LABEL="$SCENARIO_NAME-$SUFFIX"
  fi
fi

[ -n "$OUT" ] || OUT="$REPO_ROOT/.eval-results/$SKILL/$LABEL-$HOST"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
PROJECT="$OUT/project"

if [ "$DRY_RUN" -eq 0 ]; then
  case "$HOST" in
    claude) need claude "install Claude Code: npm install -g @anthropic-ai/claude-code" ;;
    codex)  need codex  "install the Codex CLI: npm install -g @openai/codex" ;;
  esac
fi

# --------------------------------------------------------------------------- #
# 1. Build the temp project
# --------------------------------------------------------------------------- #
if [ "$JUDGE_ONLY" -eq 0 ]; then
  rm -rf "$PROJECT"
  mkdir -p "$PROJECT"
  if [ -d "$SCENARIO_DIR/fixtures/repo" ]; then
    cp -R "$SCENARIO_DIR/fixtures/repo/." "$PROJECT/"
    # Repo stubs cannot hold literal dot-directories (local tooling refuses to
    # write .claude/ and friends), so fixtures use dot-claude/, dot-agents/ ...
    # Rename them here, deepest first so nested ones resolve.
    find "$PROJECT" -depth -type d -name 'dot-*' | while IFS= read -r d; do
      mv "$d" "$(dirname "$d")/.${d##*/dot-}"
    done
  fi
  if [ -d "$SCENARIO_DIR/fixtures/artifacts" ]; then
    mkdir -p "$PROJECT/artifacts"
    cp -R "$SCENARIO_DIR/fixtures/artifacts/." "$PROJECT/artifacts/"
  fi
  cp "$SCENARIO_DIR/$ANSWERS" "$PROJECT/answers.yaml"
  if [ -f "$SCENARIO_DIR/fixtures/build.py" ]; then
    python3 -I "$SCENARIO_DIR/fixtures/build.py" "$PROJECT"
  fi
  : > "$PROJECT/questions.log"
  (cd "$PROJECT" && git init -q . 2>/dev/null || true)

  "$SCRIPT_DIR/install.sh" --skill "$SKILL" --host "$HOST" --project --dest "$PROJECT" >/dev/null

  PROMPT_FILE="$OUT/prompt.md"
  {
    case "$HOST" in
      claude) echo "/$SKILL" ;;
      codex)  echo "Use the \$$SKILL skill (.agents/skills/$SKILL/SKILL.md) for this request." ;;
    esac
    echo
    cat "$PREAMBLE_FILE"
    echo
    cat "$SCENARIO_DIR/input.md"
  } > "$PROMPT_FILE"

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "run-scenario: dry run; project built at $PROJECT, prompt at $PROMPT_FILE"
    exit 0
  fi

  # ------------------------------------------------------------------------- #
  # 2. Run the host headlessly with file-write permission
  # ------------------------------------------------------------------------- #
  echo "run-scenario: running $SKILL/$LABEL on $HOST (project: $PROJECT)"
  RUN_LOG="$OUT/run-output.txt"
  case "$HOST" in
    claude)
      # Docs: https://code.claude.com/docs/en/headless  (flags verified 2026-11-14)
      # acceptEdits lets the skill write files; Bash is limited to read-only
      # inspection commands via permission-rule prefixes.
      set +e
      (cd "$PROJECT" && claude -p "$(cat "$PROMPT_FILE")" \
          --output-format json \
          --permission-mode acceptEdits \
          --allowedTools "Read,Write,Edit,Glob,Grep,Bash(wc *),Bash(ls *),Bash(cat *),Bash(find *),Bash(grep *),Bash(python3 *)" \
          ${MODEL:+--model "$MODEL"} \
          ${CLAUDE_EXTRA_ARGS:-}) > "$RUN_LOG" 2> "$OUT/run-stderr.txt"
      STATUS=$?
      set -e
      ;;
    codex)
      # Docs: https://learn.chatgpt.com/docs/non-interactive-mode (flags verified 2026-11-14)
      # --sandbox workspace-write allows edits inside the project; -a never
      # suppresses approval prompts; --full-auto is no longer supported.
      # verify: -m/--model spelling at
      #   https://learn.chatgpt.com/docs/codex/developer-commands?surface=cli#cli-codex-exec
      set +e
      codex exec -C "$PROJECT" \
          --sandbox workspace-write \
          -a never \
          --skip-git-repo-check \
          --json \
          -o "$OUT/last-message.md" \
          ${MODEL:+-m "$MODEL"} \
          ${CODEX_EXTRA_ARGS:-} \
          "$(cat "$PROMPT_FILE")" > "$RUN_LOG" 2> "$OUT/run-stderr.txt"
      STATUS=$?
      set -e
      ;;
  esac
  [ "$STATUS" -eq 0 ] || echo "run-scenario: host exited with status $STATUS (see $OUT/run-stderr.txt)" >&2
  cp "$PROJECT/questions.log" "$OUT/questions.log" 2>/dev/null || true
fi

[ -d "$PROJECT" ] || die "no project under $OUT; run without --judge-only first"

# --------------------------------------------------------------------------- #
# 3. Judge
# --------------------------------------------------------------------------- #
JUDGE_PROMPT="$OUT/judge-prompt.md"
JUDGE_OUT="$OUT/judge-output.txt"

# Cross-run diff for scenarios graded against the skill's baseline run.
if [ -z "$BASELINE" ] && [ -n "$BASELINE_SCENARIO" ] && [ "$SCENARIO_NAME" != "$BASELINE_SCENARIO" ]; then
  for cand in "$(dirname "$OUT")/$BASELINE_SCENARIO-$HOST" "$REPO_ROOT/.eval-results/$SKILL/$BASELINE_SCENARIO-$HOST" "$REPO_ROOT/eval-out/$SKILL/$BASELINE_SCENARIO-$HOST"; do
    [ -d "$cand" ] && { BASELINE="$cand"; break; }
  done
fi
EXTRA_ARGS=""
if [ -n "$BASELINE" ]; then
  BASE_DOC=""
  for cand in "$BASELINE/project/$OUTPUT_DIR/$PRIMARY_DOC" "$BASELINE/produced/$PRIMARY_DOC"; do
    [ -f "$cand" ] && { BASE_DOC="$cand"; break; }
  done
  THIS_DOC="$PROJECT/$OUTPUT_DIR/$PRIMARY_DOC"
  DIFF_NAME="diff-vs-$(basename "$BASELINE" | sed "s/-$HOST\$//" | sed 's/-.*//').md"
  if [ -n "$BASE_DOC" ] && [ -f "$THIS_DOC" ]; then
    diff -u "$BASE_DOC" "$THIS_DOC" > "$OUT/$DIFF_NAME" || true
    EXTRA_ARGS="--extra-file $OUT/$DIFF_NAME"
    echo "run-scenario: diff against $BASE_DOC written to $OUT/$DIFF_NAME"
  else
    echo "run-scenario: baseline $PRIMARY_DOC not found under $BASELINE; cross-run checks will fail" >&2
  fi
fi

# shellcheck disable=SC2086
python3 "$SCRIPT_DIR/grade-scenario.py" judge-prompt \
  --skill "$SKILL" --scenario "$SCENARIO_DIR" --project "$PROJECT" $EXTRA_ARGS > "$JUDGE_PROMPT"

echo "run-scenario: judging"
set +e
case "$HOST" in
  claude)
    # --bare skips skill/hook discovery (good for a plain judge call) but reads
    # only ANTHROPIC_API_KEY, not a login or Workload Identity Federation, so it
    # is used only when that key is set.
    (cd "$OUT" && claude -p "$(cat "$JUDGE_PROMPT")" \
        ${ANTHROPIC_API_KEY:+--bare} \
        --output-format json \
        --permission-mode dontAsk \
        --max-turns 1 \
        ${JUDGE_MODEL:+--model "$JUDGE_MODEL"}) > "$JUDGE_OUT" 2> "$OUT/judge-stderr.txt"
    ;;
  codex)
    codex exec -C "$OUT" --sandbox read-only -a never --skip-git-repo-check \
        -o "$JUDGE_OUT" \
        ${JUDGE_MODEL:+-m "$JUDGE_MODEL"} \
        "$(cat "$JUDGE_PROMPT")" > "$OUT/judge-stream.txt" 2> "$OUT/judge-stderr.txt"
    ;;
esac
JUDGE_STATUS=$?
set -e
[ "$JUDGE_STATUS" -eq 0 ] || echo "run-scenario: judge exited with status $JUDGE_STATUS" >&2

# --------------------------------------------------------------------------- #
# 4. Score
# --------------------------------------------------------------------------- #
set +e
python3 "$SCRIPT_DIR/grade-scenario.py" score \
  --skill "$SKILL" --scenario "$SCENARIO_DIR" --project "$PROJECT" \
  --judge-output "$JUDGE_OUT" --out "$OUT" --host "$HOST" --answers "$ANSWERS" --label "$LABEL"
RESULT=$?
set -e

if [ "$KEEP" -eq 0 ] && [ "$JUDGE_ONLY" -eq 0 ] && [ -n "${CI:-}" ]; then
  # In CI keep only the produced artifacts, not the whole temp project.
  mkdir -p "$OUT/produced"
  cp -R "$PROJECT/$OUTPUT_DIR/." "$OUT/produced/" 2>/dev/null || true
  rm -rf "$PROJECT"
fi

echo "run-scenario: results in $OUT/results.json"
exit "$RESULT"
