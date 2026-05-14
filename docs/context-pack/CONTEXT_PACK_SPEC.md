# CONTEXT_PACK_SPEC

## What is Context Pack

Context Pack is RepoSense's evidence-backed project maintenance context package.

It is designed for the next AI-assisted change round, not just for archival export.

## Why it is not a normal export zip

A normal export archive is usually passive output.

Context Pack is structured for active AI collaboration:

- reproducible facts handoff
- deterministic artifact map
- evidence-first investigation path
- upgrade and baseline comparison context

## Target AI Assistant Scenarios

Context Pack is intended to be consumed by assistants such as Cursor, Claude Code, Codex, and ChatGPT before making repository changes.

## Context Pack as Upgrade Handoff

Context Pack is the handoff artifact for the next AI-assisted upgrade.

It helps AI assistants and developers understand:

- entrypoints
- API surface
- backend events
- transaction / queue / cache signals
- findings and evidence
- quality gate status
- baseline diff
- run manifest

## Typical Use Cases

- project entrypoint understanding
- API surface understanding
- backend transaction and side-effect signal inspection
- high-risk finding review
- quality gate state review
- baseline diff and upgrade impact preparation

## Current Directory Structure (L1 style)

A typical context pack includes:

- `README.md`
- `MAP/index.json`
- `SPEC/*`
- `EVIDENCE/*`
- `ARTIFACTS/*`
- `manifest.json`

Depending on run content/version, additional map/artifact files may exist.

## Layer Purpose

- `README.md`: concise human/assistant entry summary
- `MAP/*`: navigation index and cross-artifact links
- `SPEC/*`: schema and shape references
- `EVIDENCE/*`: evidence snippets/references for grounded tracing
- `ARTIFACTS/*`: packaged facts and derived outputs
- `manifest.json`: package-level contract/traceability metadata

## Facts vs Derived/Export

Facts-oriented artifacts (truth-oriented inputs):

- Findings / Events / Evidence references
- `report.json`
- `event_graph.json`
- `api_surface.json`
- `coverage.json`
- `quality_gate.json`

Derived/export artifacts (consumption-oriented outputs):

- `patterns.json`
- `pattern_summary.json`
- `ai_summary.*`
- `ai_risks/*`
- `ai_explain/*`
- `backend_verifier_report.*`
- SARIF/context zip projections

## Existing RepoSense Assets in Context

Context Pack can coexist with and reference:

- Context Pack L1
- Quality Gate
- Baseline & Diff
- Run Manifest
- Backend Verifier Report
- Patterns / Risks / Explain / Ask (constrained)
- `report.html` / `learn/`

## Boundary

Context Pack provides evidence-backed context for AI collaboration and project maintenance.

It is not a full backend correctness proof.

It supports conservative, reproducible inspection and handoff.
