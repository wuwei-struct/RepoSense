# Facts, Patterns, Insights

## Definitions

## Facts

Facts are structured outputs extracted directly from code analysis.

- Components: Findings, Events, Evidence, Event Graph, API surface, coverage, gate results.
- Role: stable, auditable base for all downstream reasoning.

## Patterns

Patterns are deterministic engineering interpretations derived from Facts.

- Input: Facts artifacts only.
- Output: evidence-linked pattern objects.
- Role: bridge from low-level facts to engineering meaning.

## Insights

Insights are user-facing summaries and decisions derived from Facts + Patterns.

- Forms: summary, risks, explain, ask.
- Rule: must remain grounded to Evidence and explicit uncertainty.

## Facts First, Source On Demand

Default process:

1. Reason over Facts and Patterns.
2. If evidence is insufficient, run constrained source drill-down.
3. Keep outputs explicitly separated into confirmed / inferred / unknown.

## Example Flow

1. Pattern engine emits `transaction_missing` with evidence refs.
2. `ai explain` produces:
- confirmed: what is directly supported
- inferred: plausible but not confirmed
- unknown: what cannot be concluded yet
3. `ai risks` ranks the pattern with severity, status, evidence completeness.
4. `ai ask` answers only supported question types and links evidence/snippets.

## Boundaries

- No free full-repo source roaming by default.
- No model-generated claims without evidence anchoring.
- Derived artifacts do not become truth source.


## Context Pack in This Flow

Context Pack is the facts-first handoff standard between scan outputs and next-round AI-assisted maintenance work.

Facts describe what was observed.
Patterns organize recurring backend risks or structures.
Insights explain and prioritize.
Context Pack packages the above into upgrade-ready handoff context.

