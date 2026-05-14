# Screenshot Capture Plan

Source run should not be hardcoded to one stale folder.

- Generate source run locally:
  - `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out .reposense_demo_release_assets_current`
- Use latest run directory under:
  - `.reposense_demo_release_assets_current/<latest-run>/`
- If historical run folders were archived or removed, regenerate a new release asset run instead of relying on old paths.
- Capture from the latest valid demo run and record the actual run_dir in `docs/assets/ASSET_INDEX.md`.

Recommended screenshot targets (6):

Priority A (stable report pages):

1. `docs/assets/screenshots/report-overview.png`
   - Page: `report.html` -> Overview
   - Crop: Summary + structure cards area
2. `docs/assets/screenshots/backend-events.png`
   - Page: `report.html` -> Events
   - Crop: Backend event signals (`queue_dispatch`, `tx_boundary`, `db_op`, `api`)
3. `docs/assets/screenshots/api-surface.png`
   - Page: `report.html` -> API Surface
   - Crop: API surface summary + mismatch area
Priority B (requires generated data in the same run):

4. `docs/assets/screenshots/learn-overview.png`
   - Page: `learn/index.html`
   - Crop: Concept Navigator / Case Browser area
5. `docs/assets/screenshots/ai-risks-panel.png`
   - Page: `report.html` -> AI Risks section
   - Crop: Immediate attention / Needs review / Contextual watchlist
6. `docs/assets/screenshots/ai-explain-detail.png`
   - Page: `report.html` -> Explain detail
   - Crop: confirmed / inferred / unknown blocks

Notes:

- Avoid exposing local absolute paths (for example `E:/projects ide/RepoSense`).
- Prefer focused content-area crops over full-page screenshots.
- Keep text readable at normal README width.
- If `learn/index.html` is empty, mark learn screenshot as `pending_data_fixture`.
