File: api_surface.json
schema_version: 1
generated_by: required
Top-level required: schema_version, generated_by, endpoints, stats, mismatches
Key semantics:
- endpoints: normalized API endpoints with source mapping
- stats: aggregate counts
- mismatches: spec/code comparison
Determinism: endpoints sorted by normalized_key/source path/start_line
Example:
{"schema_version":1,"generated_by":{"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"specs_v2","ruleset_fingerprint":"abcd1234","schema_version":1},"endpoints":[],"stats":{},"mismatches":{}}
