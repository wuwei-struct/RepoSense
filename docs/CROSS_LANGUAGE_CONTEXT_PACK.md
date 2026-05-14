# CROSS_LANGUAGE_CONTEXT_PACK

## Why links are export-layer only
Cross-language links are generated from stable run artifacts and remain derived outputs.  
The source of truth stays in detections.sqlite and evidence files.  
This keeps schema and verifier contracts stable while enabling practical cross-language navigation.

## Fields
### caller
- caller_id
- language
- source_kind
- http_method
- path_literal or path_template
- path_normalized
- client_kind
- file
- line_start
- line_end
- snippet
- confidence
- parse_level

### endpoint
- endpoint_id
- method
- path
- path_normalized
- language
- framework
- source_kind
- file
- line_start
- line_end

### link
- link_id
- caller_id
- endpoint_id
- match_type
- confidence
- language_pair
- method
- caller_path
- endpoint_path
- evidence_refs
- caller file/line
- endpoint file/line

## Match rules
- exact_match:
  - same method
  - normalized paths are equal
- template_match:
  - same method
  - endpoint path has placeholders like `{id}` or `:id`
  - segment count is equal
  - all static segments are equal

## Unsupported in v1
- baseURL/host inference
- query semantic matching
- env/runtime URL assembly
- cross-file DI or interprocedural dataflow
- GraphQL/WebSocket/gRPC

## Java extension direction
- keep the same endpoint index contract
- add Java endpoint extraction to api_surface
- reuse the same matcher without changing truth-source schema

## Supported language pairs in v1
- typescript -> python
- typescript -> openapi
- typescript -> typescript
- typescript -> java
