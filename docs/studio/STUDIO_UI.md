# RepoSense Studio UI

## What it is

RepoSense Studio is a local Studio UI for interactive repository analysis.

## Start Studio

```powershell
.\.venv\Scripts\python.exe -m reposense studio serve --port 8010
```

Open:

`http://127.0.0.1:8010`

## Current workflow

1. Choose one import mode:
   - Upload a repository ZIP, or
   - Analyze a local repository path.
2. Start analysis.
3. Wait for run completion.
4. Open generated outputs:
   - `report.html`
   - Learn UI
   - SARIF
   - Context Pack
   - `run_manifest.json`
   - backend verifier report
   - local AI-derived outputs if generated

## Analyze a local repository path

1. Start Studio.
2. Enter a local repository path in `Analyze local repository path`.
3. Click `Analyze local path`.
4. Configure run profile/ruleset/specs and start analysis.
5. Track runs and open artifacts from the same run list.

Boundary notes:

- Local path analysis is local-only in Studio.
- RepoSense reads repository files for static analysis and does not execute repository code.
- Browser flow does not upload the full local directory to a hosted cloud service by default.

## What Studio does not do yet

- It does not currently expose a browser folder picker for local directories.
- It does not upload data to a hosted cloud service by default.
- It does not replace CLI workflows.
- It does not guarantee backend correctness.

## CLI alternative

For local directory analysis:

```powershell
.\.venv\Scripts\python.exe -m reposense ci run --repo <repo-path> --out .reposense_runs --profile demo --with-context-pack
```

Then open:

```powershell
.\.venv\Scripts\python.exe -m reposense show <run_dir> --open
```

## Implementation references

- `webui/studio/index.html`
- `reposense/studio/server.py`
- `reposense/studio/jobs.py`
- `reposense/cli.py`
