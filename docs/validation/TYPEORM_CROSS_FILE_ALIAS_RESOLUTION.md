# TypeORM Cross-file Alias Resolution

RepoSense builds a conservative TypeScript import and symbol graph to connect
project-local wrapper calls with canonical TypeORM database operations. The
resolver improves provenance; it is not a TypeScript type checker or a runtime
dependency-injection model.

## Supported resolution

- repository-relative named, aliased, default, and namespace imports;
- named re-exports and star exports through at most three edges;
- `.ts`, `.tsx`, and `index.ts` module resolution;
- class, interface, constructor dependency, property, and method indexes;
- NestJS constructor fields and simple same-method local assignments;
- one-hop calls from a service receiver to a uniquely resolved wrapper method;
- `provide` / `useClass` only when the provider target is unique.

The resolver emits:

- `typescript_import_graph.json`;
- `typescript_symbol_index.json`;
- `typeorm_alias_resolutions.json`;
- `typeorm_alias_resolution_summary.json`;
- real-repository validation JSON, Markdown, and an unreviewed triage template.

Each accepted resolution preserves import, dependency, callsite, target method,
and canonical DB-operation evidence. IDs, paths, and sorting are stable.

## Resolution states

- `resolved_direct_import`
- `resolved_alias_import`
- `resolved_reexport`
- `resolved_barrel`
- `resolved_local_assignment`
- `ambiguous`
- `unresolved`

Ambiguous providers, interface multi-implementations, dynamic DI tokens,
external packages, cycles, depth overflow, and unresolved tsconfig aliases are
not guessed. They retain explicit limitations such as
`target_method_ambiguous`, `dynamic_di_token_unresolved`, or
`cross_file_resolution_depth_exceeded`.

## Transaction use

TypeScript transaction correlation consumes resolutions by exact
`db_operation_id`. A resolved caller with a trusted explicit transaction can
produce `covered_explicit`; a resolved caller without one produces
`uncovered`; mixed callers produce `partially_covered`. Unresolved and
ambiguous targets remain `unknown`.

Only the specific covered DB event is removed from
`db_write_outside_tx` consideration. Other writes in the same file remain
actionable suspected signals. Canonical TypeORM operations are not regenerated
or duplicated.

## Pinned offline calibration

The 2026-07-29 rerun used existing pinned workspaces and did not execute
third-party code.

| Metric | NestJS Boilerplate | ecommerce-store-api |
|---|---:|---:|
| TypeORM writes | 41 | 46 |
| Alias candidates | 22 | 135 |
| Resolved wrapper calls | 11 | 14 |
| Ambiguous / unresolved candidates | 11 / 0 | 0 / 121 |
| Covered before / after | 0 / 0 | 13 / 13 |
| Uncovered before / after | 3 / 10 | 0 / 12 |
| Unknown before / after | 38 / 31 | 33 / 21 |
| Outside-tx Patterns before / after | 7 / 7 | 8 / 8 |
| Alias evidence valid / errors | 88 / 0 | 577 / 0 |
| Strict verify | pass | pass |

NestJS has no trusted explicit TypeORM transaction caller at the pinned commit,
so no coverage was invented. Files, Session, and Users wrapper calls became
traceable non-transactional callers; document/relational multi-implementation
paths remained ambiguous. In ecommerce-store-api, permission, role, and
session wrapper calls became traceable non-transactional callers while the
existing 13 callback-covered writes remained unchanged.

Spring PetClinic remained at 68 Java DB operations and 46
`covered_explicit` Java correlations. It produced no TypeScript alias
candidates, and strict evidence validation passed.

## Boundaries

- No complete TypeScript compiler API or type system.
- No tsconfig, webpack, monorepo, or runtime package alias inference.
- No dynamic DI container, reflection, factory provider, or multi-hop graph.
- No target repository execution.
- A resolved target does not prove reachability, transaction propagation,
  rollback behavior, data consistency, or correctness.
