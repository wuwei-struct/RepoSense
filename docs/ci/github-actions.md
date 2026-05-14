# RepoSense GitHub Actions CI

## Main Baseline Refresh
Workflow: `.github/workflows/reposense-main.yml`
- Push to `main` runs CI and writes baseline to branch `reposense-baselines` at `baselines/prod_lite/specs_v2/baseline.json`.
- Also uploads SARIF to Code Scanning.

## PR Baseline Gate
Workflow: `.github/workflows/reposense-pr.yml`
- Pull requests run CI; if baseline exists, run with `--baseline-in`.
- Uploads SARIF, creates or updates a PR comment with baseline diff summary.
- Uploads artifacts: `ci_summary.json`, `quality_gate.json`, `report.sarif.json`, `baseline_diff.md`.

## Usage
1. Ensure the repository supports `pip install -e .`.
2. Copy workflows into `.github/workflows/`.
3. Enable Code Scanning in repository security settings.
