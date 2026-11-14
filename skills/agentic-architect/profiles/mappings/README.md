# Profile mappings for external sources

A mapping tells the skill how a record returned by an external tool or MCP server answers intake questions. One file per source, named `<source>.yaml`. The skill reaches the source only through a tool the user has configured; with no such tool the mapping is ignored and file-based profiles apply.

```yaml
source: crm                      # label used in provenance: external:crm.<field>
tool: mcp__crm__get_account      # the tool or MCP tool name the host exposes; verify it exists before calling
lookup:
  argument: account_id           # the tool argument that receives the profile ID
fields:
  Q6:  { field: kb_summary,   transform: "list of knowledge sources" }
  Q7:  { field: kb_stats,     transform: "pages, change frequency, citation required" }
  Q15: { field: ticket_volume, transform: "requests per day" }
  Q16: { field: integrations, transform: "systems the solution may read or act on" }
staleness_days: 30
```

`transform` is a plain-language instruction for turning the field into the question's answer. Fields not listed are never read. Answers from a mapping carry `source: external:<source>.<field>` and the record's timestamp if it has one, otherwise the run date.

See `example.yaml` for a complete file.
