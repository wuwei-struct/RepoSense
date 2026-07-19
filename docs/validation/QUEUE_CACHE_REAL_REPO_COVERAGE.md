# Queue / Cache Real Repository Coverage

This protocol validates RepoSense queue and cache facts against pinned open-source repositories. It uses static analysis only: target repositories are not installed, built, tested, started, or otherwise executed.

## Cases

| Case | Repository | License | Pinned commit | Coverage target |
|---|---|---|---|---|
| `typescript-bullmq-redis-ecommerce` | `raouf-b-dev/ecommerce-store-api` | MIT | `147231b54ed8f8a7f3a0b5110db757a39650892c` | NestJS BullMQ producer/consumer and Redis/cache wrappers |
| `java-spring-kafka-reactive` | `ali-bouali/apache-kafka-with-spring-boot-reactive` | Apache-2.0 | `46492f9147673513338505049eff09bc796dd166` | Spring Kafka producer and listener |

The pinned metadata lives in `tools/validation/real_repo_cases.json`. Third-party source and generated smoke output remain under the ignored `.reposense_real_repo_smoke/` directory.

## Run

First acquisition requires explicit network access:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 -CaseId typescript-bullmq-redis-ecommerce -AllowNetwork -KeepWorkspace
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 -CaseId java-spring-kafka-reactive -AllowNetwork -KeepWorkspace
```

Subsequent calibration is offline:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 -CaseId typescript-bullmq-redis-ecommerce -SkipClone -KeepWorkspace
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 -CaseId java-spring-kafka-reactive -SkipClone -KeepWorkspace
```

## Validation artifacts

Each case produces:

- `queue_cache_validation.json`
- `queue_cache_validation.md`
- `queue_cache_triage_template.json`

The JSON report includes normalized queue/cache observations, producer-consumer pairs, unresolved names, duplicate counts, and Evidence Location validation. The Markdown file is a compact human-readable summary. Triage entries default to `unreviewed`; only source-inspected entries may be changed to a human review status.

## Producer / consumer matching

Matching is conservative and framework-aware:

1. Match on framework plus a statically resolved queue/topic name.
2. Do not pair Bull/BullMQ queues with Kafka topics or Rabbit queues.
3. Preserve one-to-many consumer relationships.
4. Mark dynamic names as `unknown_name`.
5. Do not treat an unresolved name as a confirmed `queue_without_consumer`.

`match_status` is one of `matched`, `dispatch_only`, `consume_only`, `unknown_name`, or `ambiguous`.

## Bull / BullMQ coverage

The TypeScript detector recognizes:

- `new Queue(...)` and `queue.add(...)`
- `new Worker(...)`
- legacy `queue.process(...)`
- Nest BullMQ `@InjectQueue(...)`
- Nest BullMQ `@Processor(...)` on `WorkerHost` consumers
- named import aliases

Static literals and local string constants are resolved. Dynamic expressions are retained without being converted into invented queue names.

## Redis receiver boundaries

Redis/cache operations require one of:

- an instance resolved from `redis` or `ioredis`;
- a pipeline/multi derived from that instance;
- an explicit Redis client/service/connection receiver;
- an explicit cache service/client/store wrapper.

Generic `Map.get`, `Map.set`, HTTP delete calls, ORM delete calls, and metric receivers such as `redisStatus.set(...)` are not cache facts. Dynamic cache keys remain expressions and require confirmation.

## Spring Kafka / Rabbit coverage

The Java detector recognizes:

- `KafkaTemplate.send`
- `@KafkaListener`
- `RabbitTemplate.convertAndSend`
- `@RabbitListener`
- local string constants used as topics or queues

A `KafkaTemplate.send(message)` call is retained as a dispatch with an unresolved name when the topic is carried indirectly in message headers. RepoSense does not perform the cross-statement value flow needed to claim a static topic in that case.

## Recorded result

The pinned offline rerun completed with:

| Metric | TypeScript BullMQ/Redis | Java Spring Kafka |
|---|---:|---:|
| scanned files | 739 | 40 |
| queue dispatch | 3 | 3 |
| queue consume | 3 | 2 |
| matched queue/topic pairs | 2 | 2 |
| unmatched dispatch | 0 | 0 |
| unmatched consumer | 1 | 0 |
| unresolved queue/topic events | 0 | 1 |
| cache read/write/invalidate | 1 / 43 / 1 | 0 / 0 / 0 |
| queue/cache evidence valid/errors | 51 / 0 | 5 / 0 |
| strict verify | pass | pass |

The unmatched TypeScript item is a confirmed `@Processor("checkout")` consumer with no directly observed producer fact. It is not presented as a runtime defect. The unresolved Java item is `KafkaTemplate.send(message)` and remains suspected for orphan analysis.

## Boundaries

- Static producer-consumer pairing does not prove runtime delivery.
- A matching consumer does not prove retries, dead-letter handling, ordering, or idempotency.
- Cache observations do not prove cache consistency, eviction correctness, or freshness.
- Missing static evidence is not proof of missing runtime behavior.
- Results are calibration evidence, not a message reliability or correctness guarantee.
