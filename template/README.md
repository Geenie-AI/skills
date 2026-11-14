# Skill template

`scripts/new-skill.sh <name>` copies these folders into place and replaces the
placeholders `{{SKILL}}` (the folder name) and `{{DATE}}` (today, ISO form):

| Template | Destination |
|---|---|
| `skill/` | `skills/<name>/` |
| `tests/` | `tests/<name>/` |
| `planning/` | `planning/<name>/` |

It then runs `scripts/skillrepo.py sync`, which generates the catalogue row in
the root `README.md` and the plugin entry in `.claude-plugin/marketplace.json`
from the skill's description. The scaffold passes `scripts/validate.py` as
generated; replace every `TODO` before the first release. The pattern it follows is described in `docs/skill-pattern.md`.
