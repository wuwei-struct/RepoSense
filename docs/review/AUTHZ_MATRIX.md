# AuthZ Matrix

AuthZ Matrix adds an optional permission contract to Permission Auditor.

It combines:

- actual permission facts from `permission_surface.json`,
- an optional expected contract from `reposense.authz.yaml`,
- evidence-backed diff output,
- a suggested negative authorization test plan.

AuthZ Matrix does not prove permissions are correct and does not replace security review.

## Contract File

RepoSense looks for an optional file at repository root:

```yaml
routes:
  POST /api/orders/:id/refund:
    resource: order
    action: refund
    expected:
      auth: required
      permissions:
        - order:refund
      ownership_check: required
      tenant_boundary: required
      transaction: required
      audit_log: required
```

Supported MVP expected fields:

- `auth`
- `roles`
- `permissions`
- `ownership_check`
- `tenant_boundary`
- `transaction`
- `audit_log`

Missing fields are treated as `unknown`. Unrecognized fields are preserved where possible but are not enforced in the MVP.

## Modes

### Inferred Only

Without `reposense.authz.yaml`, RepoSense generates `authz_matrix_inferred.yaml` only.

The inferred matrix includes `inferred: true`, confidence, evidence references, and `needs_confirmation: true`. It is not an authority contract.

### Contract Diff

With `reposense.authz.yaml`, RepoSense also writes:

- `authz_matrix_loaded.json`
- `authz_matrix_diff.json`
- `authz_matrix_report.md`

Diffs use the wording “expected signal not observed” and do not claim a proven vulnerability.

## CLI

```powershell
.\.venv\Scripts\python.exe -m reposense authz matrix <run_dir> --repo <repo_path> --contract <repo_path>\reposense.authz.yaml --json --markdown
```

## Outputs

- `authz_matrix_loaded.json`
- `authz_matrix_inferred.yaml`
- `authz_matrix_diff.json`
- `authz_matrix_report.md`
- `authz_negative_test_plan.md`

## Relationship To Repository Review And Context Pack

Repository Review consumes `authz_matrix_diff.json` when it exists and adds matrix summary counts to Permission Review.

Context Pack copies AuthZ Matrix artifacts into `context_pack/ARTIFACTS/` and lists them in `MAP/index.json`.

## Limitations

- No full cross-service permission proof.
- No tenant dataflow proof.
- No service layer bypass detection.
- No permission-check-after-side-effect rule in this MVP.
- No AI repair suggestions.
- No code execution.

## Roadmap

- Tenant dataflow.
- Service bypass checks.
- Policy layer extraction.
- Matrix confirmation workflow.

