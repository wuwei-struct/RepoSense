File: run_manifest.json
schema_version: 1
generated_by: required
Top-level required: schema_version, meta, artifacts
Key semantics:
- meta: run_dir/profile/ruleset_id/ruleset_fingerprint/content_id/pack_id
- artifacts: list of artifacts with path/kind/schema_version/bytes/sha256/generated_by(optional)
Determinism: artifacts sorted by kind then path
Example:
{"schema_version":1,"meta":{},"artifacts":[],"generated_by":{"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"specs_v2","ruleset_fingerprint":"abcd1234","schema_version":1}}
