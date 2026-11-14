# Fine-tuning gates and combining levers

Read this when behavior rows survive after prompt engineering, examples, and retrieval, and ideal examples exist (Q5). Guide sections: *Fine-tuning*, *All of the above*.

Purpose: solve learned-memory (behavior) problems by training on a domain-specific set; or reach the same accuracy cheaper (fewer prompt tokens, a smaller model) when Q15 ceilings bind.

## Gates

All must pass. When declining, list which failed in doc § 14.

- **G6.1 Baseline and axis.** A baseline eval exists and the failing rows are tagged **behavior**.
- **G6.2 Examples.** ≥ 50 high-quality examples exist or can be produced (Q5). Quality over quantity; scale up only if accuracy is still short and the errors remain behavioral.
- **G6.3 Representative.** Examples match production inputs, including the system prompt and, if retrieval is present, retrieved context in the same format, so the model does not learn to use context that is not there.
- **G6.4 Hold-out.** A hold-out set is reserved to detect overfitting.
- **G6.5 Permission.** Q20 and Q22(h) permit training on the data. (Whether the target offers fine-tuning for the chosen model is an emit question, recorded in doc § 12 as a gap, never a gate: the diagnosis and lever plan stay target-neutral.)

Dataset source of choice: **prompt baking**. Log inputs and outputs from the pilot (Q17), prune to a clean, realistic set, and keep the production prompt in every example.

Calibration from the guide's Icelandic case: fine-tuned GPT-3.5 (78 BLEU) beat few-shot GPT-4 (70); fine-tuned GPT-4 reached 87.

## Fine-tune spec (`finetune/README.md`, `finetune/format-example.jsonl`)

| Item | Content |
|---|---|
| Rows served | The behavior rows this lever addresses |
| Method | Supervised by default; preference-based only when the examples are pairs of better/worse outputs |
| Dataset | Source (logs, corrected pairs), count, selection rule, format (chat messages including the production system prompt and retrieved context) |
| Hold-out | Size and how it is kept apart |
| Before/after eval | The eval set and metric from doc § 9, run on the hold-out before and after |
| Prompt change | What the fine-tune replaces in the prompt (few-shot block, long instructions) and the token saving |
| Upkeep | Retraining trigger (Q23): drift in the eval, a format change |

## Combining levers (guide § All of the above)

When the post-baseline diagnosis carries both axes: fine-tuning carries the consistent behavior and shrinks the prompt; retrieval injects specialised or current context. Order of work: tune retrieval first, then retrain on the improved retrieval inputs (the guide's six-step journey, steps 5–6). Write this as two separate milestones with an eval between them.
