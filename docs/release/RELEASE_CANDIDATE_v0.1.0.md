# Release Candidate v0.1.0

## Candidate Version

- Suggested candidate version: `v0.1.0`
- Suggested candidate tag: `v0.1.0`
- Positioning: first public showcase release for RepoSense

## Candidate Scope

Included scope for this candidate:

- Analysis
- Learn
- AI Insights
- Studio / Demo / Docs

## Completed Items

- Main chain is stable: `ci run -> verify --strict -> gate -> patch exports -> run manifest`.
- README productized with Quickstart and docs entry points.
- Release notes and announcement drafts are prepared.
- Demo assets index and capture plan are in place.
- AI capabilities available in current scope:
  - patterns
  - summary
  - risks
  - explain
  - constrained ask

## Pending Items

- Four core screenshots are still pending manual capture:
  - `docs/assets/screenshots/report-overview.png`
  - `docs/assets/screenshots/learn-overview.png`
  - `docs/assets/screenshots/ai-risks-panel.png`
  - `docs/assets/screenshots/ai-explain-detail.png`
- Optional: polish release page visuals after screenshot completion.

## Release Blockers / Non-Blockers

### Blockers

- Screenshot set not completed yet for release-quality presentation.
  - Status: pending manual capture.
  - Reason: external-facing release quality expectation.

### Non-Blockers

- Limited ask scope (summary/risk/evidence/flow only).
  - This is an intentional product boundary.
- Some heuristics remain in inferred/suspected outputs.
  - This is documented behavior, not a hidden defect.
- Residual test warning noise (for example some ResourceWarning cases).
  - Track and reduce, but does not block candidate packaging.

## Trust Boundaries (Must Stay Explicit)

- Evidence-first
- Deterministic
- Facts first, source on demand
- No unrestricted whole-repo AI roaming by default

## Linked Release Materials

- Demo quickstart: `docs/DEMO_QUICKSTART.md`
- OSS prep: `docs/OSS_PREP.md`
- Testing and gates: `docs/TESTING_AND_GATES.md`
- Asset index: `docs/assets/ASSET_INDEX.md`
- Release notes: `docs/release/RELEASE_NOTES_v0.1.0.md`
- Announcement long: `docs/release/ANNOUNCEMENT_LONG_zh.md`
- Announcement short: `docs/release/ANNOUNCEMENT_SHORT_zh.md`

## Suggested Release Condition

Recommend publishing `v0.1.0` after all four screenshots are captured and indexed, while keeping current product boundaries explicit in release notes.
