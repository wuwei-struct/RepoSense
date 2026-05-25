# Architecture Overview

## Purpose

RepoSense provides a layered, auditable path from source code to engineering insight:

1. Analysis
2. Learn
3. AI Insights
4. Studio

## Layer Model

```text
Code Repo
  -> Analysis (Findings, Events, Evidence)
  -> Facts artifacts
  -> Pattern Engine (deterministic)
  -> Insights (summary, risks, explain, ask)
  -> Studio / Learn UI surfaces
```

## Analysis / Learn / AI / Studio Relationship

- Analysis is the extraction layer. It produces Findings, Events, Evidence, and structured facts artifacts.
- Learn is the grounded learning layer. It organizes Concepts and Cases and links back to Evidence.
- AI Insights is the derived reasoning layer. It consumes Facts + Patterns first, then optionally uses constrained source drill-down.
- Studio is the local read UI layer for run outputs, risks, explain, snippets, and links into Learn.
- Studio UI is the local interactive surface for ZIP import or local-path analysis, run orchestration, and artifact navigation.
- Studio reuses the existing scanning/run/artifact pipeline and does not change Fact Engine semantics.
- Studio is not a hosted cloud platform by default.

## Facts / Patterns / Insights Separation

- Facts:
  - Truth-bearing run outputs from analysis.
  - Example: `report.json`, `event_graph.json`, `api_surface.json`, `quality_gate.json`.
- Patterns:
  - Deterministic, evidence-linked engineering patterns derived from Facts.
  - Example: `patterns.json`, `pattern_summary.json`.
- Insights:
  - User-facing derived outputs driven by Facts and Patterns.
  - Example: `ai_summary.*`, `ai_risks/*`, `ai_explain/*`, `ai_ask/*`.

## Truth Source and Auditability

- Primary truth source remains `detections.sqlite` plus Evidence references.
- Derived artifacts do not overwrite truth source.
- `run_manifest.json` records artifact integrity and reproducibility metadata.

## Why AI Does Not Read Full Source by Default

- Full-repo free roaming reduces determinism and auditability.
- Facts-first keeps cost and output drift under control.
- Source drill-down is available only on demand and bounded by Evidence refs + budget.

## Trust Principles

- Evidence-first
- Deterministic
- Facts first, source on demand
