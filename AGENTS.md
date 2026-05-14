# AGENTS

## Project Positioning

RepoSense follows a layered contract:

Facts -> Patterns -> Insights

Default behavior is grounded and deterministic, with:

- Evidence-first
- Deterministic outputs
- Facts first, source on demand

## Working Directory and Interpreter Rules

- Run commands from repository root.
- If `.\.venv\Scripts\python.exe` exists, use it for all repo commands and tests.
- Default temp root for tests/CLI verification is `.tmp_test_runs\temp` (set `TMP/TEMP/TMPDIR` to this path).
- Windows interpreter priority:
1. `D:\安装\Python\python.exe`
2. `python`
3. `py -3`
- If no interpreter is available, stop and report. Do not claim validation was executed.

## Required Verification Chain

## Minimum regression

```bash
python -m unittest -v
```

## If changing Analysis / AI / export / manifest

Run at least:

1. Relevant focused tests
2. One real `ci run`
3. `verify --strict`
4. `gate`
5. `patch exports`
6. `run manifest`

## If changing Learn / Studio / README / Demo

Run at least:

1. Relevant focused tests
2. Demo script smoke (when demo/docs are touched)

## Definition of Done

- Do not claim "validated" or "passed" unless tests were actually executed.
- If tests were not run, do not claim "validated" or "passed".
- If gate result is `warn`, report `warn` (not `pass`).
- If only static review was done, explicitly state "not executed".
- Final report must include:
1. What changed
2. What was run
3. What passed
4. What was not run
5. Risks/boundaries

## Prohibited Actions

- Do not modify SQLite schema or `schema_version` unless explicitly required.
- Do not allow unrestricted full-repository source roaming for AI features.
- Do not fabricate verification or test results.
- Do not bypass grounded boundaries.
- Do not widen PR scope without explicit need.

## Suggested Report Format

Use a 6-part final report:

1. Change summary
2. Rules/capability changes
3. Artifact changes
4. Testing and validation
5. Risks and boundaries
6. Next steps
