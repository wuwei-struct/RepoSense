# Code Health Radar

Code Health Radar is RepoSense's deterministic maintainability-risk layer for AI-assisted and vibe-coded codebases.

It is not a lint replacement and it is not a full code quality score. It highlights conservative, evidence-backed signals that often make later maintenance, review, or AI-assisted upgrades harder.

## What It Detects In The MVP

- CHD-001 Giant file / giant function: large or giant source files. Function-level detection is limited in this release.
- CHD-002 Debt comments: TODO, FIXME, HACK, XXX, workaround, and similar code comments.
- CHD-003 Type escape: TypeScript/JavaScript/Python type-system bypass signals such as `as any`, `@ts-ignore`, and `type: ignore`.
- CHD-004 Swallowed error: empty or value-returning catch/except blocks without logging, retry, compensation, or rethrow.
- CHD-005 High-risk file without test evidence: backend side-effect files where adjacent test evidence is not observed by conservative file-name matching.

## Outputs

Running Code Health Radar writes these run-level artifacts:

- `code_health.json`: full Code Health findings.
- `code_health_summary.json`: counts, top files, languages, and an experimental heuristic health score.
- `maintainability_risks.json`: medium/high findings normalized for Repository Review Mode.

## How To Run

```powershell
.\.venv\Scripts\python.exe -m reposense health scan <run_dir> --repo <repo_path> --json
```

If the run artifacts record a readable repository path, `--repo` can be omitted. In portable CI or release assets, passing `--repo` is the safer option.

## Repository Review Integration

Repository Review Mode consumes Code Health artifacts when they exist:

- `repository_review_report.json` sets `code_health_review.status` to `enabled`.
- `repository_review_report.md` includes a Code Health Review section.
- `human_review_required.md` includes medium/high Code Health risks that require human review.

If Code Health artifacts do not exist, Repository Review keeps the section as not available and does not invent findings.

## Context Pack Integration

When present before Context Pack generation, these artifacts are copied into:

- `context_pack/ARTIFACTS/code_health.json`
- `context_pack/ARTIFACTS/code_health_summary.json`
- `context_pack/ARTIFACTS/maintainability_risks.json`

`MAP/index.json` also records Code Health output entries.

## Limitations

- Conservative detection only.
- No AST-deep semantic analysis.
- No full duplicate logic clustering.
- No rule scatter or boundary pollution detection in this MVP.
- Test gap detection is inferred from file naming only.
- The health score is experimental and is not a correctness, safety, or maintainability proof.

## Planned Next Rules

- Duplicate logic clusters.
- Rule scatter.
- Boundary pollution.
- Responsibility inflation.
- Deeper function-level complexity heuristics.

