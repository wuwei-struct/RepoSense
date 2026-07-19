# Review Context Calibration

RepoSense uses deterministic context annotations to reduce review noise without deleting the underlying facts. The annotations affect review priority; they do not prove that a route is safe or that a file is unimportant.

## Outputs

A calibrated run can include:

- `route_intent_annotations.json`
- `file_context_annotations.json`
- `review_context_summary.json`

The artifacts use stable IDs, repository-relative paths, and evidence-backed source locations. Run Manifest and Context Pack `ARTIFACTS/` include them when generated.

## Public authentication entrypoints

`public_auth_entrypoint` is reserved for high-confidence authentication entrypoints such as login, registration, password-reset requests, email-verification requests, and OAuth/OIDC callbacks. Classification combines the route path, controller or file context, handler source window, and authentication-related signals.

High-confidence public authentication entrypoints do not produce primary AUTHZ-001 or AUTHZ-002 missing-auth findings. Their route and side-effect facts remain available, and AUTHZ-005 can emit low-priority negative-test suggestions for invalid credentials, disabled accounts, malformed requests, and invalid reset or verification tokens.

The classification does not mean that an endpoint is safe. It only records that an authentication guard is not normally expected at that entrypoint.

## Protected authentication operations

Logout, token revocation, password or email changes, profile updates, session management, and account deletion remain protected operations. Admin, permission, role, refund, billing, tenant, and workspace mutations are never downgraded merely because they appear in an authentication module.

If public-entrypoint signals conflict with sensitive business actions, the intent remains `unknown`, the permission risk remains suspected, and the annotation records `route_intent_conflict`.

## File context

File annotations use these contexts:

- `production`
- `generated`
- `seed`
- `template`
- `fixture`
- `test`
- `migration`
- `unknown`

Generated classification requires an explicit generated header or a recognized generated path. Seed, template, fixture, test, and migration contexts use conservative path and file-name signals. A repository name containing `boilerplate` or `template` does not classify every file as a template.

## Raw and actionable findings

Code Health keeps raw findings in `code_health.json`. Context metadata records:

- `file_context`
- `context_confidence`
- `review_modifier`
- `context_reason`

For high-confidence generated files, CHD-001, CHD-002, CHD-003, and CHD-005 leave primary review; CHD-004 is only downweighted. For seed, template, fixture, and test files, CHD-005 remains a low, suspected raw finding but is excluded from `maintainability_risks.json` and Human Review Required. Swallowed-error signals are downweighted rather than automatically excluded.

Production and unresolved files keep normal review priority.

Repository Review reports raw and actionable counts separately. Human Review Required consumes only actionable permission and maintainability risks, while the underlying artifacts remain traceable.

## Boundaries

- Route intent is heuristic classification, not an authority contract.
- A public authentication annotation does not override `reposense.authz.yaml`.
- Missing evidence does not prove that a guard or test is absent.
- Non-production classification changes review priority, not source facts.
- The calibration does not replace security review or code review.
- RepoSense does not execute target repository code during classification.

## Route Guard Correlation

Route Intent and Guard Correlation are separate evidence layers. Route Intent classifies likely purpose; Guard Correlation records observed NestJS method, Controller, and global Guard coverage plus explicit public bypasses.

OpenAPI security is retained as contract or documentation evidence only. It cannot independently suppress a missing-auth finding. A route is treated as code-protected only when method, Controller, or global Guard source evidence exists. Sensitive routes with only an auth Guard remain eligible for role or permission review.

See [OPENAPI_GLOBAL_GUARD_CORRELATION.md](OPENAPI_GLOBAL_GUARD_CORRELATION.md) for effective Guard priority, OpenAPI match states, public bypass handling, and limitations.

## Route Guard Correlation

Route Intent and Guard Correlation are separate evidence layers. Route Intent classifies likely purpose; Guard Correlation records observed NestJS method, Controller, and global Guard coverage plus explicit public bypasses.

OpenAPI security is retained as contract or documentation evidence only. It cannot independently suppress a missing-auth finding. A route is treated as code-protected only when method, Controller, or global Guard source evidence exists. Sensitive routes with only an auth Guard remain eligible for role or permission review.

See [OPENAPI_GLOBAL_GUARD_CORRELATION.md](OPENAPI_GLOBAL_GUARD_CORRELATION.md) for effective Guard priority, OpenAPI match states, public bypass handling, and limitations.
