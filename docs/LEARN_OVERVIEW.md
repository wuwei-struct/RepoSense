# Learn Overview

## Goal

Learn turns analysis outputs into a grounded learning path:

Concepts -> Cases -> Evidence

## Learn Building Blocks

## ConceptGraph

- Concept nodes define engineering ideas (for example transaction boundary, idempotency).
- Concept links encode prerequisite and related relationships.

## CaseLibrary

- Cases are concrete examples mapped to Concepts.
- Each Case includes explain blocks and Evidence references.

## Learn UI

- Concept list/detail pages
- Case list/detail pages
- Evidence blocks with expandable snippets
- Deep links back to source evidence and concept context

## Grounded Explain in Learn

Learn explanations are grounded in existing Case / Evidence data. No free-form model narrative is required for baseline usage.

## Analysis -> Learn

- Analysis generates Findings / Events / Evidence.
- Case extraction and indexing build Cases tied to Concepts.
- Learn UI consumes Concepts + Case indexes in read-only mode.

## Learn -> Analysis

- From Learn pages, users can jump back to analysis evidence, files, and related outputs.
- Learn does not overwrite analysis truth source.

## Trust Boundaries

- Read-only for Concepts/Cases.
- Stable routes and deterministic rendering.
- Evidence traceability is preserved end-to-end.
