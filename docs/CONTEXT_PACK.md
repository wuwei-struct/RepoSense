# CONTEXT_PACK

## Added artifacts for TS async visibility
- ARTIFACTS/framework_event_summary.json
  - languages_detected
  - frameworks_detected
  - event_counts_by_kind
  - event_counts_by_language
  - event_counts_by_framework
  - top_queue_frameworks
  - top_cache_frameworks
- ARTIFACTS/unsupported_detected.json
  - records unsupported_detected warnings
  - includes TS reasons such as:
    - saw_bull_import_but_no_explicit_worker_or_add_pattern
    - saw_redis_hint_but_no_explicit_cache_op_pattern
- MAP/event_catalog.json
  - event_kind
  - language
  - framework
  - count
  - sample_event_ids

## README summary additions
- TS frameworks seen
- Queue events dispatch/consume counts
- Cache events read/write/invalidate counts
- Java queue events dispatch/consume counts
- Java DB events read/write counts
- Unsupported but detected hints count

## framework_event_summary Java additions
- frameworks_detected now includes possible:
  - spring_kafka
  - spring_rabbit
  - jpa
  - mybatis
- event_counts_by_kind includes:
  - db.read
  - db.write
- event_counts_by_framework reflects Java queue/db counts

## Added artifacts for cross-language v1
- ARTIFACTS/api_callers.json
  - TS outgoing fetch/axios callers
  - caller fields and unsupported_detected records
- ARTIFACTS/cross_language_summary.json
  - total_callers
  - matched_callers
  - unmatched_callers
  - total_endpoints
  - endpoints_with_callers
  - endpoints_without_callers
  - exact_match_count
  - template_match_count
  - links_by_language_pair
- MAP/cross_language_links.json
  - exact_match and template_match links
  - unmatched_callers
  - unmatched_endpoints
- MAP/api_topology.json
  - normalized endpoint-caller-link topology

## Cross-language README additions
- API endpoints detected
- TS callers detected
- Matched links
- Exact/template match counts
- Unmatched callers and endpoints without caller
- Top matched pairs and unmatched samples

## Scope
- Evidence-first and L2 conservative extraction
- No cross-file queue/cache semantic linking in this phase
