# Outputs Map

## Facts Outputs (analysis truth layer)

- `detections.sqlite`
- `report.json`
- `event_graph.json`
- `api_surface.json`
- `coverage.json`
- `quality_gate.json`
- `entrypoints.json`

## Readable Outputs

- `report.html`
- `learn/index.html`

## Export Outputs

- `exports/report.sarif.json`
- `exports/context_pack.zip`

## AI Derived Outputs

## Patterns

- `patterns.json`
- `pattern_summary.json`

## Summary

- `ai_summary.json`
- `ai_summary.md`

## Risks

- `ai_risks/risks.json`
- `ai_risks/risks.md`

## Explain

- `ai_explain/*/explain.json`
- `ai_explain/*/explain.md`

## Ask

- `ai_ask/*/answer.json`
- `ai_ask/*/answer.md`

## Drill-down

- `ai_drilldown/*/snippet_pack.json`
- `ai_drilldown/*/snippet_pack.md`

## Learn Outputs

- Concepts export (for Learn UI)
- Cases index and case files
- Learn static pages

## Contract and Control Files

- `run_manifest.json`
- baseline artifacts (when enabled)
- gate outputs and metadata

## Interpretation Boundary

- Facts outputs are truth-bearing.
- AI/learn outputs are derived and must remain evidence-linked.
- Manifest links all artifacts for integrity and replay.
