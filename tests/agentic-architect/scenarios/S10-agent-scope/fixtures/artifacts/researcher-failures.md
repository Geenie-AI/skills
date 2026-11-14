# Researcher failures (five from the last fortnight)

## F1 — unsupported claim
Request: "What share of the German e-bike market did the top three brands hold in 2025?"
Researcher returned (free text): "The top three brands held roughly 55% of the market in 2025, led by Cube at 22%." No source for either figure. Drafter cited "researcher findings"; reviewer passed it. The 22% figure cannot be found anywhere.
Wanted: each figure with a source URL, or "no reliable 2025 share data found" and the nearest sourced figure (2024 industry association report).

## F2 — wrong output shape
Request: "Summarise regulatory changes affecting cross-border parcel delivery in the EU since 2024."
Researcher returned a Markdown document with headings and a conclusion paragraph, not the findings list the drafter expects; the drafter treated the conclusion as a finding and cited it as a source.
Wanted: a list of findings, each with claim, source, date, and an established/contested/unknown label.

## F3 — ignored the notes repository
Request: "Do we have anything on the Nordic heat-pump subsidy schemes?"
Researcher went straight to web search and returned four web sources; the notes repository has an internal 2026 memo on exactly this (notes/energy/nordic-heat-pump-subsidies-2026.md) with primary citations.
Wanted: the memo first, web only to update it.

## F4 — unsupported claim presented as established
Request: "Is Carrefour planning to exit the Polish market?"
Researcher returned "Carrefour is expected to exit Poland in 2027" citing a single opinion column. Drafter put it in the headline.
Wanted: labelled contested or unknown; the column named as opinion.

## F5 — wrong output shape, again
Request: "Compare the three largest Spanish solar installers by 2025 revenue."
Researcher returned a table in prose with revenue figures and a line "sources available on request".
Wanted: a findings list with one source per figure.

Context at the researcher step is small: its instructions (about 60 tokens) plus the request and tool results, under 8k tokens. The information was available (F3: in the notes; F1, F4, F5: in public sources it did not cite).
