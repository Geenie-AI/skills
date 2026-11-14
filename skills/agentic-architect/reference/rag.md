# Retrieval design and the failure grid

Read this when the diagnosis has a **context** row whose source is too large or too volatile for static inclusion (Q7), and before proposing any retrieval component. Guide section: *RAG*.

Retrieval: embed the corpus, embed the question, fetch the most relevant content, pass it to the model. The guide notes that many large deployments used only prompt engineering plus retrieval.

## Failure grid

Place every retrieval-related failure row on this grid before choosing a fix:

| Where | Symptom | Fix |
|---|---|---|
| **Retrieval** | Wrong chunks: the model cannot answer | Tune search: chunking, hybrid search, metadata filters, reranking, more context per hit |
| **Retrieval** | Too many irrelevant chunks: the real information is buried, the model hallucinates | Reduce noise: lower k, rerank, filter, deduplicate; raise the relevance threshold |
| **LLM** | Right chunks present but misused | Prompt engineering on how to use context (quote-then-answer, cite chunk ids, abstain when unsupported); if examples help, the fine-tune gates |

## Rules

- **R5.1 Measure before you build.** Specify how the retrieval axis will be measured before specifying the retriever. Q8 says whether sample questions can be traced to the document that answers them; if not, the first eval milestone creates that trace for ≥ 20 items.
- **R5.2 Retrieve into the step that needs it** (R4.3), never into a global preamble. Retrieval is a tool or component attached to one step; other steps are shielded from the corpus.
- **R5.3 Retrieval can lower accuracy on a learned task.** The guide's Icelandic case lost 4 BLEU (87 → 83) when retrieved examples were added to a fine-tuned model. Propose retrieval only against a context-axis row and schedule an eval to confirm it helps.
- **R5.4 Citation requirement (Q7) → grounded generation.** The prompt asks for claims with chunk or clause references, and the verify step (R4.6) checks each reference against the fetched text.

## Retrieval spec (doc § 7.4 and `retrieval.md`)

Fill every line; write `verify:` with a doc URL for any vendor parameter you cannot confirm.

| Item | Content |
|---|---|
| Corpus | Source (Q6/Q8), size (measured or `estimated:`), change frequency (Q7), owner (Q23) |
| Chunking | Unit (clause, section, record), size and overlap in tokens, why that unit matches how questions are asked |
| Index | Where it lives (Q20 constraints), refresh schedule tied to the change frequency |
| Query strategy | What the step sends: the user question, a rewritten query, or a classification from an upstream step used as a filter |
| k and filters | Starting k (small, usually 3–8), metadata filters (policy area, date, product), relevance threshold |
| Citation ids | The stable id each chunk carries back to the prompt and the verify step |
| Measurement | Retrieval-axis eval: right chunk in top-k for each of ≥ 20 traced items; answer-axis eval separate |
| Upkeep | Who refreshes the index when the source changes (Q23) |

When Q8 shows the knowledge sits in a database or API with a known query shape, prefer a tool (R9.1) and say why retrieval was not chosen.
