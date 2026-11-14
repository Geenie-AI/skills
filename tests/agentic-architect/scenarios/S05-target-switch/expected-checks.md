This scenario is graded by diffing the produced `architecture.md` against the S02 run's `architecture.md`. The runner supplies the unified diff in the artifact listing under `diff-vs-S02.md`; without it, checks 1 and 2 fail.

1. The diff between this run's architecture document and the S02 document touches only the header line (target) and the artifacts emitted section; sections 1 to 11 and 13 to 15 are identical. [doc § 0, doc § 12]
2. The diagnosis table and the lever plan are identical to the S02 run's. [SC1, doc § 5, doc § 8]
3. For the Claude Agent SDK target, the artifacts emitted section lists subagent definitions instead of Agents SDK agents. [E8, doc § 12]
4. For the Claude Agent SDK target, retrieval is emitted as a tool or MCP server the answering step calls, not as a `file_search` vector store. [R5.2, doc § 12]
5. For the Claude Agent SDK target, the artifacts emitted section records fine-tuning as "not available on this target" as an emit gap, while the lever plan and rejected options are unchanged from S02. [E6, doc § 12]
6. For the generic target rerun, the artifacts emitted include a declarative step graph with typed edges and a JSON schema per boundary. [R9.4, doc § 12]
7. For the generic target rerun, the diagnosis table and sections 1 to 11 are again identical to the S02 run's. [doc § 5]
8. Every emitted artifact in both reruns begins with a header naming the diagnosis rows it serves. [E1]
