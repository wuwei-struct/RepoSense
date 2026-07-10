# Permission Auditor

Permission Auditor is RepoSense's deterministic permission-fact and permission-risk layer for AI-assisted projects.

It is not a security audit, not an authorization correctness proof, and not a replacement for human review. It extracts evidence-backed permission signals and highlights routes that need review.

## Why It Matters

AI-generated and vibe-coded backends often add routes quickly. The harder question is whether write routes, admin routes, and sensitive routes have observable auth, role, permission, ownership, and negative-test evidence.

Permission Auditor helps answer:

- Which APIs or routes look write-like?
- Which write routes lack observed auth guard evidence?
- Which sensitive/admin routes lack observed role or permission guard evidence?
- Are permission checks only visible in frontend code?
- Which permission-sensitive routes lack negative test evidence?

## MVP Rules

- AUTHZ-001 Public write endpoint: write-like API route without observed auth guard evidence.
- AUTHZ-002 Route missing auth guard: sensitive route without observed auth guard evidence.
- AUTHZ-003 Sensitive admin route missing role guard: auth evidence exists, but role/permission guard evidence is not observed.
- AUTHZ-004 Frontend-only permission check: frontend permission signal exists while related backend guard evidence is not observed.
- AUTHZ-005 Permission negative test gap: no negative permission test evidence observed for a permission-sensitive route.

## Outputs

Permission Auditor writes these run-level artifacts:

- `permission_surface.json`
- `permission_risks.json`
- `permission_risk_report.md`
- `human_permission_review_required.md`
- `authz_negative_test_plan.md`

## How To Run

```powershell
.\.venv\Scripts\python.exe -m reposense authz scan <run_dir> --repo <repo_path> --json --markdown
```

If run artifacts record a readable repository path, `--repo` can be omitted. Passing `--repo` is recommended for portable runs.

## Repository Review Integration

Repository Review Mode consumes permission artifacts when they exist:

- `permission_review.status` becomes `enabled`.
- `repository_review_report.md` includes Permission Review.
- `human_review_required.md` includes medium/high permission review items.

If permission artifacts do not exist, RepoSense does not invent permission results.

## AuthZ Matrix

Permission Auditor can be extended by an optional `reposense.authz.yaml` contract.

See [AUTHZ_MATRIX.md](AUTHZ_MATRIX.md) for expected vs actual permission diff, inferred matrix behavior, and negative authorization test plan generation.

## Context Pack Integration

When present before Context Pack generation, Permission Auditor artifacts are copied into `context_pack/ARTIFACTS/` and listed in `MAP/index.json`.

## Limitations

- Conservative static matching only.
- No complete AuthZ Matrix in this MVP.
- No cross-service authorization proof.
- No service bypass detection.
- No tenant SQL/dataflow proof.
- Negative test gaps are inferred from file names and keywords only.
- Frontend-only permission risks are suspected unless route correspondence is explicit.

## Future AuthZ Matrix Direction

Future work can add an optional AuthZ Matrix that maps route, actor, role, permission, ownership, tenant boundary, negative tests, and evidence references into a more complete authorization review contract.
