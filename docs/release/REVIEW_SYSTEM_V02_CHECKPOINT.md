# Review System v0.2 Checkpoint

## Baseline

- Starting HEAD: `579eacc52dc2eec906aa604f298dcd5fff9f6b71`
- Branch: `main`
- Checkpoint date: `2026-07-19`
- Public OSS baseline: `v0.1.0`
- Position: Review System v0.2 development baseline

This checkpoint consolidates the evidence-guided repository review work that
accumulated after the public v0.1.0 baseline. It is a development checkpoint,
not a formal release and not a reconstruction of separate historical PR
commits.

## Completed Capabilities

- **Repository Review** packages deterministic review decisions, risk matrices,
  and human-review queues from available analysis artifacts.
- **Code Health Radar** reports conservative code-health and maintainability
  signals while retaining source evidence and heuristic limitations.
- **Permission Auditor** extracts route and guard facts and reports permission
  risks without claiming authorization correctness.
- **AuthZ Matrix** supports an optional authority contract and an inferred-only
  mode that requires project-owner confirmation.
- **Context Pack REVIEW** provides a facts-first handoff for human and
  AI-assisted maintenance.
- **Studio Review UI** exposes generated review artifacts without running or
  replacing the review pipeline.
- **Real Repository Smoke Harness** runs reproducible, fixed-commit static
  validation without executing third-party repository code.
- **Evidence Location Contract** validates repository-relative source paths,
  positive line ranges, snippets, and evidence propagation.
- **Spring Transaction Correlation** conservatively links explicit
  `@Transactional` scopes to direct Java database writes.
- **Review Context Calibration** classifies public auth entrypoints and
  non-production file contexts to distinguish raw from actionable findings.
- **OpenAPI / Guard Correlation** separates documented security expectations
  from method, controller, and global implementation guard evidence.
- **Route Decorator Classification** uses exact NestJS decorator symbols and
  syntax context to reject property and parameter decorators as routes.
- **Queue / Cache Coverage** validates framework-aware producer, consumer, and
  cache facts with conservative unresolved-name handling.
- **TypeORM DB Operation Coverage** normalizes TypeORM receivers, operations,
  transactions, QueryBuilder calls, and raw SQL evidence.
- **TypeScript Transaction Correlation** links explicit TypeORM callback,
  QueryRunner, trusted decorator, and direct one-hop wrapper transaction
  evidence without claiming complete runtime coverage.

## Real Repository Validation

Third-party source is not included in this repository. Validation uses exact
commits and does not run third-party install, build, test, or application code.

| Case | Repository | License | Fixed commit | Validation role |
| --- | --- | --- | --- | --- |
| Brocoders NestJS Boilerplate | `https://github.com/brocoders/nestjs-boilerplate.git` | MIT | `549cc37a3925ab87a4e61b45efb3b86d2d8e234e` | NestJS routes, guards, TypeORM, permissions, and TypeScript transactions |
| Spring PetClinic REST | `https://github.com/spring-petclinic/spring-petclinic-rest.git` | Apache-2.0 | `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd` | Spring MVC, JPA, evidence integrity, security signals, and transaction correlation |
| ecommerce-store-api | `https://github.com/raouf-b-dev/ecommerce-store-api.git` | MIT | `147231b54ed8f8a7f3a0b5110db757a39650892c` | BullMQ, Redis, TypeORM receiver separation, and TypeScript transactions |
| apache-kafka-with-spring-boot-reactive | `https://github.com/ali-bouali/apache-kafka-with-spring-boot-reactive.git` | Apache-2.0 | `46492f9147673513338505049eff09bc796dd166` | Spring Kafka producer and consumer evidence |

The validation results establish reproducibility and evidence integrity for
the observed samples. They do not establish semantic correctness for every
route, transaction, queue, cache, or database operation.

## Known Boundaries

- RepoSense is not a complete security proof.
- Permission review and AuthZ Matrix output are not complete authorization
  proofs.
- Transaction correlations are not complete transaction-correctness proofs.
- TypeScript and Java support remains conservative static parsing.
- Dynamic dependency injection, reflection, multi-hop calls, runtime
  configuration, and custom framework behavior can remain unresolved.
- ResourceWarning noise has not been fully eliminated from every execution
  environment.
- Hosted AI Insight remains outside the deterministic OSS Core.
- Suspected findings require source inspection and human confirmation.

## Next Stage

- `PR-REAL-05`: Queue Retry / Idempotency Correlation
- TypeORM Cross-file Alias Resolution
- Studio Artifact Cards Polish
- Release v0.2.0 preparation
