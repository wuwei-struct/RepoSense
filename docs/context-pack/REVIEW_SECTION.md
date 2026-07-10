# Context Pack REVIEW Section

The `context_pack/REVIEW/` directory is the review handoff layer for AI-assisted maintenance and human code review.

It packages existing evidence-backed outputs into one place so a reviewer or AI assistant can start from review context before editing code.

## Why It Exists

Context Pack is a facts-first handoff. The REVIEW section makes the review path explicit:

- Repository Review Report
- Backend Verifier Report
- Code Health Radar
- Permission Auditor
- AuthZ Matrix
- Human Review Required
- Suggested AI Maintenance Constraints

## Directory Structure

```text
context_pack/REVIEW/
  README.md
  repository_review_report.md
  review_risk_matrix.json
  human_review_required.md
  backend_verifier_report.md
  code_health_summary.json
  maintainability_risks.json
  permission_risk_report.md
  human_permission_review_required.md
  authz_matrix_report.md
  authz_matrix_diff.json
  authz_negative_test_plan.md
  ai_maintenance_constraints.md
```

Only files that exist in the run directory are copied. `REVIEW/README.md` lists available and missing review artifacts.

## Recommended AI Reading Order

1. `REVIEW/README.md`
2. `REVIEW/repository_review_report.md`
3. `REVIEW/human_review_required.md`
4. `REVIEW/backend_verifier_report.md`
5. `REVIEW/code_health_summary.json`
6. `REVIEW/permission_risk_report.md`
7. `REVIEW/authz_matrix_report.md`
8. `REVIEW/authz_negative_test_plan.md`
9. `REVIEW/ai_maintenance_constraints.md`

## AI Maintenance Constraints

`ai_maintenance_constraints.md` is a static OSS handoff document. It is not commercial prompt engineering.

It tells assistants to read review outputs first, avoid broad changes, confirm suspected findings with humans, preserve evidence outputs, and re-run RepoSense after changes.

## Relationship To Review Features

- Repository Review provides the overall decision and human review queue.
- Code Health Radar provides maintainability risks.
- Permission Auditor provides permission facts and risks.
- AuthZ Matrix provides optional contract diff.
- Backend Verifier provides transaction and side-effect signals.

## Complete Review Demo

Generate a stable demo run with REVIEW artifacts using:

```powershell
powershell -ExecutionPolicy Bypass -File tools/review_demo.ps1
```

The canonical output is `.reposense_review_demo/current/`, and the Context Pack REVIEW section is available at:

`.reposense_review_demo/current/context_pack/REVIEW/README.md`

## Limitations

- REVIEW is not a correctness proof.
- REVIEW does not replace human code review.
- Suspected findings require human confirmation.
- AI assistants should not make broad changes without reading `human_review_required.md`.
