# Studio Repository Review Workbench

## Purpose

Studio 2.0 turns the local Studio from a run and artifact viewer into a
Repository Review Workbench. It provides one controlled entry point for a
complete review, structured pipeline progress, native run summaries, and
stable navigation to every generated review area.

The Workbench has one bilingual shell for `en-US` and `zh-CN`. Locale changes
preserve the active run, Workbench tab, and analysis-form state and never rerun
analysis. Translation architecture and stable-data boundaries are documented in
[STUDIO_I18N.md](STUDIO_I18N.md).

The Workbench presents deterministic RepoSense artifacts. It does not execute
the target repository, replace human code review, or prove that a repository
is secure or correct.

## Analysis profiles

### Full Repository Review

`Full Repository Review` is the recommended Studio profile. It runs the
existing scan, backend verifier, pattern, Code Health, Permission/AuthZ,
transaction, queue reliability, Repository Review, Context Pack, SARIF,
strict verification, and quality-gate entry points. AuthZ Matrix uses
inferred-only mode unless the imported repository contains
`reposense.authz.yaml`.

Each stage uses fixed argument arrays and never executes target-repository
code. If a later stage fails, artifacts from completed stages remain available.

### Quick Scan

`Quick Scan` keeps the smaller facts, API, event graph, Context Pack, and
validation path. It skips review-only Code Health, Permission/AuthZ, pattern,
and Repository Review stages. A skipped capability is not a pass result.

## Pipeline Progress

The run API exposes browser-safe progress for these stable steps:

1. Preparing repository
2. Scanning facts
3. Building event graph
4. Detecting patterns
5. Analyzing code health
6. Reviewing permissions
7. Correlating transactions
8. Reviewing queue reliability
9. Building repository review
10. Building Context Pack
11. Strict verification
12. Quality gate
13. Finalizing run

Step status is one of `pending`, `running`, `passed`, `warned`, `failed`, or
`skipped`. Public progress contains safe summaries and artifact IDs, never
shell commands, tracebacks, repository paths, workspace paths, or log paths.

## Workbench navigation

Run details use ten stable views:

- Overview
- Human Review
- Architecture & API
- Transactions & Database
- Queue & Cache
- Permission & AuthZ
- Code Health
- Validation
- Context Pack
- Artifacts

Overview shows the Review Decision, Human Review Required count, pattern and
repository fact counts, Evidence Integrity, Strict Verify, and Quality Gate.
Recommended next actions are derived only from generated artifact availability;
Studio does not create new AI recommendations.

Domain views provide compact counts and the most relevant generated artifacts.
The Artifacts view preserves the existing Artifact Cards as the advanced/raw
layer instead of duplicating the server-side catalog in JavaScript.

## Availability semantics

Workbench values preserve three distinct states:

- `available` with value `zero`: the capability ran and produced a zero count.
- `missing` / `not generated`: no artifact exists for this run or profile.
- `malformed`: an artifact exists but Studio cannot safely parse its summary.

Studio does not convert missing or malformed artifacts into zero findings and
does not create links for missing files.

## Public API privacy boundary

`GET /api/runs`, `GET /api/runs/<run_id>`, profile metadata, and Pipeline
Progress pass through explicit public serializers. They may expose safe
repository labels, run-relative artifact paths, `/runs/...` URLs, and
`/api/...` URLs. They do not expose local repository, workspace, output, run,
or log paths.

Absolute paths remain internal to the local process and persisted local run
state. This boundary reduces accidental disclosure through screenshots,
browser extensions, copied responses, and logs.

## Read-only boundary

Workbench tabs organize existing analysis output. They do not change Scanner,
Pattern, Review, Permission, AuthZ, transaction, TypeORM, or queue semantics.
A `pass` status means the corresponding deterministic gate passed for the
observed artifacts; it does not prove complete business intent, authorization,
transaction safety, idempotency, or repository security.

## Legacy UI audit

Studio 2.0 is an in-place upgrade of the single routed Studio page. No second
legacy Studio HTML page, renderer, or route remains accessible. No file was
deleted in the i18n work because the audit found no unreferenced legacy asset
with sufficient evidence for safe removal. The generated static report, Learn
UI, artifact serving, screenshots, and Context Pack REVIEW remain supported and
have distinct responsibilities.
