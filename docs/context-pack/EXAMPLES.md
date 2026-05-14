# EXAMPLES

## Minimal Context Pack Layout (example)

```text
context_pack/
  README.md
  manifest.json
  MAP/
    index.json
  SPEC/
    report.schema.md
  EVIDENCE/
    top_findings/
  ARTIFACTS/
    report.json
    event_graph.json
    api_surface.json
    quality_gate.json
    backend_verifier_report.json
    patterns.json
```

## Typical AI Usage Scenario

Goal: prepare a safe backend maintenance plan for the next sprint.

Suggested flow:

1. read `README.md` + `MAP/index.json`
2. inspect `quality_gate.json`
3. inspect `backend_verifier_report.*`
4. inspect `patterns.json` and `ai_risks/risks.json`
5. open top evidence refs for uncertain items

Output expectation:

- scoped maintenance checklist
- high/medium transaction-side-effect risks
- explicit unknowns requiring drilldown

## Facts-only then Drilldown Example

Facts-only phase:

- identify queue.dispatch without observed consume
- identify write-like API without explicit guard

Drilldown phase (only if needed):

- open evidence-linked files/ranges
- confirm whether consumer/guard signals appear near evidence regions
- keep confirmed/inferred/unknown separated

## Upgrade Before/After Example

Given baseline inputs:

- `baseline_in.json`
- `baseline_diff.json`
- `quality_gate.json`

Use Context Pack to:

1. compare new transaction/side-effect signals vs baseline
2. identify newly introduced medium/high risk patterns
3. prepare upgrade notes for next AI-assisted modification round

This is evidence-backed upgrade context support, not a guarantee of safe upgrades.
