# OpenAPI and Global Guard Correlation

RepoSense correlates NestJS code routes, method and Controller guards, global guards, explicit public bypass decorators, and OpenAPI operations. The result calibrates Permission Auditor findings without treating documentation as implementation proof.

## Outputs

A Permission Auditor run can generate:

- `route_guard_correlations.json`
- `route_guard_summary.json`
- `openapi_security_surface.json`

Run Manifest records these artifacts as `route_guard_correlation`. Context Pack copies them into `ARTIFACTS/` and adds MAP entries when they exist.

## Effective Guard Priority

Effective authentication state is resolved in this order:

1. Method-level explicit public bypass.
2. Method-level `@UseGuards(...)`.
3. Controller-level explicit public bypass.
4. Controller-level `@UseGuards(...)`.
5. Global `app.useGlobalGuards(...)` or `APP_GUARD`.
6. No observed code Guard.
7. Unknown when the evidence cannot support a correlation.

The MVP recognizes common auth, role, permission, and policy Guard names. It preserves source evidence for each declaration. A global Guard is associated conservatively without building a complete Nest module graph, so the correlation records that application-boundary limitation.

An intentional public bypass means that a route appears deliberately exempted from an observed broader Guard policy. It does not mean that the route is safe.

## Public Bypass

The extractor recognizes `@Public()`, `@AllowAnonymous()`, and `@SkipAuth()`. Confidence is higher when the decorator resolves to `SetMetadata(...)` and a Guard reads the same metadata key. An unresolved public decorator remains evidence with lower confidence and the `public_decorator_definition_unresolved` limitation.

Permission Auditor suppresses a primary missing-auth item for a public bypass only when Route Intent also classifies the route as a high-confidence `public_auth_entrypoint`. Sensitive or conflicting routes remain reviewable.

## OpenAPI Correlation

RepoSense reuses the existing normalized path and template matcher:

- identical method and route: `exact_match`
- equivalent templates such as `:id` and `{id}`: `template_match`
- implementation without a matched operation: `code_only`
- operation without a matched implementation route: `openapi_only`
- multiple plausible operations: `ambiguous`

The OpenAPI surface records global security, operation-level security, explicit `security: []`, and scheme names.

**OpenAPI security is contract or documentation evidence, not implementation Guard proof.**

Therefore:

- OpenAPI security alone never suppresses AUTHZ-001 or AUTHZ-002.
- OpenAPI-protected routes without code Guard evidence retain permission review and the `openapi_security_without_code_guard` limitation.
- `security: []` supports an intentional-public interpretation only when code and Route Intent evidence also support it.
- OpenAPI-only and ambiguous routes require human confirmation.

## Permission and AuthZ Consumption

Code-side `protected_method`, `protected_controller`, and `protected_global` states can suppress missing-auth findings. They do not suppress AUTHZ-003 when a sensitive route has no observed role or permission Guard.

Frontend-only permission review consumes the effective role state. A backend role or permission Guard removes the frontend-only signal; an auth-only Guard does not prove role enforcement.

AuthZ Matrix keeps `reposense.authz.yaml` as the authority contract. Guard correlation only enriches observed facts and inferred-only output. Inferred matrices continue to require human confirmation.

Repository Review reports effective Guard counts, intentional public bypasses, OpenAPI-protected routes without code Guard evidence, OpenAPI-only routes, and unresolved correlations. It does not add a new Review Decision rule.

## Canonical Code Routes

NestJS Guard Correlation consumes the shared route decorator classifier rather than independently matching HTTP verb prefixes. Only exact route decorators applied to Controller methods become code routes. Persistence properties such as `@DeleteDateColumn()` are classified as non-routes and cannot become `code_only` Guard correlations. See [ROUTE_DECORATOR_CLASSIFICATION.md](ROUTE_DECORATOR_CLASSIFICATION.md).

## Limitations

- The MVP focuses on NestJS and does not implement Spring `SecurityFilterChain` inference.
- It does not build a complete Nest module dependency graph.
- It does not execute custom Guards or prove runtime Guard behavior.
- It does not implement a full TypeScript type system.
- It does not prove role, permission, ownership, or tenant correctness.
- `code_only`, `openapi_only`, and `ambiguous` describe correlation coverage, not implementation correctness.
- Results do not replace security review or human code review.
