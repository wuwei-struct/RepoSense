File: quality_gate.json
schema_version: 1
generated_by: required
Top-level required: schema_version (via generated_by.schema_version), status, metrics, violations
Key semantics:
- status: pass/warn/fail
- metrics: gate metrics snapshot
- baseline_used/baseline_compatible/regressions: present when baseline mode
Example:
{"status":"pass","metrics":{},"violations":[],"generated_by":{"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"specs_v2","ruleset_fingerprint":"abcd1234","schema_version":1}}
