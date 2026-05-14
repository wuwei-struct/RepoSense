# Public Release Checklist

This checklist is for preparing a public RepoSense release.

## 1) Version / Tag

- [ ] Candidate version is decided (example: `v0.1.0`).
- [ ] Tag name is confirmed and consistent in release docs.
- [ ] Scope statement is aligned with current shipped capabilities.

## 2) Demo Verification

- [ ] Demo is executed from repo root with `tools/demo_run.ps1`.
- [ ] Demo run produces a complete run directory.
- [ ] Demo command and output paths are reproducible.
- [ ] See: `docs/DEMO_QUICKSTART.md`.

## 3) Key Outputs Verification

- [ ] `report.html` exists and opens.
- [ ] `learn/index.html` exists and opens.
- [ ] `patterns.json` exists.
- [ ] `ai_summary.md` exists.
- [ ] `ai_risks/risks.md` exists.
- [ ] At least one `ai_explain/*/explain.md` exists.
- [ ] `run_manifest.json` exists.

## 4) Docs Verification

- [ ] README Quickstart is present and runnable.
- [ ] Release notes are up to date: `docs/release/RELEASE_NOTES_v0.1.0.md`.
- [ ] Announcement docs are ready:
  - `docs/release/ANNOUNCEMENT_LONG_zh.md`
  - `docs/release/ANNOUNCEMENT_SHORT_zh.md`
- [ ] Docs entry points are cross-linked and not stale.
- [ ] See: `docs/TESTING_AND_GATES.md`.

## 5) Assets Verification

- [ ] Asset index is updated: `docs/assets/ASSET_INDEX.md`.
- [ ] Demo outputs doc is aligned: `docs/assets/demo/demo-outputs.md`.
- [ ] Product flow doc is aligned: `docs/assets/demo/product-flow.md`.
- [ ] Screenshot status is explicitly marked (done vs pending).
- [ ] Capture instructions are up to date if screenshots are pending.

## 6) OSS / License Verification

- [ ] OSS boundary review completed per `docs/OSS_PREP.md`.
- [ ] License guidance is consistent across README and docs.
- [ ] No private paths/secrets are included in public artifacts.

## 7) Known Limitations Review

- [ ] Current known limitations are listed and factual.
- [ ] Product boundaries are explicit:
  - Evidence-first
  - Deterministic
  - Facts first, source on demand
  - No unrestricted whole-repo AI roaming by default
- [ ] Non-blocking constraints are documented in release notes.

## 8) Release Notes / Announcement Ready

- [ ] Release notes text is finalized.
- [ ] Announcement long/short variants are finalized.
- [ ] Claims match current implementation status.

## 9) Post-Release Follow-ups

- [ ] Follow-up issues/tasks are created for pending items.
- [ ] Screenshot completion task is tracked if still pending.
- [ ] First wave user feedback collection plan is prepared.
