# Spring Transaction Correlation

RepoSense can conservatively correlate explicit Spring transaction scopes with direct Java Repository, DAO, `EntityManager`, and supported database write calls. The result reduces same-file-only transaction false positives without claiming complete transaction correctness.

## Supported scope

The MVP observes:

- method-level and class-level `@Transactional` annotations;
- fully qualified and parameterized annotation forms;
- constructor-injected and field-injected Repository/DAO receivers, including final fields commonly used with Lombok;
- direct calls to the existing Java DB-write taxonomy, including `save`, `delete`, `persist`, `merge`, `remove`, `insert`, `update`, and related explicit write operations;
- Repository implementation methods whose DB writes can be linked to direct Service receiver calls.

The analysis is static. It reads source and existing run artifacts but does not execute repository code.

## Coverage statuses

- `covered_explicit`: every resolved direct caller observed in the scan is inside an explicit non-read-only transaction.
- `uncovered`: resolved direct callers have no observed method-level or class-level transaction annotation.
- `partially_covered`: resolved callers have mixed transaction states or incomplete coverage.
- `read_only_transaction`: a write call appears inside `@Transactional(readOnly = true)` and is not treated as safe write coverage.
- `unknown`: no reliable direct callsite or target mapping was observed.

Only `covered_explicit` can suppress a confirmed `db_write_outside_tx`, and only when all resolved direct calls for that DB write are covered. Partial, read-only, or unknown coverage remains a suspected review item. An uncovered call remains a risk and points to the non-transactional callsite as well as the DB write.

## Artifacts

- `transaction_correlations.json`: stable per-DB-write correlations with transaction annotation, callsite, and DB-write evidence.
- `transaction_correlation_summary.json`: counts for covered, uncovered, partial, read-only, and unknown correlations.

Both artifacts use repository-relative paths and the [Evidence Location Contract](EVIDENCE_LOCATION_CONTRACT.md). Unknown locations are omitted rather than rewritten to line 1.

When present, the artifacts are included in Run Manifest, Context Pack `ARTIFACTS/` and `MAP/index.json`, and the Repository Review Transaction Review summary.

## Limitations

This is not a complete Java call graph or transaction proof. It does not model:

- Spring proxy activation or self-invocation behavior;
- dynamic dispatch, reflection, or custom AOP transaction annotations;
- Spring Data default transaction semantics;
- controller-to-service-to-repository multi-hop proof;
- transaction propagation across modules, services, or languages.

A covered direct call means explicit transaction evidence was observed for the scanned callsites. It does not prove every runtime entrypoint is transactional or that rollback behavior is correct.
