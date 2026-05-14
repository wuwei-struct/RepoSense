# Asset Index

All assets in this folder are tied to a real demo run for traceability.

Source run:

- `.reposense_demo_release_assets/run-1775037779-f9bd250b`
- Re-generate command:
  - `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out .reposense_demo_release_assets`

## Core assets

| Asset | Path | Status | Source page | Purpose | Used in |
| --- | --- | --- | --- | --- | --- |
| Report overview screenshot | `docs/assets/screenshots/report-overview.png` | pending_manual_capture | `report.html` | Show report summary/overview | README / Release notes |
| Learn overview screenshot | `docs/assets/screenshots/learn-overview.png` | pending_manual_capture | `learn/index.html` | Show concept/case browsing | README / docs |
| AI risks panel screenshot | `docs/assets/screenshots/ai-risks-panel.png` | pending_manual_capture | `report.html` (AI section) | Show grouped risks panel | README / release notes |
| AI explain detail screenshot | `docs/assets/screenshots/ai-explain-detail.png` | pending_manual_capture | `report.html` (Explain panel) | Show confirmed/inferred/unknown explain | README / docs |
| Demo outputs summary | `docs/assets/demo/demo-outputs.md` | ready | run artifacts | List key outputs from demo run | Release notes / docs |
| Product flow diagram | `docs/assets/demo/product-flow.md` | ready | static doc | Facts -> Patterns -> Insights flow | README / docs |
| Screenshot capture plan | `docs/assets/screenshots/CAPTURE_PLAN.md` | ready | capture guide | Capture targets and crop guidance | Maintainer workflow |
| Manual capture checklist | `docs/assets/screenshots/MANUAL_CAPTURE_CHECKLIST.md` | ready | capture guide | Step-by-step capture execution | Maintainer workflow |

## Update workflow

1. Re-run demo:
   - `powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1 -Out .reposense_demo_release_assets`
2. Update source run path in this file and `CAPTURE_PLAN.md` / `MANUAL_CAPTURE_CHECKLIST.md`.
3. Capture or refresh screenshot files listed above.
4. Verify links in README and release notes.
