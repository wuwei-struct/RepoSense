# Evidence Location Contract

RepoSense code evidence must point to a real, reviewable source location. This contract is shared by Pattern generation, strict verification, Repository Review aggregation, and the real-repository smoke validator.

## Code evidence

A serialized code evidence reference must provide:

- `file`: a non-empty repository-relative path;
- `start_line`: an integer greater than or equal to 1;
- `end_line`: an integer greater than or equal to `start_line`;
- a source range that does not exceed the current source file;
- a snippet when the producing artifact requires one.

Internal indexed evidence may retain an absolute source path while a run is being built. It is valid only when it resolves inside the declared repository root, and it must be converted to a repository-relative path before being propagated into Pattern, Risk, or Review artifacts.

## Unknown locations

`0`, `-1`, and an invented first line are not valid representations of an unknown location. When RepoSense cannot resolve a real source location, it must not create a code evidence reference.

The producing item should instead:

- record `source_location_unavailable` in its limitations;
- remain or become `suspected` when location evidence is required for confirmation;
- preserve non-location identifiers, such as a supporting event ID, without presenting them as source coordinates.

This is why replacing `0` with `1` is prohibited: it would make an invalid reference look reviewable while pointing to unrelated source.

## Stable validation errors

- `EVIDENCE_FILE_MISSING`
- `EVIDENCE_ABSOLUTE_PATH`
- `EVIDENCE_LINE_START_INVALID`
- `EVIDENCE_LINE_RANGE_INVALID`
- `EVIDENCE_LINE_OUT_OF_RANGE`
- `EVIDENCE_SNIPPET_MISSING`

Each strict verification error identifies the artifact, item, error code, and reason.

## Strict verification coverage

`reposense verify <run_dir> --strict` validates indexed evidence and structured evidence locations in available run artifacts, including:

- findings in `report.json` and indexed evidence in `detections.sqlite`;
- Event Graph references through their canonical `E*` evidence;
- `patterns.json`;
- `ai_risks/risks.json`;
- `code_health.json` and `maintainability_risks.json`;
- `permission_risks.json`;
- `authz_matrix_diff.json`;
- `repository_review_report.json`;
- `review_risk_matrix.json` when it contains evidence references.

Non-strict verification reports location problems as warnings for compatibility. Strict verification reports them as errors and exits non-zero.

## Boundary

A valid source location proves only that the evidence is resolvable. It does not prove that the associated finding, transaction conclusion, permission conclusion, or review decision is semantically correct.
