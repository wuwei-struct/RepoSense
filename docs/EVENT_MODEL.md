# EVENT_MODEL

## Why unified events
RepoSense keeps detections.sqlite as the source of truth. This layer adds a runtime-only normalized event view so multiple languages can share a stable vocabulary without DB schema changes.

## Core event kinds
- api.route
- db.transaction
- db.read
- db.write
- queue.dispatch
- queue.consume
- cache.read
- cache.write
- cache.invalidate
- job.schedule
- job.execute

## Fields
- event_kind: normalized kind
- event_family: api | db | queue | cache | job
- language: python | sql | openapi | typescript | java | go | unknown
- framework: fastapi | flask | django | celery | express | nestjs | prisma | typeorm | bull | bullmq | openapi | sql | redis | ioredis | spring | unknown
- source_detector
- parse_level
- confidence
- evidence_ids
- location
- meta

## Conservative boundaries
- No cross-language inference in this phase
- Unknown patterns remain unknown
- Mapping failures do not block scan/verify/export/gate
- Existing artifacts remain authoritative
- Cross-language links are derived exports, not Event source of truth

## TypeScript mapping (PR-18)
- Express route pattern:
  - app.get/post/put/delete/patch("literal", ...)
  - router.get/post/put/delete/patch("literal", ...)
  - mapped to api.route
- NestJS route pattern:
  - @Controller("prefix") + @Get/@Post/@Put/@Delete/@Patch("literal?")
  - mapped to api.route
- Prisma transaction pattern:
  - <expr>.$transaction(...)
  - mapped to db.transaction
- TypeORM transaction pattern:
  - dataSource.transaction(...)
  - manager.transaction(...)
  - connection.transaction(...)
  - mapped to db.transaction

## Current TS boundaries
- L1/L2 only
- No cross-file call resolution
- No cross-file queue producer-consumer linking
- No Redis key dataflow tracing

## TypeScript mapping (PR-19)
- Bull/BullMQ queue dispatch pattern:
  - queue.add("jobName", payload)
  - mapped to queue.dispatch
- Bull/BullMQ queue consume pattern:
  - new Worker("queueName", async job => ...)
  - queue.process(async job => ...)
  - mapped to queue.consume
- Redis/ioredis cache read pattern:
  - client.get / client.mget / client.hget
  - mapped to cache.read
- Redis/ioredis cache write pattern:
  - client.set / client.hset / client.expire
  - mapped to cache.write
- Redis/ioredis cache invalidate pattern:
  - client.del / client.unlink / client.hdel
  - mapped to cache.invalidate

## Java mapping (PR-21)
- Spring route pattern:
  - @RequestMapping
  - @GetMapping / @PostMapping / @PutMapping / @DeleteMapping / @PatchMapping
  - mapped to api.route
- Transaction pattern:
  - @Transactional (class-level or method-level)
  - mapped to db.transaction
  - mapped to db.transaction

## Java mapping (PR-22)
- Queue consume:
  - @KafkaListener / @RabbitListener
  - mapped to queue.consume
- Queue dispatch:
  - KafkaTemplate.send / RabbitTemplate.convertAndSend
  - mapped to queue.dispatch
- DB read/write:
  - JPA Repository / EntityManager / MyBatis Mapper / SqlSession base ops
  - mapped to db.read / db.write
