# Contributing to RepoSense

Thanks for contributing to RepoSense.

## Before You Start

RepoSense is built around a stable contract:

- Facts first
- Deterministic derivation
- Evidence-linked outputs

Truth source remains analysis facts and evidence references. Derived outputs (patterns/summary/risks/explain/ask) must stay grounded.

## Local Development Quick Path

1. Install environment:

```bash
.\.venv\Scripts\python.exe -m pip install -e .
```

2. Run one-command demo (Windows PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File tools/demo_run.ps1
```

3. Generate a run manually:

```bash
.\.venv\Scripts\python.exe -m reposense ci run --repo tests/fixtures/repos/java_api_queue_db_closure_min --out .reposense_ci --profile demo --with-context-pack --json
```

4. Open outputs:

- `report.html`
- `learn/index.html`

## Contribution Types

1. Rules / detectors
2. Events / graph construction
3. Learn / Concepts / Cases
4. AI derived outputs (patterns, summary, risks, explain, ask)
5. Studio / docs / demo workflows

## If You Change Rules

You must:

- Add or update fixtures.
- Add targeted tests (unit + smoke/regression as needed).
- Keep evidence references explainable and stable.
- Avoid "looks good" validation without reproducible checks.

## If You Change Learn or AI Outputs

You must:

- Keep outputs grounded to facts/evidence.
- Preserve explicit `confirmed / inferred / unknown` separation where required.
- Follow "Facts first, source on demand".
- Avoid unsupported narrative expansion without evidence.

## PR Checklist

PR structure should follow [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md).

- [ ] Ran related unit/integration tests
- [ ] Ran at least one real `ci run` when runtime path is affected
- [ ] Ran `python -m reposense verify <run_dir> --strict` when applicable
- [ ] Recorded `gate` result (`pass`/`warn`/`fail`) accurately
- [ ] Verified `run_manifest` updates when artifacts changed
- [ ] Updated README/docs entry points if docs or outputs changed

## Validation Chain Reference

Primary production chain:

1. `ci run`
2. `verify --strict`
3. `gate`
4. `patch exports`
5. `run manifest`

See [docs/TESTING_AND_GATES.md](docs/TESTING_AND_GATES.md) for details.

## Code of Conduct and License

- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [LICENSE](LICENSE)
