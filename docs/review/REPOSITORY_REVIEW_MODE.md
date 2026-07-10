# Repository Review Mode

Repository Review Mode is RepoSense's evidence-guided repository review layer.

It aggregates existing run artifacts into a repository-level review report:

- Backend Verifier Report
- Patterns and Pattern Summary
- AI Risks
- Code Health Radar artifacts, when generated
- Permission Auditor artifacts, when generated
- AuthZ Matrix diff artifacts, when generated
- Quality Gate
- Event Graph
- API Surface
- Coverage
- Run Manifest

It does not rescan source code, execute repository code, or perform unrestricted source browsing.

## Relationship to Backend Verifier

Backend Verifier focuses on backend transaction, queue, cache, database, API surface, and side-effect signals.

Repository Review Mode uses that evidence as one input and combines it with patterns, risks, quality gate status, and API/event summaries to produce:

- `repository_review_report.json`
- `repository_review_report.md`
- `review_risk_matrix.json`
- `human_review_required.md`

## Human Review Required

`human_review_required.md` is the main review handoff artifact.

Each item is derived from an existing pattern or risk with evidence references. It records:

- why a human should review the path or artifact,
- the suggested reviewer role,
- the decisions the reviewer should make,
- the evidence references that triggered the item.

This file is not a proof of correctness. It is a focused review queue.

## Current Scope

This first release aggregates existing artifacts only.

Code Health Review is MVP optional in this release. It is enabled when `code_health.json`, `code_health_summary.json`, and `maintainability_risks.json` exist in the run directory.

See [CODE_HEALTH_RADAR.md](CODE_HEALTH_RADAR.md).

Permission Review is MVP optional in this release. It is enabled when `permission_surface.json` and `permission_risks.json` exist in the run directory.

See [PERMISSION_AUDITOR.md](PERMISSION_AUDITOR.md).

AuthZ Matrix is optional and contract-based. When `authz_matrix_diff.json` exists, Permission Review includes matrix mode and missing expected signal counts.

See [AUTHZ_MATRIX.md](AUTHZ_MATRIX.md).

## Boundaries

- Repository Review Mode does not replace human code review.
- It does not guarantee backend safety.
- It does not prove all transactions are correct.
- It does not execute repository code.
- It does not let AI freely roam the full source tree by default.

## CLI

```powershell
.\.venv\Scripts\python.exe -m reposense review report <run_dir> --json --markdown
```

The command writes the four review artifacts into `<run_dir>` and updates `run_manifest.json`.

## Complete Review Demo

Use the review demo script to generate a stable, screenshot-ready run that includes Backend Verifier, Code Health Radar, Permission Auditor, AuthZ Matrix, Repository Review, and Context Pack REVIEW artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File tools/review_demo.ps1
```

The canonical demo output is:

`.reposense_review_demo/current/`

This demo is built from `tests/fixtures/repos/review_demo_full/`. It is a static fixture for review demonstration and does not execute repository code.

## Demo and screenshots

Review screenshots are tracked in `docs/assets/ASSET_INDEX.md`.

Screenshots should be captured from the canonical review demo only:

`.reposense_review_demo/current/`

Recommended screenshot targets include `repository-review-report.png`, `human-review-required.png`, and `studio-review-panel.png`.
