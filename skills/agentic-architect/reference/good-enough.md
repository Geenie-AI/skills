# Good-enough accuracy and graceful failure

Read this in every run that fills doc § 10. Guide section: *How much accuracy is "good enough"*.

Off-the-shelf methods rarely reach near-perfect accuracy; the job is to decide when accuracy is sufficient and to manage the risk of failure.

## Business worksheet (from Q18)

Replicate the guide's customer-service table with the user's figures. If Q18 is unknown, use the symmetric placeholder (+1 success, −1 failure, break-even 50 %), flag it in doc § 2 and § 10, and tell the user it is the first number to replace.

| Event | Value per case | Expected share | Contribution |
|---|---|---|---|
| Success | +V_s | p | p · V_s |
| Failure type 1 (e.g. unnecessary escalation) | −C_1 | (1−p) · s_1 | −(1−p) · s_1 · C_1 |
| Failure type 2 (e.g. wrong answer accepted) | −C_2 | (1−p) · s_2 | −(1−p) · s_2 · C_2 |
| **Break-even accuracy p\*** | solve contribution = 0 | | p\* = Σ s_i·C_i ÷ (V_s + Σ s_i·C_i) |

Worked example from the guide: +$20 success, −$40 escalation (95 % of failures), −$1000 churn (5 % of failures) → p\* ≈ 81.5 %. Show the arithmetic in the document.

Then estimate the **realistic accuracy** the chosen levers can reach (cite the eval if one exists, otherwise the guide's calibration points and say it is an estimate) and state the gap to p\*.

Decision rules:

- Realistic accuracy below p\*: keep the human in the lead and the model as assistant for the risky decision class, and say so. Then recompute p\* with the handoff in place, because routing uncertain cases away changes the failure shares.
- Failures mostly cheap (early escalation): a lower accuracy can still be worth shipping.
- Root cause blocked by Q21/Q22 and accuracy below p\*: flag at the top of the document (SC3 extended) and show the design the user would get by relaxing the constraint.

Pilot metrics to track: CSAT human vs AI, decision accuracy from retrospective review, time to resolution.

## Technical worksheet (from Q19)

Choose at least one graceful-failure pattern per failure type and record the chosen point:

| Pattern | Mechanism | Trade | Permission |
|---|---|---|---|
| Ask for clarification | The model requests more information when unsure | First-attempt accuracy down, two-turn accuracy up | Q22(f) |
| Return to an earlier stage | A later step sends the case back to intent detection or routing, once, with a widened query | Latency | Q22(a) |
| Hand off to a human | Below a confidence threshold, after a failed verification, or on an irreversible action (Q16, R9.3) | Short-term savings down, churn risk down | Q22(g) |

The handoff policy (doc § 10 and `handoff-policy.md`) is a decision table:

| Failure type | Pattern | Threshold / trigger | Owner |
|---|---|---|---|

Name a measurable trigger for every row (confidence field below a value, unsupported-claim count above zero after verification, a tool marked irreversible). In `prompt` scope the abstain output (R4.7) is the prompt-level handoff and § 10 is `n/a (scope)`.
