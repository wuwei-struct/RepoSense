# Release Checklist

Use this checklist before creating a public release tag or release package.

## 1. Product Surfaces

- [ ] Demo chain runs end-to-end.
- [ ] `report.html` is generated and readable.
- [ ] `learn/index.html` is generated and readable.
- [ ] `patterns.json` / `pattern_summary.json` are generated.
- [ ] `ai_summary.*`, `ai_risks/*`, `ai_explain/*` generation is validated.
- [ ] Studio run page can open key views.

## 2. Testing and Gates

- [ ] Key focused tests pass.
- [ ] Full `python -m unittest -v` status is recorded.
- [ ] Warning status is recorded (including ResourceWarning trend).
- [ ] Production chain validated on at least one real run:
  - [ ] `ci run`
  - [ ] `verify --strict`
  - [ ] `gate`
  - [ ] `patch exports`
  - [ ] `run manifest`

## 3. Documentation

- [ ] README first screen is clear (value + boundary + quickstart).
- [ ] Quickstart command is copy-runnable.
- [ ] Docs entry points are complete and up to date.
- [ ] Grounded boundary language is consistent (Evidence-first, deterministic, Facts first).

## 4. OSS and Compliance

- [ ] License layering is confirmed (code/docs/case data policy).
- [ ] Third-party case data keeps minimal necessary snippets and `repo_ref`.
- [ ] No secrets/private tokens/private paths in tracked artifacts.
- [ ] Machine-specific assumptions are documented or removed.

See also: [OSS_PREP.md](OSS_PREP.md)

## 5. Release Artifacts

- [ ] `run_manifest.json` is stable and readable.
- [ ] `exports/context_pack.zip` is generated and valid.
- [ ] Demo output paths are stable and documented.
- [ ] Release assets list is explicit (if publishing artifacts):
  - [ ] report sample
  - [ ] patterns sample
  - [ ] ai summary sample
  - [ ] risks sample
  - [ ] manifest sample

## 6. Packaging Gate A

- [ ] The wheel contains Studio/Report/Learn web assets.
- [ ] The wheel contains all default rulesets, presets, runtime specs, concepts, and the SQLite initialization schema.
- [ ] Dependency-neutral target installation imports RepoSense from the installed target, not the source checkout.
- [ ] Installed Studio returns HTTP 200 for `/`, `/artifact-cards.js`, `/artifact-cards.css`, and `/api/runs`.
- [ ] Installed Learn loads the packaged concept graph.
- [ ] Installed default ruleset, preset, and specs complete a fixture CI scan.
- [ ] The wheel excludes tests, local workspaces, smoke outputs, temporary files, and secrets.

Run:

```bash
python tools/release/package_runtime_smoke.py --mode asset-and-target
```

## 7. Packaging Gate B

- [ ] The platform-specific wheelhouse lock is present and contains only the approved dependency closure.
- [ ] All wheel hashes verified; filename and metadata identities match.
- [ ] The wheelhouse contains no source distributions, installers, or extra packages.
- [ ] A fresh venv is created without system site packages.
- [ ] RepoSense and all dependencies install with `--no-index` and the controlled `--find-links` wheelhouse.
- [ ] `pip check` passes.
- [ ] The installed `reposense` console script and required CLI help commands pass.
- [ ] Installed Studio HTTP endpoints pass.
- [ ] Installed Learn concepts load from packaged resources.
- [ ] Installed default rules, presets, specs, and SQLite schema support the fixture scan.
- [ ] Installed review, Context Pack, manifest, SARIF, strict verify, and quality gate pass.
- [ ] Package identity checks prove that neither the source checkout nor the development venv was imported.

Gate B is a release blocker. Passing Gate A alone is not sufficient to publish.

Run:

```bash
python tools/release/offline_wheelhouse.py --verify
python tools/release/fresh_venv_runtime_smoke.py
```

See
[Offline Wheelhouse and Fresh-Venv Validation](release/OFFLINE_WHEELHOUSE_FRESH_VENV.md).

## 8. v0.2.0 Readiness Audit

The 2026-07-30 local audit at
`edb05dcfa08446fcfa5fe6bf163eba97260902c8` concluded
`READY_WITH_KNOWN_WARNINGS`. Packaging Gate A and Gate B passed, including two
fresh-venv offline runs, and the Studio run API privacy blocker is resolved.
This is approval to enter RC Preparation, not approval to publish.

- [Readiness Audit](release/V0_2_0_RELEASE_READINESS_AUDIT.md)
- [Release Plan](release/V0_2_0_RELEASE_PLAN.md)
- [Changelog Draft](release/V0_2_0_CHANGELOG_DRAFT.md)
- [Release Notes Draft](release/V0_2_0_RELEASE_NOTES_DRAFT.md)

Before an RC push:

- [ ] Refresh remotes and review divergence.
- [ ] Update/consolidate product version authority.
- [ ] Add explicit package license and README metadata.
- [ ] Build and inspect wheel and sdist.
- [ ] Rerun Gate A, Gate B, tests, demos, real-repository smoke, and Studio
      privacy checks against the RC commit.
- [ ] Record all known warnings in the RC notes.

## 9. Final Sign-off

- [ ] No schema changes (`schema_version` unchanged) unless explicitly planned.
- [ ] No grounded-boundary violations.
- [ ] Release notes include known limits and deferred items.
- [ ] Packaging Gate A and Packaging Gate B both pass.
