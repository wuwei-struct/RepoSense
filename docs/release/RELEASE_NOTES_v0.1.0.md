# RepoSense v0.1.0 - Backend Transaction, Side-effect, and Upgrade-context System

## Included In This Release

### Analysis

- Repository scanning to structured Findings, Events, and Evidence references.
- Deterministic run artifacts including `report.json`, `event_graph.json`, `api_surface.json`, `coverage.json`, and `quality_gate.json`.
- Main run chain remains stable: `ci run -> verify --strict -> gate -> patch exports -> run manifest`.

### Learn

- Learn UI minimal loop with concept and case browsing.
- Read-only, grounded navigation over concepts/cases/evidence artifacts.

### AI Insights

- Deterministic `patterns.json` + `pattern_summary.json`.
- Facts-only `ai summary`, `ai risks`, `ai explain`, and constrained `ai ask`.
- Explain/Risks outputs keep explicit `confirmed / inferred / unknown` boundaries.

### Demo / Docs / Studio

- One-command demo flow via `tools/demo_run.ps1`.
- Productized docs entry points and demo asset index.
- Studio/run view supports AI Summary, Risks panel, Explain entry, and snippet deep links.

## Key Capabilities

- Facts layer: findings/events/event graph with evidence traceability.
- Export layer: report/context pack/gate/manifest contracts.
- Learn layer: concept and case navigation from grounded data.
- Insights layer: patterns, summary, risks, explain, and ask over existing artifacts.
- Upgrade-context handoff layer: Context Pack + baseline diff + run manifest for the next AI-assisted change.

## Trust Boundaries

- Evidence-first
- Deterministic
- Facts first, source on demand
- AI does not freely roam the whole repository by default

## Supported Languages And Current Scope

Current scope centers on:

- Python
- TypeScript/JavaScript
- Java
- SQL
- OpenAPI signals

Not in this release as completed scope:

- Full Go closed-loop parity
- Deep semantic whole-program reasoning
- Open-ended free-repo conversational agent behavior

## Known Limitations

- No full backend correctness proof.
- No default whole-repo AI roaming.
- Some conclusions remain heuristic and intentionally marked as inferred/suspected.
- Screenshot PNG assets may still be pending manual capture according to the capture plan.

## Demo And Quickstart

- Quickstart command: `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1`
- See also: `README.md`
- Full walkthrough: `docs/DEMO_QUICKSTART.md`

## Output Examples

- Demo output map: `docs/assets/demo/demo-outputs.md`
- Product flow: `docs/assets/demo/product-flow.md`
- Asset/source tracking: `docs/assets/ASSET_INDEX.md`

