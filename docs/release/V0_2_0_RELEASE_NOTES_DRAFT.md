# RepoSense v0.2.0 Release Notes Draft

Draft for RC preparation. v0.2.0 has not been released.

## Why v0.2 Matters

RepoSense v0.2 is intended to turn repository facts into a more usable,
evidence-grounded review workflow. It adds prioritized review artifacts,
cross-file transaction context, messaging reliability signals, and a Studio
view that helps humans decide what to inspect first.

## New Capabilities

- Repository Review Report and Human Review Required.
- Code Health Radar, Permission Auditor, and AuthZ Matrix.
- Context Pack REVIEW for AI/human handoff.
- TypeORM operations, transaction correlation, and conservative cross-file
  alias/wrapper resolution.
- Queue/cache matching and queue retry/idempotency evidence correlation.
- NestJS route/guard/OpenAPI calibration.
- Studio Artifact Cards with validation and missing-artifact states.
- Pinned real-repository validation summaries.

## Quick Experience

From a source checkout:

```powershell
.\.venv\Scripts\python.exe -m reposense --help
powershell -ExecutionPolicy Bypass -File tools/review_demo.ps1
.\.venv\Scripts\python.exe -m reposense studio serve --port 8010
```

Open `http://127.0.0.1:8010` and select the canonical Review run. The Studio is
read-only with respect to generated artifacts.

## Studio and Review

The run page highlights Review Decision, Evidence Integrity, Strict Verify,
Quality Gate, Validation status, and Human Review Required. Recommended First
shows at most four available artifacts. Missing artifacts are shown as not
generated and do not receive fabricated links.

Public run APIs omit local repository, workspace, output, run, and log paths.
Artifacts are served through run-relative URLs.

## Packaging

The candidate wheel is expected to include Studio assets, rulesets, presets,
runtime specs, concepts, the SQLite initialization schema, and LICENSE.
Packaging Gate A checks archive and target-install behavior. Packaging Gate B
uses exact, hash-locked dependency wheels and a fresh venv for offline install,
`pip check`, CLI, Studio, Learn, and scan/review verification.

Current installed-wheel validation is specific to CPython 3.11 on Windows
AMD64. Other Python and operating-system combinations require separate
validation.

## Safety Boundaries

RepoSense reports statically observed evidence and conservative correlations.
It does not certify that a repository is safe, permissions are correct,
transactions always behave correctly, or consumers are idempotent. OpenAPI
security is contract evidence, not code Guard proof. Producer identity does not
prove consumer business idempotency. Human review remains required.

## Known Limitations

- Spring `SecurityFilterChain` inference is not implemented.
- Dynamic DI, reflection, and multi-hop TypeScript calls can remain unknown.
- No pinned real-repository sample currently contains explicit retry evidence;
  positive retry behavior is covered by synthetic fixtures.
- Prod-lite retains a known OpenAPI fixture coverage warning.
- Full tests pass but emit existing ResourceWarnings from test file handles.
- Wheel archives are not currently bit-for-bit reproducible.
- Remote state must be refreshed before RC push.

## Upgrading from v0.1.0

The RC will define the final installation command and compatibility notes.
Before upgrading, retain prior generated artifacts, review the v0.2 limitations,
and rerun analysis rather than assuming old and new review decisions are
identical. Do not treat this draft as a published package or tag.
