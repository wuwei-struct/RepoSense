File: report.json
schema_version: 1
generated_by: tool/reposense_version/ruleset_id/ruleset_fingerprint/schema_version
Top-level required: schema_version, generated_by, findings, run_summary
Key semantics:
- findings: list of detection objects
- run_summary: aggregate metrics including profile/ruleset/budget
Determinism: stable ordering of lists is not guaranteed; consumers must not rely on order
Example:
{
  "schema_version": 1,
  "engine_version": "0.1.0",
  "generated_by": {"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"specs_v2","ruleset_fingerprint":"abcd1234","schema_version":1},
  "findings": [],
  "run_summary": {"profile":"prod_lite","ruleset":"rulesets/specs_v2"}
}
