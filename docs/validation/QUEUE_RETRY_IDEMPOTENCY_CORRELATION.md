# Queue Retry / Idempotency Correlation

RepoSense correlates static queue retry configuration, matched consumers,
consumer side effects, and idempotency evidence. The result is a review aid;
it is not proof that retries are active or that message processing is
idempotent at runtime.

## Artifacts

A normal analysis run can generate:

- `queue_reliability_correlations.json`
- `queue_reliability_summary.json`
- `queue_reliability_risks.json`

Real-repository smoke validation additionally generates:

- `queue_retry_idempotency_validation.json`
- `queue_retry_idempotency_validation.md`
- `queue_retry_idempotency_triage_template.json`

The triage template always starts as `unreviewed`. Automated validation does
not claim human source confirmation.

## Correlation model

Producer and consumer facts are matched by framework plus a statically
resolved queue or topic name. Dynamic or unknown names are retained but do not
produce strong orphan or retry/idempotency conclusions.

The correlation distinguishes:

- retry status: explicit retry, explicit no-retry, default/unknown, or dynamic;
- producer identity: Bull/BullMQ `jobId` or deduplication, Kafka message key,
  and Kafka transport idempotence;
- consumer guard: persistent processed-event/inbox state, unique constraints,
  Redis NX/SETNX, or an explicit idempotency service;
- side effects: canonical DB writes, cache writes/invalidations, and further
  queue dispatches in the same handler or a uniquely resolved one-hop helper.

## Producer identity is not consumer idempotency

`jobId`, a Kafka message key, BullMQ deduplication, and
`enable.idempotence=true` are producer or transport signals. They can reduce
duplicate enqueue or producer transport behavior, but they do not prove that a
consumer's database, cache, HTTP, or downstream message side effects are safe
under redelivery.

Reading or logging a message/job ID is also not an idempotency guard.

## Bull and BullMQ

The MVP recognizes `queue.add(...)`, `defaultJobOptions`, `attempts`,
fixed/exponential backoff, `jobId`, BullMQ deduplication, `new Worker`,
`queue.process`, `@Processor`, and `WorkerHost`.

Only a statically resolved `attempts > 1` is an explicit retry. Dynamic
configuration remains unresolved. `removeOnComplete` and `removeOnFail` do not
count as retry or idempotency.

## Spring Kafka

The MVP recognizes `@RetryableTopic`, fixed/exponential backoff,
`DefaultErrorHandler`, `DeadLetterPublishingRecoverer`, Kafka message keys, and
producer transport idempotence. Error-handler and broker runtime wiring can be
dynamic, so unresolved configuration remains a limitation.

Kafka producer idempotence does not satisfy consumer business idempotency.

## Spring Rabbit

The MVP recognizes `@Retryable`, `RetryTemplate`, common retry interceptor
signals, and fixed/exponential backoff evidence. Dead-letter configuration is
failure-routing evidence, not consumer idempotency evidence. RepoSense does not
construct a complete Spring Bean graph.

## Guard strength

Persistent or atomic evidence can satisfy a consumer guard:

- processed-message/event/job persistence;
- inbox or consumed-event storage;
- a unique constraint or equivalent conflict-safe insert/upsert;
- Redis `SET NX` / `SETNX`;
- an explicit idempotency/deduplication service.

A non-atomic check followed by a write is only
`guard_signal_observed` and carries
`check_then_write_atomicity_unresolved`. A transaction alone is not
idempotency.

## Conservative risks

Two Pattern types are emitted:

- `queue_retry_without_idempotency_guard`
- `queue_consumer_side_effect_without_idempotency_evidence`

Both remain `suspected`; severity is no higher than `medium`. A risk requires
a matched, statically named consumer and a canonical side-effect evidence
chain. Unknown names, consumers without observed side effects, and insufficient
evidence do not produce a strong risk.

Missing evidence means "not observed by this static analysis", not "proven
absent".

## Downstream use

Backend Verifier and Repository Review summarize matched channels, retries,
consumer guards, producer-only dedupe, side effects, unresolved policies, and
actionable suspected risks. Run Manifest and Context Pack include the JSON
artifacts when present. No new Review Decision or BLOCK rule is introduced.

## Pinned real-repository result

The 2026-07-19 offline rerun used the existing fixed workspaces and did not
execute third-party code:

| Case | Matched channels | Explicit retry | Side-effecting consumer | Consumer guard | New risk | Evidence |
|---|---:|---:|---:|---:|---:|---:|
| `typescript-bullmq-redis-ecommerce` (`147231b54ed8f8a7f3a0b5110db757a39650892c`) | 2 | 0 | 0 | 0 | 0 | 12/12 valid |
| `java-spring-kafka-reactive` (`46492f9147673513338505049eff09bc796dd166`) | 2 | 0 | 0 | 0 | 0 | 10/10 valid |

The TypeScript case retained three BullMQ correlations. Consumer handlers
delegate to injected step/process objects, so the allowed same-handler or
uniquely resolved one-hop analysis does not claim their downstream effects.
The Java case retained three Kafka correlations; sampled consumers only log
messages. Neither pinned revision contained explicit retry configuration, so
no retry/idempotency risk was invented. The full positive/negative behavior is
backed by the synthetic BullMQ, Kafka, and Rabbit fixture.

## Current limits

- same-handler and uniquely resolved one-hop helper scope only;
- no complete TypeScript or Java type system;
- no full Spring Bean graph;
- no runtime environment/configuration execution;
- no multi-hop call graph, reflection, or dynamic DI proof;
- no guarantee of message ordering, exactly-once delivery, rollback behavior,
  external API idempotency, or cache consistency.

These outputs support evidence-guided review. They do not replace source review,
integration testing, chaos testing, or production reliability controls.
