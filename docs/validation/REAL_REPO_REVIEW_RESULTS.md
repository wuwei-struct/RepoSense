# Real Open-Source Repository Review Results

The pinned external repository smoke was executed on 2026-07-16. Target repository code was not installed, built, tested, or executed.

The protocol and reproduction commands are documented in [REAL_REPO_REVIEW_SMOKE.md](REAL_REPO_REVIEW_SMOKE.md). Generated triage templates remain `unreviewed`; the source observations below are a limited calibration sample, not a complete human audit.

## Pinned cases

| Case | Commit | License | Working-tree size | Pipeline |
|---|---|---|---:|---|
| [brocoders/nestjs-boilerplate](https://github.com/brocoders/nestjs-boilerplate) | `549cc37a3925ab87a4e61b45efb3b86d2d8e234e` | MIT | 1.21 MB | complete |
| [spring-petclinic/spring-petclinic-rest](https://github.com/spring-petclinic/spring-petclinic-rest) | `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd` | Apache-2.0 | 0.69 MB | complete |

Both repositories were checked out at the exact configured commit. The size column excludes `.git` objects.

## Artifact completeness

Both cases generated all 15 required smoke artifacts, including Backend Verifier, Patterns, Code Health, Permission Auditor, inferred-only AuthZ Matrix, Repository Review, Context Pack `REVIEW/`, and Run Manifest outputs.

Strict RepoSense verification passed for both runs. Quality Gate completed for both runs.

## Detection summary

| Metric | NestJS Boilerplate | Spring PetClinic REST |
|---|---:|---:|
| scanned files | 471 | 151 |
| API endpoints | 6 | 38 |
| DB operations | 0 | 68 |
| transaction signals | 0 | 58 |
| queue dispatch / consume | 0 / 0 | 0 / 0 |
| cache operations | 0 | 0 |
| Patterns | 1 | 12 |
| Code Health findings | 4 | 19 |
| Permission risks | 40 | 44 |
| AuthZ inferred routes | 23 | 42 |
| Review Decision | WARN | WARN |
| Human Review Required | 24 | 48 |
| confirmed / suspected | 16 / 29 | 36 / 39 |

The smoke did not observe queue or cache events in either selected repository. These cases therefore validate route, DB, transaction, auth, test, and review paths more strongly than queue/cache coverage.

## Evidence integrity

### NestJS Boilerplate

- 178 evidence records checked.
- No out-of-repository absolute path was observed.
- No invalid source line or unresolved evidence ID was observed.
- Evidence integrity result: pass.

### Spring PetClinic REST

- 506 evidence records checked.
- No out-of-repository absolute path was observed.
- 22 invalid line references were reported because 11 `db_write_outside_tx` pattern evidence entries use line `0`, and those references are repeated in Human Review Required.
- Evidence integrity result: fail.

The line-zero failures remain visible by design. They are not treated as successful evidence and are a prerequisite calibration item for the next iteration.

## Limited source sampling

The following samples were inspected against the pinned source without copying source blocks into this document:

| Case | Signal | Triage observation |
|---|---|---|
| NestJS | CHD-001 on `src/auth/auth.service.ts` | `plausible`: the file is 508 lines, so the maintainability signal is grounded, though severity remains heuristic. |
| NestJS | CHD-005 on a `.hygen` seed template | `likely_false_positive`: generator templates should be excluded or strongly down-weighted. |
| NestJS | AUTHZ-001 on Apple/Facebook/Google login routes | `likely_false_positive`: login endpoints are intentionally public authentication entry points. |
| NestJS | unmatched root API endpoint | `needs_business_context`: a backend-only repository does not necessarily require a matching in-repository caller. |
| Spring | `db_write_outside_tx` on repository implementations | `likely_false_positive`: write methods are called through a service layer with observed `@Transactional` methods, but the current pattern does not correlate that cross-file boundary. |
| Spring | AUTHZ-001 on OpenAPI write routes | `needs_business_context`: OpenAPI rows do not carry method-level `@PreAuthorize` or conditional global Spring Security evidence. |
| Spring | CHD-001 on large test classes | `likely_false_positive` for release prioritization: test fixtures should remain visible but more strongly down-weighted. |

Sample distribution: 1 `plausible`, 4 `likely_false_positive`, and 2 `needs_business_context`. This is a small calibration sample, not a statistical precision estimate.

## Observed calibration gaps

No rules were changed in this PR. The smoke identified these follow-up candidates:

1. NestJS API extraction observed fewer routes than Permission Auditor source extraction and did not observe TypeORM DB operations in this repository.
2. Public authentication entry points need route-intent handling before AUTHZ-001 can be treated as high-confidence risk.
3. Generated/template/tooling paths such as `.hygen` need stronger Code Health exclusions or weighting.
4. Transaction patterns need cross-file service-to-repository correlation before repository writes are labeled confirmed outside a transaction.
5. Pattern evidence must not emit line `0` when it is promoted into review artifacts.
6. OpenAPI-derived permission risks need correlation with controller guards and global/conditional security configuration.
7. Cross-language unmatched endpoint patterns need a backend-only repository boundary.
8. A future real-repository case should explicitly cover queue or cache signals.

## Execution notes

- NestJS case duration recorded by the harness: 9,787 ms.
- Spring case duration recorded by the harness: 8,716 ms.
- Spring coverage reported 37 unsupported Java JPA/MyBatis signals and one additional parse warning; NestJS reported one parse warning.
- AuthZ Matrix mode was `inferred_only` for both cases, with human confirmation required.
- Canonical local output: `.reposense_real_repo_smoke/current/`.

## Evidence Integrity Calibration

The original Spring smoke found 11 `db_write_outside_tx` Pattern references with `line_start=0`. Repository Review propagated those references into Human Review, producing 22 integrity errors in the original independent smoke audit.

Root cause analysis showed that the Event Graph node already referenced canonical `E*` evidence with a real source line, while Pattern event normalization read only `meta.start_line`. Spring DB nodes stored their source range in canonical evidence and `meta.scope`, so the missing direct field was converted to `0`.

The fix now resolves Pattern locations from canonical Event evidence first, preserves repository-relative source paths, and uses scope locations only as a valid fallback. Unknown locations are omitted rather than rewritten to line 1, and affected conclusions remain suspected with `source_location_unavailable` recorded.

Strict verification now validates structured evidence locations across Pattern, Risk, Code Health, Permission, AuthZ, and Repository Review artifacts. Repository Review filters invalid references and deduplicates Human Review items using source identity, normalized location, and required decisions.

The pinned Spring workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`. The rerun checked 506 evidence records with 0 integrity errors, and strict verification completed successfully. All 11 `db_write_outside_tx` references now use observed positive source lines; no duplicate Human Review stable keys were found.

Evidence integrity therefore changed from 22 propagated location errors in the original smoke to 0 after regeneration. No transaction-correlation or rule-severity semantics were changed by this calibration.

## Boundaries

- Target repository code was not executed.
- No authority contract was invented for either repository.
- Results do not prove repository safety, permission correctness, or transaction correctness.
- Third-party source and generated smoke outputs remain ignored and are not committed.
- Large third-party source excerpts are not copied into this document.

## Spring Cross-layer Transaction Calibration

The pinned Spring PetClinic REST workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`. Target code was not executed or modified.

The correlation pass links explicit Service transaction annotations and direct Repository calls to implementation-level DB writes. It does not use Spring Data default transaction semantics.

| Metric | Before correlation | After correlation |
|---|---:|---:|
| DB operations | 68 | 68 |
| transaction signals | 58 | 58 |
| transaction correlations | not available | 46 |
| covered / uncovered / partial / read-only / unknown | not available | 46 / 0 / 0 / 0 / 0 |
| `db_write_outside_tx` patterns | 11 | 0 |
| total patterns | 12 | 1 |
| Human Review Required | 48 | 37 |
| evidence integrity errors | 0 after PR-REAL-02A | 0 |
| strict verification | pass | pass |
| Review Decision | WARN | WARN |

The remaining Pattern is unrelated to transaction correlation. Pattern count reduction is not treated as a correctness metric; the relevant result is that every suppressed DB write has an explicit annotation, direct callsite, and DB-write evidence chain.

### Covered source samples

| Repository operation | Transaction evidence | Direct callsite | DB-write evidence | Observation |
|---|---|---|---|---|
| `OwnerRepository.save` | `ClinicServiceImpl.java:233` | `ClinicServiceImpl.java:235` | `JpaOwnerRepositoryImpl.java:95` | Explicit method transaction covers the resolved direct save call. |
| `UserRepository.save` | `UserServiceImpl.java:17` | `UserServiceImpl.java:34` | `JpaUserRepositoryImpl.java:22` | Explicit method transaction covers the resolved direct save call. |
| `VisitRepository.save` | `ClinicServiceImpl.java:220` | `ClinicServiceImpl.java:222` | `JpaVisitRepositoryImpl.java:53` | Explicit method transaction covers the resolved direct save call. |

All paths above are repository-relative in generated artifacts. The samples record source coordinates only and do not copy third-party source blocks.

### Retained-risk calibration

The final pinned Spring run produced no `uncovered`, `partially_covered`, `read_only_transaction`, or `unknown` correlations, so three real retained-risk samples do not exist in this repository revision. RepoSense does not fabricate retained findings to satisfy a sample quota.

The synthetic fixture preserves and tests the conservative behavior:

- `UncoveredService.java:11`: an unannotated direct `save` call remains a confirmed outside-transaction risk and points to the callsite.
- `MixedService.java:14` and `MixedService.java:18`: transactional and non-transactional callers produce `partially_covered` and a suspected Pattern.
- `JpaUnknownRepository.java:9`: a DB write without a resolved direct caller remains `unknown` and suspected without a fabricated caller location.

### Remaining limitations

- Correlation covers direct Java calls and explicit Spring `@Transactional` only.
- It does not prove Spring proxy activation, self-invocation behavior, transaction propagation, or runtime dispatch.
- It does not infer Spring Data default transaction behavior.
- One covered direct caller does not prove that an unobserved runtime caller cannot exist.

## Queue and Cache Real Repository Coverage

PR-REAL-03 added two pinned cases and a dedicated Queue/Cache validator. Both cases were acquired once with explicit network access and rerun from fixed local workspaces. No target repository install, build, test, service, or package script was executed.

| Case | License | Commit |
|---|---|---|
| `raouf-b-dev/ecommerce-store-api` | MIT | `147231b54ed8f8a7f3a0b5110db757a39650892c` |
| `ali-bouali/apache-kafka-with-spring-boot-reactive` | Apache-2.0 | `46492f9147673513338505049eff09bc796dd166` |

### TypeScript BullMQ and Redis

- scanned files: 739
- queue dispatch / consume: 3 / 3
- resolved queues: `checkout`, `notifications`, `payment-events`
- matched producer-consumer pairs: 2
- unmatched dispatch / consumer: 0 / 1
- cache read / write / invalidate: 1 / 43 / 1
- duplicate queue/cache events: 0
- Queue/Cache evidence: 51 checked, 51 valid, 0 errors
- complete run evidence: 2942 checked, 2942 valid, 0 errors
- strict verification: pass
- Review Decision: WARN

Source review confirmed three dispatch calls, three `@Processor`/`WorkerHost` consumers, and sampled Redis read/write/invalidate calls. The `checkout` observation is consumer-only in the static scan; this does not prove the producer is absent at runtime.

Initial calibration exposed a metric call, `redisStatus.set(...)`, that was incorrectly classified as cache write solely because the receiver name contained `redis`. Receiver classification now requires a resolved Redis instance or an explicit Redis/cache client, service, connection, or store wrapper. The false event disappeared while sampled Redis wrapper operations remained.

### Java Spring Kafka

- scanned files: 40
- queue dispatch / consume: 3 / 2
- resolved topics: `alibou`, `wikimedia-stream`
- matched producer-consumer pairs: 2
- unresolved topic events: 1
- duplicate queue events: 0
- Queue evidence: 5 checked, 5 valid, 0 errors
- complete run evidence: 73 checked, 73 valid, 0 errors
- strict verification: pass
- Review Decision: WARN

Source review confirmed two literal-topic `KafkaTemplate.send` calls and two `@KafkaListener` consumers. The third dispatch uses `KafkaTemplate.send(message)`; source constructs the message with a Kafka topic header, but resolving that value requires cross-statement flow. The event therefore remains `unknown_name`, and its `queue_without_consumer` Pattern remains suspected rather than confirmed.

### Old-case regression

- NestJS Boilerplate: 0 queue/cache events, 895/895 evidence records valid, strict pass, Review Decision WARN.
- Spring PetClinic REST: 0 queue/cache events, 46 `covered_explicit` transaction correlations retained, 904/904 evidence records valid, strict pass, Review Decision WARN.

No queue/cache events were fabricated in repositories where the corresponding facts were not observed. Full methodology and boundaries are documented in [QUEUE_CACHE_REAL_REPO_COVERAGE.md](QUEUE_CACHE_REAL_REPO_COVERAGE.md).

## NestJS Route Decorator Classification Calibration

The pinned NestJS Boilerplate workspace was rerun offline at commit `549cc37a3925ab87a4e61b45efb3b86d2d8e234e`. Target code was not installed, built, tested, executed, or modified.

The original false routes were created by Permission Auditor's independent decorator expression. The expression accepted an HTTP verb prefix without requiring an exact decorator symbol or method syntax context, so `@DeleteDateColumn()` was truncated to `Delete`. The TypeScript detector and Guard extractor used different expressions, which allowed downstream route inventories to disagree.

The shared classifier now supplies canonical NestJS route facts to the TypeScript detector, Permission Auditor, and Guard Correlation.

| Metric | Guard-correlated run before classification | Route-classified run |
|---|---:|---:|
| correlated code routes | 24 | 24 |
| decorator candidates | not available | 349 |
| accepted route decorators | not available | 24 |
| rejected non-route decorators | not available | 316 |
| rejected `DeleteDateColumn` | not available | 2 |
| unknown decorator candidates | not available | 0 |
| Permission risks | 15 | 9 |
| actionable Permission risks | 6 | 0 |
| Human Review Required | 7 | 8 |
| Review Decision | WARN | WARN |
| evidence integrity | 455 / 455, pass | 895 / 895, pass |
| strict verification | pass | pass |

Risk-count reduction is not the correctness criterion. The decisive evidence is the syntax context:

- `src/session/infrastructure/persistence/relational/entities/session.entity.ts:37` is `@DeleteDateColumn()` on the `deletedAt` entity property.
- `src/users/infrastructure/persistence/relational/entities/user.entity.ts:72` is `@DeleteDateColumn()` on the `deletedAt` entity property.

Both are recorded as `property` / `non_route` in `route_decorator_classifications.json`. Neither appears in Permission Surface, Permission risks, inferred AuthZ Matrix routes, Guard Correlation, or Human Review Required.

Real routes remained classified as methods:

- `src/auth/auth.controller.ts:146`: exact `@Delete('me')`
- `src/auth/auth.controller.ts:91`: exact `@Get('me')`
- `src/auth-apple/auth-apple.controller.ts:32`: exact `@Post('login')`

The nine remaining Permission items are low, suspected public-auth negative-test suggestions with `suggested_human_review=false`; there are no remaining high/medium actionable Permission items in this pinned run. The eight Human Review items are Code Health adjacent-test signals, not propagated decorator routes.

### Spring regression after route classification

The pinned Spring PetClinic REST workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`.

- DB operations: 68.
- transaction signals: 58.
- transaction correlations: 46, all `covered_explicit`.
- Patterns: 1.
- Human Review Required: 37.
- evidence integrity: 904 / 904 records valid, 0 errors.
- strict verification: pass.
- Review Decision: WARN.

The TypeScript decorator summary is empty for this Java-only case. Evidence Location and Spring transaction correlation did not regress.

### Classification limitations

- The classifier is conservative lexical analysis, not a complete TypeScript AST.
- Aliased, computed, or dynamically constructed decorators may remain unresolved.
- Exact route classification does not prove runtime route registration, Guard correctness, or permission correctness.
- OpenAPI-only operations remain separate contract/documentation facts.

## Public Auth Entrypoint Calibration

The pinned NestJS Boilerplate workspace was rerun offline at commit `549cc37a3925ab87a4e61b45efb3b86d2d8e234e`. Target code was not installed, built, tested, executed, or modified.

| Metric | Original smoke | Context-calibrated rerun |
|---|---:|---:|
| Permission risks | 40 | 31 |
| actionable permission risks | not available | 22 |
| public authentication entrypoints | not available | 9 |
| protected authentication operations | not available | 4 |
| Code Health findings | 4 | 4 |
| actionable maintainability risks | not available | 2 |
| Human Review Required | 24 | 19 |
| Review Decision | WARN | WARN |
| evidence integrity | pass | 400 / 400 records, pass |
| strict verification | pass | pass |

The nine public entrypoints include email login and registration, email confirmation, forgot/reset password, and Apple/Facebook/Google login handlers. They retain low-priority negative-test suggestions but no longer create primary missing-auth review items.

### Public-route source samples

| Route evidence | Classification | Review effect |
|---|---|---|
| `src/auth-apple/auth-apple.controller.ts:32` | high-confidence public login | AUTHZ-001/002 suppressed; low AUTHZ-005 suggestion retained outside Human Review |
| `src/auth-facebook/auth-facebook.controller.ts:32` | high-confidence public login | AUTHZ-001/002 suppressed; low AUTHZ-005 suggestion retained outside Human Review |
| `src/auth-google/auth-google.controller.ts:32` | high-confidence public login | AUTHZ-001/002 suppressed; low AUTHZ-005 suggestion retained outside Human Review |

These classifications record expected public intent; they do not prove abuse protection, credential validation, or authentication correctness.

### Retained permission samples

| Route evidence | Retained result | Reason |
|---|---|---|
| `src/users/users.controller.ts:56` | medium/high AUTHZ-001/002 | ordinary user write operation is not a public authentication entrypoint |
| `src/users/users.controller.ts:115` | high AUTHZ-001/002 | user update remains a protected business operation |
| `src/users/users.controller.ts:129` | high AUTHZ-001/002 | user deletion remains a protected business operation |

Permission source extraction still interprets some non-route decorators such as persistence `@DeleteDateColumn` as route-like facts. That pre-existing extraction noise is not hidden by this calibration and remains a candidate for a separate API/route extraction PR.

## Non-production File Calibration

The NestJS rerun classified 13 seed files, 3 template files, and 1 fixture file. No file met the strict generated-file signals in this pinned revision.

The only Code Health item excluded from primary review was CHD-005 at `.hygen/seeds/create-document/run-seed-service.ejs.t:1`. The raw finding remains in `code_health.json` with `file_context=seed`, `severity=low`, `status=suspected`, and `review_modifier=exclude_from_primary_review`; it is absent from `maintainability_risks.json` and Human Review Required.

Production observations remained visible:

- `src/home/home.controller.ts:1` retains a medium, suspected CHD-005 test-evidence gap.
- `src/main.ts:1` retains a medium, suspected CHD-005 test-evidence gap.
- `src/auth/auth.service.ts:1` retains the raw large-file observation with production context.

The calibrated summary therefore distinguishes four raw Code Health findings from two actionable maintainability risks. Lower priority does not mean that seed, template, or generated code is correct or harmless.

## Context Calibration Regression

The pinned Spring PetClinic REST workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`.

- DB operations: 68.
- transaction signals: 58.
- transaction correlations: 46, all `covered_explicit`.
- `db_write_outside_tx` patterns: 0; total Patterns: 1.
- Human Review Required: 37.
- evidence integrity: 829 / 829 records valid, 0 errors.
- strict verification: pass.
- Review Decision: WARN.

The context pass downweighted two test-file findings but did not change transaction correlation or Evidence Location semantics.

## OpenAPI and Global Guard Correlation Calibration

The deterministic synthetic fixture covers NestJS method, Controller, and global Guards, resolved public metadata bypasses, OpenAPI global and operation security, explicit `security: []`, exact/template matching, OpenAPI-only operations, and ambiguous matches.

The calibration preserves these boundaries:

- only code-side Guard evidence suppresses missing-auth findings;
- OpenAPI security remains contract/documentation evidence;
- auth-only protection does not suppress missing role or permission review;
- intentional public bypass requires supporting Route Intent before it leaves primary missing-auth review;
- OpenAPI-only and ambiguous routes require human confirmation.

Synthetic regression is implemented and passing. Offline NestJS and Spring smoke rerun results are recorded below only after the pinned workspaces are actually executed; no result is inferred from the fixture.

### NestJS pinned rerun

The pinned NestJS Boilerplate workspace was rerun offline at commit `549cc37a3925ab87a4e61b45efb3b86d2d8e234e`. Target code was not installed, built, tested, executed, or modified.

| Metric | Context-calibrated run | Guard-correlated run |
|---|---:|---:|
| Permission risks | 31 | 15 |
| actionable permission risks | 22 | 6 |
| Human Review Required | 19 | 7 |
| code routes correlated | not available | 24 |
| method / Controller / global Guard declarations | not available | 8 / 2 / 0 |
| protected method / Controller / global routes | not available | 8 / 5 / 0 |
| intentional public bypasses | not available | 0 |
| OpenAPI routes | not available | 0 |
| Review Decision | WARN | WARN |
| evidence integrity | pass | 455 / 455 records, pass |
| strict verification | pass | pass |

Risk-count reduction is not treated as a correctness metric. The relevant evidence is that routes now carry code-side Guard scope and declaration references.

Protected source samples:

- `DELETE /auth/me` at `src/auth/auth.controller.ts:146` is linked to a method Guard at line 147.
- `DELETE /users/{id}` at `src/users/users.controller.ts:129` is linked to Controller auth and role Guards at line 41.
- `POST /files/upload` at `src/files/infrastructure/uploader/local/files.controller.ts:37` is linked to its method Guard at line 36.

Public authentication samples remain Route Intent classifications rather than Guard bypasses in this commit:

- `POST email/login` at `src/auth/auth.controller.ts:39`
- `POST login` at `src/auth-apple/auth-apple.controller.ts:32`
- `POST email/register` at `src/auth/auth.controller.ts:48`

This pinned revision contains no detected OpenAPI document, no global Guard declaration, and no resolved `@Public()`-style bypass. RepoSense therefore reports zero real exact/template/OpenAPI-only matches and zero intentional public bypasses for this case. Those branches are covered by the synthetic fixture; no real sample is fabricated.

All six remaining actionable Permission items derive from two persistence entity decorators parsed as route-like `DELETE` facts:

- `src/session/infrastructure/persistence/relational/entities/session.entity.ts:37`
- `src/users/infrastructure/persistence/relational/entities/user.entity.ts:72`

They comprise AUTHZ-001/002 findings and their AUTHZ-005 test-gap projections. Manual source review classifies these as route-decorator extraction noise, not retained sensitive route evidence. Correcting non-route decorator classification is explicitly deferred to PR-REAL-02E.

### Spring regression

The pinned Spring PetClinic REST workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`.

- DB operations: 68.
- transaction signals: 58.
- transaction correlations: 46, all `covered_explicit`.
- Patterns: 1.
- Human Review Required: 37.
- evidence integrity: 904 / 904 records valid, 0 errors.
- strict verification: pass.
- Review Decision: WARN.

This PR does not implement Spring `SecurityFilterChain` inference. The 37 OpenAPI operations are therefore recorded as `openapi_only` with unknown effective auth status rather than being treated as implementation proof. Evidence Location and Spring transaction correlation remain intact.

## OpenAPI and Global Guard Correlation Calibration

The deterministic synthetic fixture covers NestJS method, Controller, and global Guards, resolved public metadata bypasses, OpenAPI global and operation security, explicit `security: []`, exact/template matching, OpenAPI-only operations, and ambiguous matches.

The calibration preserves these boundaries:

- only code-side Guard evidence suppresses missing-auth findings;
- OpenAPI security remains contract/documentation evidence;
- auth-only protection does not suppress missing role or permission review;
- intentional public bypass requires supporting Route Intent before it leaves primary missing-auth review;
- OpenAPI-only and ambiguous routes require human confirmation.

Synthetic regression is implemented and passing. Offline NestJS and Spring smoke rerun results are recorded below only after the pinned workspaces are actually executed; no result is inferred from the fixture.

### Calibration limitations

- Route intent remains deterministic heuristic classification and does not override an AuthZ contract.
- Public authentication endpoints still require project-specific abuse, credential, token, and account-state review.
- File context is path/header based and does not establish runtime importance.
- Raw findings remain the traceable source; actionable counts are review-priority projections.

## Spring Cross-layer Transaction Calibration

The pinned Spring PetClinic REST workspace was rerun offline at commit `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd`. Target code was not executed or modified.

The correlation pass links explicit Service transaction annotations and direct Repository calls to implementation-level DB writes. It does not use Spring Data default transaction semantics.

| Metric | Before correlation | After correlation |
|---|---:|---:|
| DB operations | 68 | 68 |
| transaction signals | 58 | 58 |
| transaction correlations | not available | 46 |
| covered / uncovered / partial / read-only / unknown | not available | 46 / 0 / 0 / 0 / 0 |
| `db_write_outside_tx` patterns | 11 | 0 |
| total patterns | 12 | 1 |
| Human Review Required | 48 | 37 |
| evidence integrity errors | 0 after PR-REAL-02A | 0 |
| strict verification | pass | pass |
| Review Decision | WARN | WARN |

The remaining Pattern is unrelated to transaction correlation. Pattern count reduction is not treated as a correctness metric; the relevant result is that every suppressed DB write has an explicit annotation, direct callsite, and DB-write evidence chain.

### Covered source samples

| Repository operation | Transaction evidence | Direct callsite | DB-write evidence | Observation |
|---|---|---|---|---|
| `OwnerRepository.save` | `ClinicServiceImpl.java:233` | `ClinicServiceImpl.java:235` | `JpaOwnerRepositoryImpl.java:95` | Explicit method transaction covers the resolved direct save call. |
| `UserRepository.save` | `UserServiceImpl.java:17` | `UserServiceImpl.java:34` | `JpaUserRepositoryImpl.java:22` | Explicit method transaction covers the resolved direct save call. |
| `VisitRepository.save` | `ClinicServiceImpl.java:220` | `ClinicServiceImpl.java:222` | `JpaVisitRepositoryImpl.java:53` | Explicit method transaction covers the resolved direct save call. |

All paths above are repository-relative in generated artifacts. The samples record source coordinates only and do not copy third-party source blocks.

### Retained-risk calibration

The final pinned Spring run produced no `uncovered`, `partially_covered`, `read_only_transaction`, or `unknown` correlations, so three real retained-risk samples do not exist in this repository revision. RepoSense does not fabricate retained findings to satisfy a sample quota.

The synthetic fixture preserves and tests the conservative behavior:

- `UncoveredService.java:11`: an unannotated direct `save` call remains a confirmed outside-transaction risk and points to the callsite.
- `MixedService.java:14` and `MixedService.java:18`: transactional and non-transactional callers produce `partially_covered` and a suspected Pattern.
- `JpaUnknownRepository.java:9`: a DB write without a resolved direct caller remains `unknown` and suspected without a fabricated caller location.

### Remaining limitations

- Correlation covers direct Java calls and explicit Spring `@Transactional` only.
- It does not prove Spring proxy activation, self-invocation behavior, transaction propagation, or runtime dispatch.
- It does not infer Spring Data default transaction behavior.
- One covered direct caller does not prove that an unobserved runtime caller cannot exist.
## TypeORM DB Operation Calibration

PR-REAL-04 adds provenance-aware TypeORM receiver correlation and canonical
`db.read`, `db.write`, `db.transaction`, and `db.query_unknown` facts.
Repository, EntityManager, DataSource, QueryRunner, QueryBuilder, and explicit
BaseEntity signals are covered without treating ordinary `.get()`, `.save()`,
or `.delete()` calls as database operations.

The original NestJS Boilerplate smoke observed TypeORM usage but reported zero
DB operations. The pinned offline rerun completed without executing third-party
code.

### Pinned rerun statistics

| Metric | NestJS Boilerplate | Queue/cache TypeScript case | Spring PetClinic |
|---|---:|---:|---:|
| Scanned files | 471 | 739 | 151 |
| TypeORM imports | 31 | 72 | 0 |
| Injected repositories | 6 | 15 | 0 |
| TypeORM reads | 16 | 51 | 0 |
| TypeORM writes | 41 | 46 | 0 |
| TypeORM transaction signals | 0 | 11 | 0 |
| Explicit-context TypeORM writes | 0 | 13 | 0 |
| Unresolved-context TypeORM writes | 41 | 33 | 0 |
| Raw SQL unknown | 0 | 1 | 0 |
| Total DB operations | 57 | 98 | 68 |
| Evidence integrity errors | 0 | 0 | 0 |
| Strict verify | pass | pass | pass |

NestJS produced seven `db_write_outside_tx` patterns; all remained
`suspected` with unresolved TypeScript transaction coverage rather than being
promoted to a transaction correctness claim. The queue/cache case produced
eight such suspected patterns. No QueryBuilder operation was observed in these
two pinned repositories, so QueryBuilder behavior remains fixture-backed.

### Source sampling

- NestJS: five seed `Repository.count()` reads and five migration
  `QueryRunner.query()` DDL writes were confirmed by source.
- Queue/cache case: five repository reads, five repository writes, and all
  eleven explicit transaction signals in the generated triage sample were
  confirmed by source.
- The one dynamic `DataSource.query()` item remains `needs_context`; it is
  retained as `db.query_unknown`.
- Redis/cache calls remained 45 cache observations and did not enter the
  TypeORM artifact. Sampled non-TypeORM calls included `app.get()`,
  configuration `.get()`, HTTP request/response `.get()`, and cache service
  `.get()`, `.set()`, and `.delete()`.
- Spring PetClinic remained at 68 Java DB operations, 58 transaction signals,
  and 46 `covered_explicit` correlations.

The calibrated review decisions were `REVIEW` for both TypeScript cases and
`WARN` for Spring PetClinic. Unknown TypeScript transaction coverage remains
suspected. These facts do not prove transaction correctness or data
consistency.

## TypeScript / TypeORM Transaction Correlation Calibration

The 2026-07-19 offline rerun reused the pinned workspaces and did not execute
third-party code. TypeScript correlations now share
`transaction_correlations.json` with the existing Java/Spring correlations.

### Correlation results

| Metric | NestJS Boilerplate | Queue/cache TypeScript case | Spring PetClinic |
|---|---:|---:|---:|
| TypeORM writes | 41 | 46 | 0 |
| `covered_explicit` | 0 | 13 | 0 |
| `uncovered` | 5 | 0 | 0 |
| `partially_covered` | 0 | 0 | 0 |
| `read_only_transaction` | 0 | 0 | 0 |
| `unknown` | 36 | 33 | 0 |
| Migration policy unresolved | 26 | 0 | 0 |
| `db_write_outside_tx` before / after | 7 / 7 | 8 / 8 | 0 / 0 |
| Human Review Required | 19 | 32 | 37 |
| Review Decision | REVIEW | REVIEW | WARN |
| Evidence integrity | 1295/1295 | 3539/3539 | 904/904 |
| Strict verify | pass | pass | pass |

NestJS contains no trusted explicit TypeORM transaction signal in the pinned
revision. The five `uncovered` writes are direct seed-service operations; the
26 migration writes remain `unknown` with
`migration_transaction_policy_requires_confirmation`; the remaining ten
unknown writes are repository-wrapper operations with no uniquely resolved
explicit caller. All seven existing outside-transaction Pattern groups were
reviewed and retained as suspected. No coverage was invented to reduce their
count.

The queue/cache case has thirteen writes inside nine statically bounded
`DataSource.transaction(...)` callbacks. Source review confirmed every
transaction boundary and write evidence pair. The remaining 33 writes are
repository-wrapper operations without a uniquely resolved explicit
transaction caller and remain `needs_context`. The eight outside-transaction
Pattern groups remain suspected. Cache observations stayed at 45, so Redis
operations were not correlated as TypeORM transactions.

Spring PetClinic retained 68 Java DB operations and 46 Java/Spring
`covered_explicit` correlations. It produced zero TypeScript correlations.
This confirms the shared artifact merge did not change Spring transaction
semantics.

No real pinned case exercised a TypeScript QueryRunner write between
`startTransaction()` and commit/rollback, a trusted transaction decorator, or
a mixed wrapper caller. Those paths remain synthetic-fixture backed. The
correlation result is static evidence, not proof of transaction activation,
propagation, rollback behavior, or runtime correctness.

## Queue Retry / Idempotency Correlation Calibration

The 2026-07-19 offline rerun reused all four pinned workspaces. RepoSense did
not install, build, test, or execute third-party code.

| Metric | TypeScript BullMQ/Redis | Java Spring Kafka | NestJS | Spring PetClinic |
|---|---:|---:|---:|---:|
| Reliability correlations | 3 | 3 | 0 | 0 |
| Matched channels | 2 | 2 | 0 | 0 |
| Explicit retries | 0 | 0 | 0 | 0 |
| Producer identity / transport idempotence | 0 | 0 | 0 | 0 |
| Side-effecting consumers | 0 | 0 | 0 | 0 |
| Consumer guards | 0 | 0 | 0 | 0 |
| New suspected risks | 0 | 0 | 0 | 0 |
| Reliability evidence valid/errors | 12 / 0 | 10 / 0 | 0 / 0 | 0 / 0 |
| Strict verify | pass | pass | pass | pass |
| Review Decision | REVIEW | WARN | REVIEW | WARN |

The TypeScript case retained the previous three dispatches, three consumers,
two matched channels, and 45 cache observations. Source sampling covered every
correlation. `checkout` is consumer-only; `notifications` and
`payment-events` are matched. Their `WorkerHost.process` methods delegate to
injected step/process objects, so the permitted same-handler or uniquely
resolved one-hop analysis does not claim downstream database/cache effects.
No explicit `attempts`, default retry option, `jobId`, or BullMQ deduplication
signal was observed in the correlated producers.

The Java case retained three dispatches, two consumers, two matched topics, and
one dynamic producer topic. Source sampling confirmed that the two matched
Kafka listeners only log messages and that no `@RetryableTopic`,
`DefaultErrorHandler`, producer idempotence, or consumer business guard was
observed. Dynamic topic evidence remained unresolved and did not produce a
strong risk.

NestJS Boilerplate and Spring PetClinic produced no queue reliability facts,
as expected. Their TypeORM and Spring transaction baselines remained intact:
NestJS retained 41 TypeORM writes and seven suspected outside-transaction
patterns; Spring retained 68 Java DB operations and 46
`covered_explicit` transaction correlations. Evidence integrity passed for all
four cases (73/73 Java Kafka, 1295/1295 NestJS, 904/904 Spring PetClinic, and
3539/3539 TypeScript BullMQ/Redis records).

No pinned real case contains explicit retry configuration in the statically
matched channels. Positive retry, producer-identity, consumer-guard,
check-then-write, and suspected-risk behavior therefore remains
synthetic-fixture backed. No coverage or risk was invented to improve counts.

## TypeORM Cross-file Alias Resolution Calibration

The 2026-07-29 offline rerun reused the pinned NestJS Boilerplate,
ecommerce-store-api, and Spring PetClinic workspaces. Third-party code was not
executed.

| Metric | NestJS before / after | ecommerce before / after |
|---|---:|---:|
| TypeORM writes | 41 / 41 | 46 / 46 |
| `covered_explicit` | 0 / 0 | 13 / 13 |
| `uncovered` | 3 / 10 | 0 / 12 |
| `unknown` | 38 / 31 | 33 / 21 |
| `db_write_outside_tx` | 7 / 7 | 8 / 8 |
| Resolved wrapper calls | 0 / 11 | 0 / 14 |
| Ambiguous / unresolved candidates | n/a / 11 / 0 | n/a / 0 / 121 |
| Evidence integrity | 1395 / 1395 | 3865 / 3865 |
| Strict verify | pass | pass |

The immediate pre-change NestJS rerun on this baseline reported 3 uncovered
and 38 unknown writes, which differs from the older historical 5/36 snapshot
above. The pinned source and TypeORM write count were unchanged; this section
records the directly comparable rerun rather than rewriting history.

Source sampling confirmed:

- `FilesLocalService.create` line 30 resolves through its constructor
  `FileRepository` to `FileRelationalRepository.create` line 18.
- `SessionService.create` line 19 resolves to
  `SessionRelationalRepository.create` line 30.
- `UsersService.remove` line 286 resolves to
  `UserRelationalRepository.remove` line 123.
- Files, Session, and Users read methods with document/relational provider
  alternatives remain ambiguous rather than selecting an implementation.
- ecommerce permission/role initialization and session-token use cases resolve
  to their imported PostgreSQL wrapper methods and canonical writes.
- No newly resolved caller in either repository had trustworthy explicit
  transaction evidence, so no new `covered_explicit` result was created.

NestJS retained seven suspected outside-transaction Pattern groups and 19
Human Review items. ecommerce retained eight suspected outside-transaction
groups, 45 cache observations, and 32 Human Review items. Their Review
Decisions remained REVIEW.

Spring PetClinic retained 68 Java DB operations and 46 Java
`covered_explicit` correlations. TypeScript alias artifacts were empty, all
904 evidence records were valid, and strict verify passed. The alias resolver
does not change Java/Spring transaction semantics.
