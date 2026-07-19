# Real Open-Source Repository Review Smoke

This protocol validates RepoSense against pinned, license-declared open-source backend repositories without executing target repository code.

It exercises the existing chain:

```text
Repository -> Facts -> Backend Verifier -> Patterns -> Code Health
           -> Permission Auditor -> AuthZ inferred matrix
           -> Repository Review -> Context Pack REVIEW -> Validation Summary
```

The protocol measures reproducibility, artifact completeness, evidence integrity, and calibration needs. It does not prove that a repository is safe or correct.

## Repository selection

Cases are declared in `tools/validation/real_repo_cases.json` and must have:

- a public repository URL;
- a clear license;
- a fixed 40-character commit SHA;
- a bounded repository size;
- backend capabilities that RepoSense has an opportunity to observe.

Expected capabilities are observation opportunities, not required finding counts. Smoke runs never follow a floating `main` or `master` reference after a case is configured.

The current cases cover a TypeScript NestJS backend and a Java Spring backend. Third-party source is cloned only into the ignored `.reposense_real_repo_smoke/workspaces/` directory and is never committed to RepoSense.

## Safety model

The harness does not run target repository code. It does not invoke target package installation, build, test, Maven, Gradle, npm, yarn, pnpm, or application scripts.

Only RepoSense static analysis commands and Git operations needed to obtain the configured commit are executed. Network access is opt-in through `-AllowNetwork`.

No `reposense.authz.yaml` is invented for an external repository. In the absence of a project-owned contract, AuthZ Matrix must remain `inferred_only` and require human confirmation.

## Run the protocol

Local no-network fixture smoke:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 `
  -RepoPath tests/fixtures/repos/review_demo_full `
  -CaseId local-review-demo
```

Run one existing local workspace without network access:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 `
  -CaseId nestjs-boilerplate `
  -SkipClone
```

Clone and run all enabled pinned cases:

```powershell
powershell -ExecutionPolicy Bypass -File tools/real_repo_review_smoke.ps1 `
  -AllowNetwork `
  -ContinueOnCaseFailure
```

Useful options:

- `-CaseId <id>` runs one configured case.
- `-RepoPath <path>` uses an existing local repository and does not clone.
- `-AllowNetwork` permits pinned clone/fetch operations.
- `-SkipClone` requires an existing workspace at the configured commit.
- `-KeepWorkspace` leaves managed clones in the canonical workspace path.
- `-ContinueOnCaseFailure` records a failed case and proceeds to the next one.

## Outputs

Canonical results are written to:

`.reposense_real_repo_smoke/current/`

Each case contains:

- `source-meta.json`: repository, license, commit, source mode, and size budget;
- `run/`: RepoSense run artifacts;
- `pipeline-meta.json`: stage exit codes, durations, and bounded output summaries;
- `validation.json` and `validation.md`: completeness, statistics, and evidence integrity;
- `triage-template.json`: unreviewed samples for manual calibration.

The root contains `summary.json`, `summary.md`, and `CURRENT_RUN.md`.

Before a new run, the previous full result is moved into the ignored local history. Only summaries and necessary metadata are copied into `docs/archive/local-artifacts/root-moved/`; third-party workspaces are not copied into documentation archives.

## Validation metrics

The validator records:

- pipeline completion, failed stage, duration, scanned files, unsupported signals, and parse warnings;
- required artifact availability;
- API, DB, transaction, queue, cache, pattern, Code Health, permission, inferred AuthZ, review decision, and human-review counts;
- suspected and confirmed status distribution;
- evidence file existence, positive and bounded line numbers, resolvable evidence IDs, repository-bound paths, and snippet budgets.

Evidence failures remain visible in `validation.json`; they are not silently converted to success.

## Manual triage

`triage-template.json` samples at most five items from each category:

- backend pattern;
- Code Health;
- permission risk;
- AuthZ inferred route;
- Human Review Required.

Allowed triage states are:

- `unreviewed`
- `plausible`
- `confirmed_by_source`
- `needs_business_context`
- `likely_false_positive`
- `duplicate`
- `unsupported`

Generated entries always start as `unreviewed`. Automation does not claim human confirmation.

## Workspace handling

All smoke workspaces and results are ignored by Git. To reclaim space, review `.reposense_real_repo_smoke/workspaces/`, `.reposense_real_repo_smoke/workspace-history/`, and `.reposense_real_repo_smoke/history/` manually. The harness itself uses non-destructive moves and does not delete these directories.

## Boundaries

- This protocol does not execute target repository code.
- It does not replace human code review or security review.
- It does not prove permission, transaction, or backend correctness.
- Inferred AuthZ routes are review aids, not authority contracts.
- A single sample must not be used to justify immediate rule changes.

Recorded results are maintained in [REAL_REPO_REVIEW_RESULTS.md](REAL_REPO_REVIEW_RESULTS.md).
