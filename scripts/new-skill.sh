#!/usr/bin/env bash
# Scaffold a new skill package from template/.
#
# Usage:
#   scripts/new-skill.sh <name>
#
#   <name>   Lowercase letters, digits and single hyphens (the Agent Skills
#            name rule); becomes skills/<name>, tests/<name>, planning/<name>.
#
# Replaces {{SKILL}} and {{DATE}} in the copied files, then runs
# `scripts/skillrepo.py sync` so the README catalogue and the marketplace get
# their row and entry, and prints what to do next.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$REPO_ROOT/template"

NAME=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "new-skill: unknown argument $1" >&2; exit 1 ;;
    *) NAME="$1"; shift ;;
  esac
done

die() { echo "new-skill: $*" >&2; exit 1; }

[ -n "$NAME" ] || die "a skill name is required"
printf '%s' "$NAME" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$' || die "name must be lowercase letters, digits and single hyphens"
[ "${#NAME}" -le 64 ] || die "name must be at most 64 characters"
for d in "skills/$NAME" "tests/$NAME" "planning/$NAME"; do
  [ ! -e "$REPO_ROOT/$d" ] || die "$d already exists"
done
[ -d "$TEMPLATE/skill" ] || die "template/skill is missing"

DATE="$(date +%Y-%m-%d)"

copy_tree() {
  # copy_tree SRC DEST: copy and substitute placeholders in every file
  mkdir -p "$2"
  (cd "$1" && find . -type d) | while IFS= read -r d; do mkdir -p "$2/$d"; done
  (cd "$1" && find . -type f) | while IFS= read -r f; do
    sed -e "s/{{SKILL}}/$NAME/g" -e "s/{{DATE}}/$DATE/g" "$1/$f" > "$2/$f"
  done
}

copy_tree "$TEMPLATE/skill" "$REPO_ROOT/skills/$NAME"
copy_tree "$TEMPLATE/tests" "$REPO_ROOT/tests/$NAME"
copy_tree "$TEMPLATE/planning" "$REPO_ROOT/planning/$NAME"

# One catalogue row and one marketplace entry per skill, generated from SKILL.md.
(cd "$REPO_ROOT" && python3 scripts/skillrepo.py sync >/dev/null)

cat <<EOF
Scaffolded $NAME:
  skills/$NAME/        SKILL.md, README.md, reference/, templates/
  tests/$NAME/         config.yaml, preamble.md, judge-prompt.md, scenarios/S01-first-request/
  planning/$NAME/      00-README.md
  README.md and .claude-plugin/marketplace.json   catalogue row and plugin entry (from the description)

Next:
  1. Write planning/$NAME/ (rules with IDs and sources, output spec, scenarios).
  2. Replace every TODO in skills/$NAME/ and tests/$NAME/.
  3. python3 scripts/validate.py --skill $NAME
  4. scripts/run-scenario.sh --skill $NAME --host claude --scenario S01
  5. Fill the README, add a CHANGELOG.md entry under Unreleased; the next vX.Y.Z tag ships it.
EOF
