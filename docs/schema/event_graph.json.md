File: event_graph.json
schema_version: 1
generated_by: required
Top-level required: schema_version, generated_by, nodes, edges
Key semantics:
- nodes: event nodes with evidence references
- edges: relationships between nodes
Determinism: nodes/edges sorted by id for stability
Example:
{
  "schema_version": 1,
  "generated_by": {"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"specs_v2","ruleset_fingerprint":"abcd1234","schema_version":1},
  "nodes": [],
  "edges": []
}
