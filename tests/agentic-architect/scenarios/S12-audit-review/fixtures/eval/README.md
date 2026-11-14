# Existing eval for the support reply prompt

`support-reply-eval.jsonl`: 40 items, one per line, with the header block, the customer message, the expected `type`, `priority`, `needs_human`, the expected tags, and a rubric line a judge checks the reply against. Scored by `scripts/eval.py` (not included): type, priority and needs_human by exact match, tags by set overlap, reply by a rubric judge. Last run on 2026-11-09 with the v22 prompt: 93 percent (37 of 40 pass; misses were items 11, 23 and 36).
