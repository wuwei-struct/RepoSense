# Screenshot Capture Plan

Use one canonical release demo source for all screenshots.

- Generate canonical demo:
  - `powershell -ExecutionPolicy Bypass -File tools/release_demo.ps1`
- Canonical run path:
  - `.reposense_release_demo/current/`
- If old demo folders were archived, regenerate canonical demo instead of using stale paths.

Recommended screenshot targets (8):

P0 (core report pages):

1. `docs/assets/screenshots/report-overview.png`
   - Open: `.reposense_release_demo/current/report.html` -> Overview
2. `docs/assets/screenshots/backend-events.png`
   - Open: `.reposense_release_demo/current/report.html` -> Events
3. `docs/assets/screenshots/api-surface.png`
   - Open: `.reposense_release_demo/current/report.html` -> API Surface

P1 (release materials):

4. `docs/assets/screenshots/backend-verifier-report.png`
   - Open: `.reposense_release_demo/current/backend_verifier_report.md`
5. `docs/assets/screenshots/demo-outputs.png`
   - Open: `.reposense_release_demo/current/` (output file list view)
6. `docs/assets/screenshots/learn-overview.png`
   - Open: `.reposense_release_demo/current/learn/index.html`

P2 (AI materials):

7. `docs/assets/screenshots/ai-risks-panel.png`
   - Open: `.reposense_release_demo/current/ai_risks/risks.md` or report AI Risks panel
8. `docs/assets/screenshots/ai-explain-detail.png`
   - Open: `.reposense_release_demo/current/ai_explain/*/explain.md` or report Explain area

Notes:

- Avoid exposing local absolute paths (for example `E:/projects ide/RepoSense`).
- Prefer focused content-area crops over full-page screenshots.
- Keep text readable at normal README width.
- If `learn/index.html` is empty, do not mark `learn-overview.png` as captured.
