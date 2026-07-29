# TypeORM DB Operation Coverage

RepoSense performs conservative, static extraction of TypeORM database
operations. It does not install dependencies, execute repository code, or prove
transaction correctness or data consistency.

## Canonical receivers

The extractor requires TypeORM provenance before classifying a call:

- `Repository<T>`, `TreeRepository<T>`, and `MongoRepository<T>`
- `@InjectRepository(Entity)` constructor or property injection
- `EntityManager`
- `DataSource`, including `getRepository()` and transaction callbacks
- `QueryRunner`, including explicit transaction lifecycle calls
- query builders created from a confirmed TypeORM receiver
- entities that explicitly extend TypeORM `BaseEntity`

Receiver names alone are insufficient. Ordinary services, HTTP clients, Redis
clients, maps, arrays, and repository-shaped mocks are not treated as TypeORM
receivers without provenance evidence.

## Operation classification

Repository and manager reads include `find`, `findOne`, `findBy`, `count`,
`exists`, and related variants. Writes include `save`, `insert`, `update`,
`upsert`, `delete`, `remove`, soft-delete/restore operations, counters, and
other explicit write-intent methods.

QueryBuilder reads require a read terminal such as `getMany` or `getOne`.
QueryBuilder writes require both a write builder and `execute()`. A bare
`.update()` or `.delete()` is not emitted as a confirmed write.

Static raw SQL is classified by its leading SQL keyword. Dynamic or unresolved
SQL is emitted as `db.query_unknown` with
`dynamic_sql_operation_unresolved`; it is not guessed as a read or write.

## Transaction context

Operations inside a confirmed `DataSource.transaction()` or
`EntityManager.transaction()` callback are marked `explicit_callback`.
Operations inside a statically bounded QueryRunner transaction are marked
`query_runner_explicit`.

Unknown context does not prove that a write runs outside a transaction.
TypeScript TypeORM writes without explicit local transaction evidence remain
suspected and carry `typescript_transaction_coverage_unresolved`. RepoSense
also correlates trusted transaction decorators and uniquely resolved one-hop
wrapper calls. See
[`TYPESCRIPT_TRANSACTION_CORRELATION.md`](TYPESCRIPT_TRANSACTION_CORRELATION.md).
It does not construct a complete cross-file TypeScript transaction call graph.

## Artifacts

Each scan writes:

- `typeorm_db_operations.json`
- `typeorm_db_summary.json`

The real-repository validation harness additionally writes:

- `typeorm_db_validation.json`
- `typeorm_db_validation.md`
- `typeorm_db_triage_template.json`

Run Manifest records these files when present. Context Pack copies them into
`ARTIFACTS/` and exposes them through `MAP/index.json`.

## Validation

Use the pinned offline smoke harness:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 -CaseId nestjs-boilerplate -SkipClone -KeepWorkspace
```

The validator checks operation counts, receiver coverage, transaction context,
duplicate operations, and Evidence Location Contract compliance. Triage
templates remain `unreviewed` until a human checks source.

The 2026-07-18 pinned offline calibration observed:

- NestJS Boilerplate: 16 reads, 41 writes, and no explicit TypeORM transaction
  signal; all 41 write contexts remained unresolved.
- Queue/cache TypeScript case: 51 reads, 46 writes, 11 transaction signals,
  and 13 writes inside explicit callback context.
- Spring PetClinic regression: 68 Java DB operations and 46 explicit Spring
  transaction correlations, unchanged by the TypeORM implementation.

All three runs had zero evidence integrity errors and passed strict verify.
Detailed source sampling is recorded in
`docs/validation/REAL_REPO_REVIEW_RESULTS.md`.

## Limitations

- No complete TypeScript type system or cross-file data flow.
- No runtime QueryBuilder or dynamic SQL resolution.
- No TypeScript service-to-repository transaction proof.
- Mongo-specific persistence semantics are not expanded.
- A DB fact proves only that a static signal was observed, not that the code is
  correct, transactional, reachable, or safe at runtime.

## Cross-file provenance

TypeORM operations remain canonical and deduplicated by their existing
operation identity. `typeorm_alias_resolutions.json` adds project-local import,
constructor dependency, wrapper target, and caller evidence without creating a
second DB operation. See
[TYPEORM_CROSS_FILE_ALIAS_RESOLUTION.md](TYPEORM_CROSS_FILE_ALIAS_RESOLUTION.md).
