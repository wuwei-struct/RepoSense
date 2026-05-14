# Backend Verifier + Upgrade Context

## Product Positioning

RepoSense is a backend transaction and side-effect verifier for AI-generated and vibe-coded projects, with upgrade-context as a long-term system capability.

It converts repositories into evidence-backed engineering facts, then applies deterministic patterns and grounded insight layers for inspection and prioritization.

## Target Users

- Traditional backend engineers maintaining production services
- AI-assisted developers shipping fast first versions
- Vibe coding users who need post-generation backend verification

## Typical Problems RepoSense Helps Expose

- API write paths that touch database writes without clear transaction boundaries
- Side effects that trigger queues/events without visible closure
- Cache and state mutation signals spread across handlers/services
- Cross-surface changes that are hard to verify after AI-assisted edits
- Upgrade impact risk signals for maintainability and handoff

## Core Outputs

- Findings / Events / Evidence
- report artifacts (`report.json`, `report.html`)
- `event_graph.json`
- `api_surface.json`
- Context Pack and SARIF exports
- Quality Gate, Baseline & Diff, Run Manifest
- Learn local site
- Patterns and constrained AI insight outputs

## Current Capabilities

RepoSense can already provide conservative, evidence-backed detection for backend transaction and side-effect signals, and surface them in report, learn, and insight views.

## Why upgrade context matters

The first AI-generated backend version is increasingly easy to produce, but the second and third change rounds are where visibility breaks down.

Maintainers need to know existing side effects, transaction boundaries, evidence trails, and risk posture before the next AI-assisted upgrade.

RepoSense turns these into handoff-ready context through Context Pack, Baseline & Diff, Quality Gate, and Run Manifest.

## What RepoSense Does Not Do

- It does not guarantee full backend correctness.
- It does not guarantee all transactions are correct.
- It is not a default full-repository AI roaming tool.
- It is not a generic open-ended AI chat product.

## Road Ahead

- Verifier foundation (current OSS focus)
- Maintain Mode for upgrade and change-readiness workflows
- AI Insight Platform layers for guided explanations and prioritization
