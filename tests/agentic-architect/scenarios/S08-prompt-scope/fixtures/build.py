#!/usr/bin/env python3
"""Build the S01 fixtures into a project directory.

Usage: python3 -I fixtures/build.py <project-dir>

Writes, under <project-dir>/artifacts/:
  policy-corpus.md                 the ~90k-token synthetic Northwind policy manual
  pipeline-system-prompt.full.md   the production prompt with the corpus pasted in
  failures.md                      copied from fixtures/artifacts/

Deterministic; standard library only.
"""
import os
import random
import sys

SECTIONS = [
    (1, "Introduction, scope and definitions"),
    (2, "Working hours and attendance"),
    (3, "Leave and absence"),
    (4, "Remuneration and payroll"),
    (5, "Expenses and travel"),
    (6, "Equipment and acceptable use of IT"),
    (7, "Remote and hybrid working"),
    (8, "Health, safety and wellbeing"),
    (9, "Conduct, grievance and disciplinary procedure"),
    (10, "Data protection and confidentiality"),
    (11, "Learning and development"),
]
SUBSECTIONS = {
    1: ["Purpose", "Who this manual applies to", "Definitions", "Precedence and local annexes", "Review cycle", "Contractors and agency workers"],
    2: ["Standard hours", "Flexible start and finish", "Overtime", "Breaks", "Time recording", "Lateness and unauthorised absence"],
    3: ["Annual leave entitlement", "Carry-over and forfeiture", "Sickness absence", "Public holidays and part-time staff", "Parental and family leave", "Unpaid and special leave"],
    4: ["Pay dates and cut-offs", "Salary reviews", "Corrections and back-pay", "Advances and loans", "Deductions", "Bank details and payslips"],
    5: ["Claim windows and receipts", "Travel booking", "Per diems and subsistence", "Mileage", "Entertainment and gifts", "Late and exceptional claims"],
    6: ["Standard issue equipment", "Replacement cycle", "Loss, theft and damage", "Personal use", "Software and licences", "Return on leaving"],
    7: ["Hybrid tiers", "Eligibility and approval", "Home office allowance", "Working from another country", "Availability and core hours", "Ergonomics and assessment"],
    8: ["Reporting incidents", "First aid", "Display screen equipment", "Mental health support", "Lone working", "Workplace adjustments"],
    9: ["Expected standards", "Informal resolution", "Formal grievance", "Disciplinary procedure", "Right to be accompanied", "Appeals"],
    10: ["Classification of information", "Handling personal data", "Devices and encryption", "Breach reporting", "Confidentiality after leaving", "Subject access requests"],
    11: ["Training budget", "Approval of courses", "Professional memberships", "Study leave", "Conferences", "Mentoring"],
}
CLAUSES_PER_SUBSECTION = 6

ACTORS = ["the employee", "the line manager", "People Operations", "Payroll", "the Finance Director", "the HR Business Partner", "the IT service desk", "the Head of Department"]
VERBS = ["must", "may", "is required to", "is expected to", "should", "is entitled to"]
OBJECTS = [
    "submit the request through the People Portal", "obtain written approval in advance", "retain supporting documentation",
    "notify their line manager on the first working day", "record the hours in the time system", "complete the relevant form",
    "confirm eligibility against the criteria in this section", "escalate the matter to the next level of approval",
    "provide a copy to People Operations", "review the arrangement at the next one-to-one",
]
CONDITIONS = [
    "where the period exceeds {n} consecutive working days", "where the amount exceeds {cur} {amt}", "within {n} working days of the event",
    "unless a local annex states otherwise", "where the employee has completed {n} months of continuous service", "no later than {n} calendar days before the intended date",
    "where the arrangement is expected to last more than {n} weeks", "except in the circumstances described in clause POL-{ref}",
]
CONSEQUENCES = [
    "Requests that do not meet this condition will be returned without decision.", "Failure to comply may be treated as a conduct matter under section 9.",
    "The decision will be confirmed in writing within {n} working days.", "Exceptions require the approval of {actor} and are recorded on the employee's file.",
    "Any amount paid in error will be recovered in accordance with clause POL-4.3.{c}.", "The employee will be informed of the outcome and of their right to appeal.",
    "This does not affect the employee's statutory rights.", "Records are retained for the period set out in clause POL-10.2.{c}.",
]

OVERRIDES = {
    "POL-7.3.2": (
        "Home office allowance",
        "An employee approved for hybrid working at Tier 2 or Tier 3 may claim a one-time home office allowance of up to EUR 450 "
        "towards a desk, a chair or both. The claim must be submitted through the expenses system with itemised receipts within 60 calendar days "
        "of the purchase and within six months of the hybrid approval date. The allowance is not available to employees at Tier 1 and is not "
        "renewable on a change of address. Line manager approval is required before purchase. Items purchased with the allowance remain the "
        "employee's property.",
    ),
    "POL-3.2.4": (
        "Carry-over of unused annual leave",
        "An employee may carry over up to five days of unused annual leave into the following leave year. Carried-over days must be taken by "
        "31 March of that year and are forfeited if untaken, except where the employee was prevented from taking leave by sickness absence or "
        "family leave, in which case clause POL-3.2.5 applies. Carry-over above five days requires written approval from the Head of Department "
        "before the end of the leave year. Unused annual leave is not paid out except on termination of employment.",
    ),
    "POL-5.1.6": (
        "Late claims",
        "Expense claims must be submitted within 30 calendar days of the date of return from travel or, for non-travel expenses, of the date of "
        "purchase. Claims submitted after 30 days will not be reimbursed unless the Finance Director approves an exception in writing. "
        "Exception requests are made by the line manager, must state the reason for the delay, and are decided within ten working days. "
        "Claims older than 90 days are not eligible for exception.",
    ),
}


def clause_text(sec, sub, c):
    cid = f"POL-{sec}.{sub}.{c}"
    if cid in OVERRIDES:
        title, body = OVERRIDES[cid]
        return cid, title, body
    rng = random.Random(sec * 10007 + sub * 101 + c)
    title = f"{SUBSECTIONS[sec][sub - 1]}: provision {c}"
    sentences = []
    for _ in range(5):
        actor = rng.choice(ACTORS)
        verb = rng.choice(VERBS)
        obj = rng.choice(OBJECTS)
        cond = rng.choice(CONDITIONS).format(
            n=rng.choice([3, 5, 7, 10, 14, 21, 30, 60]), cur="EUR", amt=rng.choice([50, 100, 250, 500, 1000]),
            ref=f"{sec}.{rng.randint(1, 6)}.{rng.randint(1, CLAUSES_PER_SUBSECTION)}",
        )
        sentences.append(f"{actor[0].upper() + actor[1:]} {verb} {obj} {cond}.")
    for _ in range(2):
        sentences.append(rng.choice(CONSEQUENCES).format(
            n=rng.choice([5, 10, 15]), actor=rng.choice(ACTORS), c=rng.randint(1, CLAUSES_PER_SUBSECTION)))
    sentences.append(
        f"For the purposes of this clause, '{rng.choice(['working day', 'continuous service', 'the event', 'the arrangement'])}' has the meaning given in clause POL-1.3.{rng.randint(1, CLAUSES_PER_SUBSECTION)}."
    )
    return cid, title, " ".join(sentences)


def build_corpus():
    out = ["# Northwind Group Employee Policy Manual", "", "Edition 2026.3, effective 1 October 2026. Regenerated monthly from the policy repository.", ""]
    for sec, heading in SECTIONS:
        out.append(f"## Section {sec} — {heading}")
        out.append("")
        for sub in range(1, len(SUBSECTIONS[sec]) + 1):
            out.append(f"### {sec}.{sub} {SUBSECTIONS[sec][sub - 1]}")
            out.append("")
            for c in range(1, CLAUSES_PER_SUBSECTION + 1):
                cid, title, body = clause_text(sec, sub, c)
                out.append(f"**{cid} {title}.** {body}")
                out.append("")
    return "\n".join(out)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: build.py <project-dir>")
    project = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    art = os.path.join(project, "artifacts")
    os.makedirs(art, exist_ok=True)
    corpus = build_corpus()
    with open(os.path.join(art, "policy-corpus.md"), "w") as f:
        f.write(corpus)
    with open(os.path.join(here, "artifacts", "pipeline-system-prompt.md")) as f:
        prompt = f.read()
    with open(os.path.join(art, "pipeline-system-prompt.full.md"), "w") as f:
        f.write(prompt.replace("{{POLICY_CORPUS}}", corpus))
    with open(os.path.join(here, "artifacts", "failures.md")) as f:
        failures = f.read()
    with open(os.path.join(art, "failures.md"), "w") as f:
        f.write(failures)
    print(f"corpus: {len(corpus)} bytes, ~{len(corpus) // 4} tokens; wrote {art}")


if __name__ == "__main__":
    main()
