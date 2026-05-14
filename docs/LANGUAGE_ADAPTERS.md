# LANGUAGE_ADAPTERS

## Adapter responsibility
Language adapters provide language-scoped capability metadata and projection hooks:
- detect_framework_hints
- emit_findings
- emit_events
- emit_api_surface
- emit_entrypoints
- capabilities

Adapters do not change DB schema, do not replace detector logic, and do not infer unsupported cross-language links.

## Registry contract
- list_registered_languages()
- get_adapter(language_id)
- get_capability_matrix()

The registry is deterministic and safely handles unknown language IDs.

## Add a new language
1. Create a new adapter implementing LanguageAdapter
2. Register it in adapters/registry.py
3. Declare capabilities and framework hints
4. Map existing detector outputs into unified events conservatively
5. Add tests for registration and capability matrix

## TypeScript adapter (current scope)
- language_id = "typescript"
- framework hints: express, nestjs, prisma, typeorm
- supported event kinds:
  - api.route
  - db.transaction
- supported API surface projection:
  - Express literal routes
  - NestJS Controller + HTTP verb decorators
- conservative boundaries:
  - no cross-file linking
  - no Bull/BullMQ
  - no Redis/ioredis
