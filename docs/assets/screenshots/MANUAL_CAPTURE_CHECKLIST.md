# Manual Capture Checklist

Canonical release screenshots must come from one fixed demo directory:

- Generate canonical demo:
  - `powershell -ExecutionPolicy Bypass -File tools/release_demo.ps1`
- Canonical source path:
  - `.reposense_release_demo/current/`
- If an old demo path was archived or removed, regenerate canonical demo instead of using stale run folders.
- Record capture status in `docs/assets/ASSET_INDEX.md`.
- Learn requirement:
  - `learn/index.html` must be non-empty (concept/case cards visible) before `learn-overview.png` can be marked `captured`.

## 1) report-overview.png (P0)

- Open: `.reposense_release_demo/current/report.html`
- Page: Overview
- Capture region: summary/overview cards (`findings/events/edges` + structure summary)
- Save to: `docs/assets/screenshots/report-overview.png`

## 2) backend-events.png (P0)

- Open: `.reposense_release_demo/current/report.html`
- Page: Events
- Capture region: backend event signals (`queue_dispatch`, `tx_boundary`, `db_op`, `api`)
- Save to: `docs/assets/screenshots/backend-events.png`

## 3) api-surface.png (P0)

- Open: `.reposense_release_demo/current/report.html`
- Page: API Surface
- Capture region: endpoint summary + mismatch area
- Save to: `docs/assets/screenshots/api-surface.png`

## 4) backend-verifier-report.png (P1)

- Open: `.reposense_release_demo/current/backend_verifier_report.md`
- Capture region: `API Surface Summary` / `Side-effect Map` / `Limitations`
- Save to: `docs/assets/screenshots/backend-verifier-report.png`

## 5) demo-outputs.png (P1)

- Open folder: `.reposense_release_demo/current/`
- Capture region: key output files list
- Save to: `docs/assets/screenshots/demo-outputs.png`

## 6) learn-overview.png (P1)

- Open: `.reposense_release_demo/current/learn/index.html`
- Capture region: Concepts / Cases area
- Save to: `docs/assets/screenshots/learn-overview.png`

## 7) ai-risks-panel.png (P2)

- Open: `.reposense_release_demo/current/ai_risks/risks.md`
  - or `.reposense_release_demo/current/report.html` AI Risks section
- Capture region: risk groups / priority actions
- Save to: `docs/assets/screenshots/ai-risks-panel.png`

## 8) ai-explain-detail.png (P2)

- Open: `.reposense_release_demo/current/ai_explain/*/explain.md`
  - or `.reposense_release_demo/current/report.html` Explain section
- Capture region: `confirmed / inferred / unknown`
- Save to: `docs/assets/screenshots/ai-explain-detail.png`

## Privacy / quality checks before commit

- Do not expose local absolute paths (for example `E:/projects ide/RepoSense`).
- Prefer tight content-area crop over full-page screenshot.
- Keep text readable.
- Avoid browser address bar, username labels, and system path areas.
- If local paths are visible, re-crop or mask before commit.
