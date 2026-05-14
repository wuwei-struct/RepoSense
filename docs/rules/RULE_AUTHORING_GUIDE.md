# Rule Authoring Guide

## When to Add a New Pattern

Add a pattern when:

- the signal appears repeatedly across repositories
- the signal has clear engineering meaning (transaction, queue, cache, side-effect)
- evidence references can be attached deterministically
- the output can be expressed conservatively

## When Not to Add a Pattern

Do not add a pattern when:

- evidence is insufficient or inconsistent
- rule semantics require speculative global reasoning
- claim depends on unstated runtime assumptions
- wording would overstate certainty

## rule_id Naming

Use stable lowercase snake_case.

Examples:

- `db_write_outside_tx`
- `queue_without_consumer`
- `api_write_without_idempotency_guard`

Avoid unstable or organization-specific IDs.

## category / severity / confidence_policy

- `category`: stable engineering domain label (`transaction`, `queue`, `cache`, `cross_language`, ...)
- `severity`: conservative risk level (`info`, `warning`, `error` by project policy)
- `confidence_policy`: use `conservative` unless strong evidence justifies stricter policy

## evidence_required Principle

Set `evidence_required=true` for public contract rules by default.

Pattern claims should be grounded in observable findings/events/evidence refs.

## Writing public_description

A good `public_description` is:

- short
- factual
- evidence-oriented
- free of guarantee language

Avoid wording like "proves" or "guarantees".

## Designing signals

Signals should be:

- composable (`db_write`, `queue_dispatch`, `transaction_boundary_absent`)
- explainable to contributors
- testable with fixtures

Prefer explicit signals over opaque scoring heuristics.

## Deterministic + Conservative by Design

- deterministic ordering and grouping
- no random weighting
- no hidden model calls in rule matching
- express missing observations as "not observed" rather than absolute absence

## Testing Requirements

For new pattern rules, include:

- fixture-level tests (minimal positive/negative examples)
- smoke/integration test over a run artifact
- regression checks for deterministic ordering and schema compatibility

## Avoid "Smart-Looking but Ungrounded" Rules

Do not ship rules that:

- rely on deep unstated assumptions
- cannot provide evidence refs
- mix explanation with detection semantics

Keep detection open, explainability enhancements layered.
