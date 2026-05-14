# Asset Index

All assets in this folder are tied to a real local demo run for traceability.

Source run policy:

- Generate with:
  - `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out .reposense_demo_release_assets_current`
- Use latest run directory under:
  - `.reposense_demo_release_assets_current/<latest-run>/`
- If historical run folders were archived or removed, regenerate a new release asset run instead of relying on old paths.

Current run_dir used for this index update:

- `.reposense_demo_release_assets_current/run-1778741929-c53ae7d1`

## Screenshot Status (Release Materials)

| asset | target_path | source_page | status | purpose | privacy_note |
|---|---|---|---|---|---|
| report-overview | `docs/assets/screenshots/report-overview.png` | `report.html` -> Overview | pending_manual_capture | Show report summary cards and structure view | Crop out absolute local paths and browser chrome |
| backend-events | `docs/assets/screenshots/backend-events.png` | `report.html` -> Events | pending_manual_capture | Show backend event signals (`queue_dispatch`, `tx_boundary`, `db_op`, `api`) | Crop out absolute local paths and browser chrome |
| api-surface | `docs/assets/screenshots/api-surface.png` | `report.html` -> API Surface | pending_manual_capture | Show endpoint surface and mismatch area | Crop out absolute local paths and browser chrome |
| learn-overview | `docs/assets/screenshots/learn-overview.png` | `learn/index.html` | pending_manual_capture | Show non-empty Learn concepts/cases cards | Crop out absolute local paths and browser chrome |
| ai-risks-panel | `docs/assets/screenshots/ai-risks-panel.png` | `report.html` -> AI Risks | pending_manual_capture | Show grouped risk panels | Crop out absolute local paths and browser chrome |
| ai-explain-detail | `docs/assets/screenshots/ai-explain-detail.png` | `report.html` -> Explain detail | pending_manual_capture | Show confirmed/inferred/unknown explain blocks | Crop out absolute local paths and browser chrome |

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
