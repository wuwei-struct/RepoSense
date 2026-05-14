# Manual Capture Checklist

Source run should be generated from the latest local demo, not hardcoded to a stale run id.

- Generate source run:
  - `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out .reposense_demo_release_assets_current`
- Use latest run directory under:
  - `.reposense_demo_release_assets_current/<latest-run>/`
- If historical run folders were archived or removed, regenerate a new release asset run instead of relying on old paths.
- Record the actual run_dir used in `docs/assets/ASSET_INDEX.md`.
- Learn screenshot requirement:
  - `learn/index.html` must show non-empty concept or case cards.
  - If Learn is empty, do not mark `learn-overview.png` as captured; use `pending_data_fixture`.

## 1) report-overview.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/report.html`
- Page: Overview
- Capture region: summary/overview cards (findings/events/edges + structure summary)
- Save to: `docs/assets/screenshots/report-overview.png`

## 2) backend-events.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/report.html`
- Page: Events
- Capture region: backend event signal area (`queue_dispatch`, `tx_boundary`, `db_op`, `api`)
- Save to: `docs/assets/screenshots/backend-events.png`

## 3) api-surface.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/report.html`
- Page: API Surface
- Capture region: API surface summary + mismatch info
- Save to: `docs/assets/screenshots/api-surface.png`

## 4) learn-overview.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/learn/index.html`
- Capture region: Concept Navigator / Case Browser high-density area
- Save to: `docs/assets/screenshots/learn-overview.png`

## 5) ai-risks-panel.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/report.html`
- Navigate to AI Risks section
- Capture region: Immediate attention / Needs review / Contextual watchlist groups
- Save to: `docs/assets/screenshots/ai-risks-panel.png`

## 6) ai-explain-detail.png

- Open: `.reposense_demo_release_assets_current/<latest-run>/report.html`
- Open Explain detail panel
- Capture region: confirmed / inferred / unknown blocks
- Save to: `docs/assets/screenshots/ai-explain-detail.png`

## Privacy / quality checks before commit

- Do not expose local absolute paths (for example `E:/projects ide/RepoSense`).
- Prefer tight content-area crop over full-page screenshot.
- Keep text readable.
- Avoid browser address bar, username labels, and system path areas.
- If local paths are visible, re-crop or mask before commit.
