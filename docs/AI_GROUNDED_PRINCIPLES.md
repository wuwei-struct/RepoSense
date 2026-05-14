# AI Grounded Principles

## Why This Exists

RepoSense AI features are designed for auditability and repeatability, not unconstrained code chat.

## Facts-only Reasoning by Default

AI features first consume run artifacts such as:

- `report.json`
- `event_graph.json`
- `api_surface.json`
- `coverage.json`
- `quality_gate.json`
- `patterns.json`
- `pattern_summary.json`

## Source Drill-down On Demand

When facts are insufficient, use constrained drill-down:

- Evidence-first selection
- File/range/context windows only
- Hard budgets for files/snippets/lines/chars
- Explicit `why_selected` and `source_refs`

No unrestricted full-repository source traversal.

## Output Uncertainty Contract

All explain-style outputs separate:

- confirmed
- inferred
- unknown

Uncertain claims must not be presented as confirmed.

## Why Pattern Engine Comes First

Pattern Engine stabilizes semantic interpretation before narrative outputs.

Code -> Facts -> Patterns -> Insights

This reduces drift and keeps explanations anchored to evidence.

## Feature Boundaries

## summary

- Facts + Patterns overview
- deterministic section structure

## risks

- batch risk ranking from patterns + gate context
- optional targeted drill-down for suspected medium/high

## explain

- single-target grounded explanation
- optional drill-down when closure is insufficient

## ask

- restricted question types (`summary`, `risk`, `evidence`, `flow`)
- unsupported questions are explicitly rejected with scope guidance

## Non-goals in This Boundary

- open-domain chat
- provider-specific model behavior assumptions
- free source roaming
