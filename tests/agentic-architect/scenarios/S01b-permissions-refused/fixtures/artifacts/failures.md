# Observed failures — Northwind reply pipeline (three of eleven logged in October 2026)

All three ran through the v14 prompt in a single call. Context at the point of drafting (task 4) was measured from the trace at roughly 100k tokens: the 9k-token prompt with the 90k-token manual pasted in, plus the outputs of tasks 1 to 3.

## Failure 1 — invented clause (ticket HR-21104)

**Input**

```
ticket_id: HR-21104
employee_id: E-5120
first_name: Daniel
manager: Ruth Okafor
message: I'm moving to the hybrid arrangement next month (tier 2 I think). Is there any money towards a desk? Mine is a kitchen table.
```

**Produced (task 4 body, abridged)**

> Yes, there is support for this. Under the Home Office Furniture Reimbursement Scheme you can claim up to EUR 600 for a desk and chair once your hybrid arrangement starts (POL-12.4.1). Submit the receipts through the expenses system within 90 days (POL-12.4.3). Your manager does not need to approve the purchase.

Citations in the JSON: `POL-12.4.1`, `POL-12.4.3`. Neither exists; the manual has eleven sections.

**Should have produced**

> Yes. Employees approved at Tier 2 or Tier 3 can claim a one-time home office allowance of up to EUR 450 towards a desk, a chair or both (POL-7.3.2). You need your line manager's approval before you buy, and itemised receipts must go through the expenses system within 60 calendar days of purchase (POL-7.3.2). Could you confirm your approved tier so we can check eligibility?

Citation: `POL-7.3.2`, `requires_manager_approval: true`. The correct clause was in the manual, in section 7, about 70k tokens after the task 4 instructions.

## Failure 2 — invented clause with the wrong rule (ticket HR-21177)

**Input**

```
ticket_id: HR-21177
employee_id: E-2208
first_name: Mei
manager: Stefan Ahlgren
message: I have 9 days of holiday left and the year ends in December. What happens to them? Do I lose them or get paid?
```

**Produced (task 4 body, abridged)**

> You will not lose them. Any unused annual leave at the end of the leave year is paid out with your January salary at your normal daily rate (POL-7.8.2). No action is needed on your side.

Citation in the JSON: `POL-7.8.2`. Section 7 has six subsections; there is no 7.8. The statement is also the opposite of the policy.

**Should have produced**

> You can carry over up to five days into next year, and those five days must be taken by 31 March or they are forfeited (POL-3.2.4). The remaining four days would be lost unless your Head of Department approves additional carry-over in writing before the end of the leave year (POL-3.2.4). Unused leave is not paid out except when you leave the company (POL-3.2.4). It would be worth speaking to your manager now about booking some of the days before December.

Citation: `POL-3.2.4`, `requires_manager_approval: true`.

## Failure 3 — schema ignored and invented clause (ticket HR-21203)

**Input**

```
ticket_id: HR-21203
employee_id: E-3390
first_name: Jonas
manager: Amara Diallo
message: I got back from the Hamburg trip six weeks ago and completely forgot to file my expenses (about EUR 740). Is it too late?
```

**Produced (task 5 output, verbatim)**

```
Here is the final JSON for ticket HR-21203:

Hi Jonas,

It is not too late. Claims can be submitted up to 60 days after the trip (POL-3.2.14), so you are still within the window. Please upload the receipts and your manager will approve as usual.

Kind regards, People Operations

Citations: POL-3.2.14
Confidence: high
```

No JSON object was produced; the task 5 block is prose with labels. `POL-3.2.14` does not exist (subsection 3.2 has six clauses) and is in the wrong section for expenses.

**Should have produced**

A valid JSON object per the schema, with body:

> You are past the standard window: claims must be submitted within 30 calendar days of returning from travel, and later claims are not reimbursed unless the Finance Director approves an exception in writing (POL-5.1.6). At six weeks you are still inside the 90-day limit for exceptions, so the route is for your line manager to request the exception stating the reason for the delay; Finance decides within ten working days (POL-5.1.6). Please upload the receipts now so the claim is ready if the exception is granted.

Citation: `POL-5.1.6`, `escalate_to: "finance"`, `requires_manager_approval: true`.

## What has been tried

- Added "Do not hallucinate", "Do not invent clause ids" and "This is extremely important" at the top of the prompt (v13 → v14). No measurable change: 4 of 11 October replies still cite non-existent clauses.
- Added rules 24 to 29 and the quality checklist. No change in invented citations; replies got slightly shorter.
