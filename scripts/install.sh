#!/usr/bin/env bash
# Install one of this repository's skills into a host's skills location.
#
# Usage:
#   scripts/install.sh --skill NAME --host <host> [--user|--project] [--dest DIR] [--link] [--rule]
#
#   --skill    Which skill under skills/ to install. Optional when the repository
#              holds exactly one skill.
#   --host     Which host to install for (required). One of:
#                claude   Claude Code            .claude/skills/        ~/.claude/skills/
#                codex    OpenAI Codex           .agents/skills/        ~/.agents/skills/
#                copilot  GitHub Copilot         .github/skills/        ~/.copilot/skills/
#                gemini   Gemini CLI             .gemini/skills/        ~/.gemini/skills/
#                cursor   Cursor                 .cursor/skills/        ~/.cursor/skills/
#                kiro     Kiro                   .kiro/skills/          ~/.kiro/skills/
#                agents   Any host that reads the shared .agents/skills/ layout
#                         (Codex, Copilot, Gemini CLI, Cursor, OpenCode, Amp,
#                         Goose, Roo Code, Windsurf/Devin)   ~/.agents/skills/
#                generic  Print the pointer line only (copy with --dest)
#   --user     Install for the current user (the default).
#   --project  Install into the current project (or --dest).
#   --dest     Project directory to install into (default: current directory).
#   --link     Symlink the skill folder instead of copying it.
#   --rule     Cursor only: also write .cursor/rules/<skill>.mdc from the adapter template.
#
# The source folder is never modified. For Claude Code the copied SKILL.md
# gains `disable-model-invocation: true` so the skill is user-invoked only.
# Pointer lines and snippets are generated from the skill's own frontmatter.
# Compatible with macOS bash 3.2 (no associative arrays, no mapfile).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILL=""
HOST=""
SCOPE=""
DEST=""
DEST_GIVEN=""
LINK=0
RULE=0

usage() {
  sed -n '2,27p' "$0" | sed 's/^# \{0,1\}//'
}

die() {
  echo "install.sh: $*" >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skill) SKILL="${2:-}"; shift 2 ;;
    --host) HOST="${2:-}"; shift 2 ;;
    --user) SCOPE="user"; shift ;;
    --project) SCOPE="project"; shift ;;
    --dest) DEST="${2:-}"; DEST_GIVEN=1; shift 2 ;;
    --link) LINK=1; shift ;;
    --rule) RULE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
done

# Resolve the skill: the only one, or the one named.
if [ -z "$SKILL" ]; then
  COUNT=0; ONLY=""
  for d in "$REPO_ROOT"/skills/*/; do
    [ -f "$d/SKILL.md" ] || continue
    COUNT=$((COUNT + 1)); ONLY="$(basename "$d")"
  done
  [ "$COUNT" -eq 1 ] || { usage; die "--skill is required (available: $(ls -1 "$REPO_ROOT/skills" | tr '\n' ' '))"; }
  SKILL="$ONLY"
fi
[ -n "$HOST" ] || { usage; die "--host is required"; }
SRC="$REPO_ROOT/skills/$SKILL"
[ -d "$SRC" ] || die "skill folder not found: $SRC"
[ -f "$SRC/SKILL.md" ] || die "SKILL.md not found in $SRC"

# Description from the frontmatter, used for generated pointer lines.
DESCRIPTION="$(sed -n '/^---$/,/^---$/p' "$SRC/SKILL.md" | sed -n 's/^description:[[:space:]]*//p' | head -1 | sed 's/^"\(.*\)"$/\1/')"

print_generic_pointer() {
  echo "Add this pointer to your agent's always-on instructions (AGENTS.md or equivalent):"
  echo
  echo "- \`$SKILL\` (\`skills/$SKILL/SKILL.md\`): $DESCRIPTION Read the file and follow its steps when the request matches."
}

print_codex_snippet() {
  echo "## Skills"
  echo
  echo "- \`$SKILL\` (\`.agents/skills/$SKILL/SKILL.md\`): use it, or let the user invoke it with \`\$$SKILL\`, when the request matches: $DESCRIPTION"
}

if [ -n "$DEST" ] && [ -z "$SCOPE" ]; then
  SCOPE="project"
fi
[ -n "$DEST" ] || DEST="$(pwd)"
[ -n "$SCOPE" ] || SCOPE="user"

# Resolve the target skills directory for the host. Paths come from each
# host's documentation; see adapters/README.md for the verification table.
case "$HOST" in
  claude)
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.claude/skills"; else TARGET_PARENT="$DEST/.claude/skills"; fi ;;
  codex)
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.agents/skills"; else TARGET_PARENT="$DEST/.agents/skills"; fi ;;
  copilot)
    # https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.copilot/skills"; else TARGET_PARENT="$DEST/.github/skills"; fi ;;
  gemini)
    # https://geminicli.com/docs/cli/skills/
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.gemini/skills"; else TARGET_PARENT="$DEST/.gemini/skills"; fi ;;
  cursor)
    # https://cursor.com/docs/skills (project .cursor/skills, user ~/.cursor/skills)
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.cursor/skills"; else TARGET_PARENT="$DEST/.cursor/skills"; fi ;;
  kiro)
    # https://kiro.dev/docs/skills/
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.kiro/skills"; else TARGET_PARENT="$DEST/.kiro/skills"; fi ;;
  agents)
    # The shared layout most hosts read: https://agentskills.io
    if [ "$SCOPE" = "user" ]; then TARGET_PARENT="$HOME/.agents/skills"; else TARGET_PARENT="$DEST/.agents/skills"; fi ;;
  generic)
    # Hosts without skill support only need the pointer line; the folder is
    # copied only when a --dest is given explicitly.
    SCOPE="project"
    [ -n "$DEST_GIVEN" ] || { print_generic_pointer; exit 0; }
    TARGET_PARENT="$DEST/skills"
    ;;
  *)
    die "unknown host '$HOST' (expected claude, codex, copilot, gemini, cursor, kiro, agents or generic)"
    ;;
esac

TARGET="$TARGET_PARENT/$SKILL"

# Never place the folder onto itself: with --host generic and no --dest run from
# the repo root, the target would be the shared source folder.
SRC_REAL="$(cd "$SRC" && pwd -P)"
if [ -e "$TARGET" ]; then
  TARGET_REAL="$(cd "$TARGET" 2>/dev/null && pwd -P || echo "")"
  [ "$TARGET_REAL" != "$SRC_REAL" ] || die "target $TARGET is the shared source folder; pass --dest to a project directory"
fi
case "$TARGET_PARENT/" in
  "$REPO_ROOT/skills/"*) die "target $TARGET is inside this repository's skills/ folder; pass --dest to a project directory" ;;
esac

# Idempotent placement: remove whatever is at the target (copy or link), then
# place the folder again.
mkdir -p "$TARGET_PARENT"
if [ -L "$TARGET" ]; then
  rm "$TARGET"
elif [ -d "$TARGET" ]; then
  rm -rf "$TARGET"
elif [ -e "$TARGET" ]; then
  die "refusing to replace non-directory at $TARGET"
fi

if [ "$LINK" -eq 1 ]; then
  ln -s "$SRC" "$TARGET"
  PLACED="linked"
else
  # README.md is for people browsing the repository; the installed copy
  # carries only what the model reads.
  cp -R "$SRC" "$TARGET"
  rm -f "$TARGET/README.md"
  find "$TARGET" -name '.DS_Store' -delete 2>/dev/null || true
  PLACED="copied"
fi

# Claude Code overlay: mark the installed copy as user-invoked only (H7).
if [ "$HOST" = "claude" ] && [ "$LINK" -eq 0 ]; then
  SKILL_MD="$TARGET/SKILL.md"
  if ! grep -q '^disable-model-invocation:' "$SKILL_MD"; then
    TMP="${TMPDIR:-/tmp}/skill-md.$$"
    awk 'NR==1 && $0=="---" {print; print "disable-model-invocation: true"; next} {print}' "$SKILL_MD" > "$TMP"
    mv "$TMP" "$SKILL_MD"
  fi
fi

# Cursor overlay: optional project rule generated from the adapter template.
if [ "$HOST" = "cursor" ] && [ "$RULE" -eq 1 ] && [ "$SCOPE" = "project" ]; then
  mkdir -p "$DEST/.cursor/rules"
  sed -e "s|{{SKILL}}|$SKILL|g" -e "s|{{DESCRIPTION}}|$(printf '%s' "$DESCRIPTION" | sed 's/[&|]/\\&/g')|g" \
    "$REPO_ROOT/adapters/cursor/rule.template.mdc" > "$DEST/.cursor/rules/$SKILL.mdc"
  echo "wrote $DEST/.cursor/rules/$SKILL.mdc"
fi

echo "$PLACED $SKILL -> $TARGET"

case "$HOST" in
  claude)
    if [ "$LINK" -eq 1 ]; then
      echo "note: --link keeps the shared SKILL.md as-is, so the skill stays model-invocable."
    fi
    echo "Invoke with: /$SKILL"
    ;;
  codex)
    echo "Invoke with: \$$SKILL (or /skills in the Codex CLI)."
    echo "Optional AGENTS.md lines (paste into the project's AGENTS.md):"
    echo
    print_codex_snippet
    ;;
  copilot)
    echo "Copilot picks the skill from its description; in the Copilot CLI or VS Code type /$SKILL to force it."
    ;;
  gemini)
    echo "Gemini CLI activates the skill when the request matches its description (you confirm the activation); /skills list shows it."
    ;;
  cursor)
    echo "Invoke with /$SKILL in the Agent chat, or let Cursor pick it from the description."
    [ "$RULE" -eq 1 ] || echo "Optional: add --rule --project to also write .cursor/rules/$SKILL.mdc."
    ;;
  kiro)
    echo "Invoke with /$SKILL, or let Kiro pick it from the description."
    ;;
  agents)
    echo "Hosts reading .agents/skills pick the skill from its description; Codex: \$$SKILL, Copilot/Windsurf: /$SKILL, OpenCode: @$SKILL, Goose: /skills $SKILL."
    ;;
  generic)
    print_generic_pointer
    ;;
esac
