File: exports/report.sarif.json
schema_version: N/A (SARIF 2.1.0 standard)
Reposense contract additions:
- runs[0].properties.reposense.gate_status: "pass"|"warn"|"fail"
- results[].fingerprints["reposense/v1"]: stable fingerprint
- results[].locations[].physicalLocation.artifactLocation.uri: relative path
Determinism: SARIF ordering follows tool output; consumers must not rely on order changes
Example snippet:
{"version":"2.1.0","runs":[{"properties":{"reposense.gate_status":"pass"},"results":[{"fingerprints":{"reposense/v1":"abcd1234"}}]}]}
