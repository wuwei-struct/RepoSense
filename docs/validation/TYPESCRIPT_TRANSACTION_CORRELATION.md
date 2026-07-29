# TypeScript / TypeORM Transaction Correlation

RepoSense correlates canonical TypeORM writes with explicit, statically
reviewable TypeScript transaction evidence. The result reduces
`db_write_outside_tx` noise without claiming that every runtime path is
transactional.

## Supported explicit coverage

The correlation pass recognizes:

- `DataSource.transaction(...)` callbacks, including callback manager aliases;
- `EntityManager.transaction(...)` callbacks;
- QueryRunner writes located between `startTransaction()` and
  `commitTransaction()` or `rollbackTransaction()`;
- method-level and class-level `Transactional` decorators imported from
  `typeorm-transactional` or `typeorm-transactional-cls-hooked`;
- legacy TypeORM transaction decorators only when import provenance is
  explicit;
- one-hop calls from a transaction-decorated method to a uniquely resolved
  local wrapper method containing a canonical TypeORM write.

The correlation stores transaction, callsite, and DB-write evidence using
repository-relative paths and the Evidence Location Contract.

## Coverage states

- `covered_explicit`: explicit local transaction evidence covers the write.
- `uncovered`: a direct, statically resolved call has no explicit transaction.
- `partially_covered`: the same target has both transactional and
  non-transactional callers, or mixed resolvability.
- `read_only_transaction`: a write is observed in an explicitly read-only
  transaction and is not treated as safe coverage.
- `unknown`: transaction provenance, caller target, migration policy, or scope
  cannot be resolved conservatively.

Only `covered_explicit` suppresses `db_write_outside_tx`. Other states remain
suspected review signals. An untrusted same-name decorator is not transaction
proof and records `transaction_decorator_provenance_unresolved`.

## Migration handling

Migration DDL and DML remain canonical DB-write facts. Without an explicit
QueryRunner transaction scope, their transaction policy remains `unknown` with
`migration_transaction_policy_requires_confirmation`. RepoSense neither marks
all migrations covered nor declares them outside a transaction.

## Artifacts

TypeScript correlations share the existing artifacts with Java/Spring:

- `transaction_correlations.json`
- `transaction_correlation_summary.json`

The summary includes `by_language_framework`, with separate `java/spring` and
`typescript/typeorm` sections. Real-repository smoke additionally writes:

- `typescript_transaction_validation.json`
- `typescript_transaction_validation.md`
- `typescript_transaction_triage_template.json`

Run Manifest and Context Pack include available artifacts.

## Limitations

This analysis does not implement a complete TypeScript type system, runtime DI
resolution, reflection, multi-hop call graph, or transaction propagation
model. It does not execute decorators or repository code. A
`covered_explicit` result proves only that explicit static evidence was
observed for the correlated write; it does not prove rollback behavior,
isolation, reachability, or transaction correctness.

## Cross-file wrapper enhancement

Transaction correlation now prefers `typeorm_alias_resolutions.json` when it
is available. Calls are joined to canonical writes by exact `db_operation_id`,
with import, constructor dependency, callsite, target method, and DB-write
evidence. Direct, aliased, default, re-exported, barrel, and simple local
assignment receivers are supported conservatively.

Resolved non-transactional callers become `uncovered`, mixed callers become
`partially_covered`, and only trusted explicit transaction callers may become
`covered_explicit`. Ambiguous providers and dynamic DI remain `unknown`. See
[TYPEORM_CROSS_FILE_ALIAS_RESOLUTION.md](TYPEORM_CROSS_FILE_ALIAS_RESOLUTION.md).
