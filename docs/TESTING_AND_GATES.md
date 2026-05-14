# Testing and Gates

RepoSense is an artifact-chain project. Validation is not only unit tests, but also run/gate/manifest contract checks.

## Runtime Defaults

- Prefer project interpreter: `.\.venv\Scripts\python.exe` (when present).
- Prefer project temp root: `.tmp_test_runs\temp` by setting:
  - `TMP=.tmp_test_runs\temp`
  - `TEMP=.tmp_test_runs\temp`
  - `TMPDIR=.tmp_test_runs\temp`

## Core Production Chain

1. `ci run`
2. `verify --strict`
3. `gate`
4. `patch exports`
5. `run manifest`

Typical commands:

```bash
python -m reposense ci run --repo <repo_path> --out .reposense_ci --profile demo --with-context-pack --json
python -m reposense verify <run_dir> --strict
python -m reposense gate <run_dir> --gate presets/gates/prod_lite.json
python -m reposense patch exports <run_dir>
python -m reposense run manifest <run_dir> --json
```

## Demo Script

For product-level smoke validation (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1
```

This should produce report/learn/patterns/summary/risks/explain/manifest outputs.

## Learn Tests

Focus areas:

- Learn UI routes
- Learn snapshots
- learn serve smoke

## AI Tests

Focus areas:

- pattern rules/engine/schema
- summary engine/render/cli/integration
- drilldown selector/engine/cli/integration
- explain engine/render/cli/integration
- risks engine/ranker/render/cli/integration
- ask classifier/engine/render/cli/integration

## Studio/UI Snapshot Tests

Focus areas:

- studio AI section rendering
- route/accessibility of AI cards
- snapshot stability for empty/filled states

## Reporting Rules

- Report exactly what was run.
- If not run, say "not run".
- If gate is `warn`, report `warn`.
- Do not claim full regression unless it was executed.
