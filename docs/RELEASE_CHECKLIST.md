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

- [ ] A controlled offline wheelhouse contains PyYAML, requests, and all transitive dependency wheels.
- [ ] A fresh venv installs RepoSense and dependencies only from that wheelhouse.
- [ ] The installed `reposense` console script passes CLI, Studio, Learn, and scan smoke checks.
- [ ] No source checkout or `PYTHONPATH` fallback is used.

Gate B is a release blocker. Passing Gate A alone is not sufficient to publish.

## 8. Final Sign-off

- [ ] No schema changes (`schema_version` unchanged) unless explicitly planned.
- [ ] No grounded-boundary violations.
- [ ] Release notes include known limits and deferred items.
- [ ] Packaging Gate A and Packaging Gate B both pass.
