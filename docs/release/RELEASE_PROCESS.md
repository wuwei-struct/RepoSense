# Release Process

This document defines the standard release process for RepoSense.

## 1) Select Version

1. Choose a candidate version/tag (for example `v0.1.0`).
2. Confirm release scope against current shipped capabilities.
3. Record boundaries and known limitations early.

## 2) Run Demo

1. Run `tools/demo_run.ps1` from repository root.
2. Confirm required outputs are generated.
3. Record the source run directory for traceability.

## 3) Run Regression Checks

1. Run focused tests for changed areas.
2. Run representative docs/demo tests.
3. Run required chain checks when applicable:
   - `verify --strict`
   - `gate`
   - `patch exports`
   - `run manifest`
4. If needed, run `python -m unittest -v` for full regression.

## 4) Review Release Notes

1. Update/check `docs/release/RELEASE_NOTES_v0.1.0.md` (or target version file).
2. Ensure capabilities and boundaries are accurate.
3. Ensure known limitations are explicit.

## 5) Review Assets

1. Verify `docs/assets/ASSET_INDEX.md` is current.
2. Verify demo outputs/product flow docs are current.
3. Mark screenshot status clearly (completed vs pending manual capture).

## 6) Prepare Tag

1. Decide final tag name.
2. Confirm release candidate blockers are resolved.
3. Create tag only after checklist completion.

## 7) Publish Release

1. Publish GitHub release entry with release notes.
2. Attach/point to key artifacts and docs.
3. Ensure links are valid.

## 8) Publish Announcement

1. Use long and short announcement docs as source material.
2. Tailor channel-specific wording without changing factual scope.
3. Keep trust boundary statements intact.

## 9) Record Known Limitations

1. Keep a clear blockers/non-blockers section in candidate docs.
2. Track pending items as post-release follow-ups.
3. Do not claim unfinished items as completed.
