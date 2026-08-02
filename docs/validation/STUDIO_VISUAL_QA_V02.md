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

## Studio 2.0 Workbench QA record

- Date: 2026-07-31
- RepoSense commit under test: working tree based on `08e86d9a87f25a23638d7eaff80acc134f5f8943`
- Branch: `pr-studio-05-workbench-foundation`
- Browser: user-confirmed manual browser session; product/version not reported
- Viewport: 1440 x 900 review target
- Target run: `run-1785495179-79b715c3`
- Manual visual QA result: passed

The user confirmed the Home page, Analyze Repository profile selector,
Pipeline Progress, Recent Runs, all ten Workbench tabs, Artifact Cards,
missing/zero states, console, responsive layout, and local-path privacy. The
target Full Repository Review completed all 13 steps; its Review Decision was
`WARN` and its Quality Gate was `warn`, and neither state was presented as a
safety guarantee.

Automated HTTP checks for the same run returned 200 for the app shell, four new
Workbench JS/CSS assets, profile API, run list, run detail, and a generated
artifact. Recursive public-payload scanning found no local path leak,
Recommended First contained four items, and missing artifacts had no fabricated
URL.

The seven existing screenshots remain historical Studio Artifact Cards assets
and require a later refresh because the Workbench changes the product shell
substantially. The exact browser product/version was not supplied with the
manual confirmation and remains a documentation limitation.

## Studio 2.0 bilingual QA record

- Date: 2026-07-31
- RepoSense commit under test: working tree based on `b8f8f2760f5aca34e20ed2598bdc8912e152e636`
- Branch: `pr-studio-06a-i18n-foundation`
- Browser and viewport: Chromium through the Codex in-app browser, 1440 x 900,
  with user confirmation against the same local Studio URL
- Locales: `zh-CN` and `en-US`
- Target run: `review_demo_full` / `run-1785495179-79b715c3`
- Result: pass; the user explicitly confirmed the Chinese and English visual check

Home, Analyze Repository, both profiles, pipeline progress, Recent Runs, all ten
Workbench tabs, Artifact Cards, and available/missing/warn/failed states were
checked in both locales. Language switching was immediate and retained the
selected profile, local-path input, active run, and Workbench tab. Chinese text
rendered without mojibake; neither locale showed horizontal overflow at the
target viewport, and no browser-console error was observed. Recursive API checks
found no local-path leak in run-list or run-detail payloads.

No visual defect required a CSS or layout change during this QA pass. The seven
existing English screenshots are historical; updated English and Chinese Studio
2.0 screenshots remain a follow-up asset task.
