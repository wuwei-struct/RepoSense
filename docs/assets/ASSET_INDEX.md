# Asset Index

All assets in this folder are tied to a real canonical local release demo for traceability.

Canonical source run policy:

- Generate with:
  - `powershell -ExecutionPolicy Bypass -File tools/release_demo.ps1`
- Use fixed path:
  - `.reposense_release_demo/current/`
- If old demo folders were archived or removed, regenerate canonical demo.

Current canonical source path:

- `.reposense_release_demo/current/`

## Screenshot Status (Release Materials)

| asset | target_path | source_page | status | purpose | privacy_note |
|---|---|---|---|---|---|
| report-overview (P0) | `docs/assets/screenshots/report-overview.png` | `.reposense_release_demo/current/report.html` -> Overview | captured | Show report summary cards and structure view | Crop out absolute local paths and browser chrome |
| backend-events (P0) | `docs/assets/screenshots/backend-events.png` | `.reposense_release_demo/current/report.html` -> Events | captured | Show backend event signals (`queue_dispatch`, `tx_boundary`, `db_op`, `api`) | Crop out absolute local paths and browser chrome |
| api-surface (P0) | `docs/assets/screenshots/api-surface.png` | `.reposense_release_demo/current/report.html` -> API Surface | captured | Show endpoint surface and mismatch area | Crop out absolute local paths and browser chrome |
| backend-verifier-report (P1) | `docs/assets/screenshots/backend-verifier-report.png` | `.reposense_release_demo/current/backend_verifier_report.md` | captured | Show verifier report sections (`API Surface Summary`, `Side-effect Map`, `Limitations`) | Crop out absolute local paths and browser chrome |
| demo-outputs (P1) | `docs/assets/screenshots/demo-outputs.png` | `.reposense_release_demo/current/` output file listing | captured | Show key generated outputs from one canonical run | Crop out absolute local paths and browser chrome |
| learn-overview (P1) | `docs/assets/screenshots/learn-overview.png` | `.reposense_release_demo/current/learn/index.html` | captured | Show non-empty Learn concepts/cases cards | Crop out absolute local paths and browser chrome |
| ai-risks-panel (P2) | `docs/assets/screenshots/ai-risks-panel.png` | `.reposense_release_demo/current/ai_risks/risks.md` or report AI Risks | captured | Show grouped risk panels / priority actions | Crop out absolute local paths and browser chrome |
| ai-explain-detail (P2) | `docs/assets/screenshots/ai-explain-detail.png` | `.reposense_release_demo/current/ai_explain/*/explain.md` or report Explain | captured | Show confirmed/inferred/unknown explain blocks | Crop out absolute local paths and browser chrome |

## Non-image assets

| asset | path | status | purpose |
|---|---|---|---|
| demo-outputs | `docs/assets/demo/demo-outputs.md` | ready | List key outputs from demo run |
| product-flow | `docs/assets/demo/product-flow.md` | ready | Facts -> Patterns -> Insights product flow |
| capture-plan | `docs/assets/screenshots/CAPTURE_PLAN.md` | ready | Capture targets and crop guidance |
| manual-capture-checklist | `docs/assets/screenshots/MANUAL_CAPTURE_CHECKLIST.md` | ready | Step-by-step capture instructions |

## Status values

- `captured`: PNG exists and reviewed.
- `pending_manual_capture`: Target is planned but PNG is not committed yet.
- `pending_data_fixture`: Screenshot requires a run with non-empty supporting data.
