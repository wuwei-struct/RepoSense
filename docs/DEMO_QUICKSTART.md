# Demo Quickstart

This document explains the one-command demo flow for RepoSense.

## One Command

Run from repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1
```

## What the Script Does

`tools/demo_run.ps1` executes a deterministic demo pipeline:

1. ENV check
- Resolve Python interpreter in this order:
  - `D:\安装\Python\python.exe`
  - `python`
  - `py -3`
- Print interpreter path and version.

2. CI_RUN
- `python -m reposense ci run --repo <fixture> --out <out> --profile demo --with-context-pack --json`
- Build Learn output into `<run_dir>/learn/index.html`.

3. AI_PATTERNS
- `python -m reposense ai patterns <run_dir> --json`

4. AI_SUMMARY
- `python -m reposense ai summary <run_dir> --json --markdown`

5. AI_RISKS
- `python -m reposense ai risks <run_dir> --json --markdown`

6. AI_EXPLAIN
- Read `<run_dir>/patterns.json`
- Auto-select one pattern by priority:
  - severity: `high > medium > low`
  - status: `confirmed > suspected`
  - confidence desc, then `pattern_id` asc
- Run `reposense ai explain` for that target.
- If selected target is `suspected`, add `--with-drilldown`.

7. PATCH_EXPORTS
- `python -m reposense patch exports <run_dir>`

8. RUN_MANIFEST
- `python -m reposense run manifest <run_dir> --json`

## Default Demo Fixture

- `tests/fixtures/repos/java_api_queue_db_closure_min`

## Default Output Root

- `.reposense_demo`

Latest run directory is printed by the script, for example:

- `.reposense_demo/run-...`

## Required Artifacts Checked by Script

- `<run_dir>/report.html`
- `<run_dir>/learn/index.html`
- `<run_dir>/patterns.json`
- `<run_dir>/ai_summary.md`
- `<run_dir>/ai_risks/risks.md`
- at least one `<run_dir>/ai_explain/*/explain.md`
- `<run_dir>/run_manifest.json`

## Common Failures

- `[ERROR][ENV]`:
  - Python not found or fixture path missing.
- `[ERROR][CI_RUN]`:
  - scan chain failed or run_dir not resolved from JSON output.
- `[ERROR][AI_PATTERNS|AI_SUMMARY|AI_RISKS|AI_EXPLAIN]`:
  - corresponding AI stage failed.
- `[ERROR][PATCH_EXPORTS|RUN_MANIFEST]`:
  - export/manifest stage failed.

## Use Your Own Repository

```powershell
powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Repo <your_repo_path> -Out .reposense_demo_custom
```
