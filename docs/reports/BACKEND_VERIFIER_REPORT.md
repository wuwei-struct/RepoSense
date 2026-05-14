# Backend Verifier Report

RepoSense `backend_verifier_report` is an evidence-backed, conservative backend transaction and side-effect report generated from existing run artifacts.

## Inputs

- `report.json`
- `event_graph.json`
- `api_surface.json`
- `entrypoints.json` (optional)
- `coverage.json`
- `quality_gate.json`
- `patterns.json` (optional)
- `run_manifest.json` (optional)

## Outputs

- `<run_dir>/backend_verifier_report.json`
- `<run_dir>/backend_verifier_report.md`

## Fixed Sections

1. API Surface Summary
2. Backend Events Summary
3. Transaction Signals
4. Queue Dispatch Signals
5. Cache Operation Signals
6. Side-effect Map
7. High-risk Findings
8. Evidence Index
9. Limitations

## Boundary

- Conservative detection based on existing artifacts.
- Not a proof of full backend correctness.
- Not a guarantee that all transactions are correct.
- Side-effect map is an approximate, evidence-backed aggregation, not a full call-chain proof.

