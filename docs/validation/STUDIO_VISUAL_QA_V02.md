# Studio Visual QA v0.2

## Validation record

- Date: 2026-07-30
- RepoSense commit under test: `c5f1110ff39915df5881eb449a15896130d8ce52`
- Branch: `pr-studio-03-visual-qa-review-screenshots`
- Browser: Chromium through the Codex in-app browser, with user confirmation against the same local Studio URL
- Viewport: 1440 x 900
- Target run: `run-1785373708-af7e4069`
- Source: canonical `.reposense_review_demo/current/`
- Manual visual QA result: passed

The user explicitly confirmed the visual check after the Studio service was restarted in the browser-visible host environment.

## Checklist

| Area | Result | Notes |
|---|---|---|
| ZIP upload | pass | Entry remains visible. |
| Local repository path | pass | Entry remains visible. |
| Run list | pass | The canonical Review Demo snapshot is selectable. |
| Run Status Header | pass | Review Decision, Evidence Integrity, Strict Verify, Quality Gate, Validation Status, and Human Review Required are distinct. |
| Conservative status wording | pass | `not generated` remains distinct from pass; no safe/secure claim is shown. |
| Recommended First | pass | Four available cards appear in the required stable order. |
| Artifact groups | pass | Review dimensions and Advanced / Raw grouping are present. |
| Missing artifacts | pass | Missing artifacts have no fabricated links. |
| Open links | pass | Available artifact links resolve to the selected run. |
| Copy relative path | pass | Relative paths are exposed without local absolute paths. |
| Responsive layout | pass | No material horizontal overflow or card overlap at 1440 x 900. |
| Browser console | pass | No Studio application error was observed; a missing favicon request is non-functional and out of scope. |

## Status interpretation

The canonical artifacts passed external strict verification before Studio registration. The Studio snapshot did not contain persisted Evidence Integrity or Strict Verify summary artifacts, so those cards correctly displayed `not generated` rather than pass. Quality Gate displayed pass from its generated artifact, and Review Decision displayed WARN / needs attention.

These states were reviewed as display behavior only. This visual check does not prove repository safety, authorization correctness, transaction correctness, or complete validation coverage.

## Issues and resolution

The first Studio process was started inside a restricted execution environment. Terminal requests returned successfully, but the user browser could not reach the service and remained loading. Restarting the unchanged Studio command in the browser-visible host environment resolved access. This was an execution-environment issue; no Studio UI or API code change was required.

No layout, card, API, or artifact-catalog defect requiring a product change was found during this QA pass.

## Screenshot record

The following PNG files were captured from the canonical run and reviewed for readability, privacy, and source fidelity:

- `docs/assets/screenshots/studio-review-panel.png`
- `docs/assets/screenshots/repository-review-report.png`
- `docs/assets/screenshots/human-review-required.png`
- `docs/assets/screenshots/code-health-summary.png`
- `docs/assets/screenshots/permission-risk-report.png`
- `docs/assets/screenshots/authz-matrix-report.png`
- `docs/assets/screenshots/context-pack-review-section.png`

All screenshots omit browser chrome and local absolute paths. No detection counts were edited.

## Remaining limitations

- This QA covers the 1440 x 900 desktop layout; it is not an exhaustive browser/device matrix.
- Markdown and JSON screenshots use read-only previews of canonical artifacts.
- Studio does not register arbitrary external run directories automatically; the canonical run was copied unchanged into the ignored Studio workspace for display.
- Visual QA validates presentation and navigation only, not the correctness of analysis findings.
