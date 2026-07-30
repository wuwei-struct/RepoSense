# Packaging Runtime Assets

## Status

This document describes Packaging Gates A and B for the local v0.2.0
development baseline. RepoSense remains version `0.1.0`; v0.2.0 has not been
released. Gate B has been validated locally for CPython 3.11 on Windows AMD64,
but the full release readiness audit must still be repeated before RC
preparation.

## Original Blocker

The setuptools configuration originally discovered only `reposense*` Python
packages. The source checkout worked because several modules walked from
`__file__` to repository-root directories, but the built wheel omitted:

- `webui/`
- `rulesets/`
- `presets/`
- `specs/`
- `reposense/shared/concepts/concepts.json`
- `sql/schema_v1.sql`

The missing files affected Studio, generated Report/Learn styles, default
profiles and gates, runtime specs, the Learn concept graph, and SQLite database
initialization.

## Packaging Strategy

Runtime assets keep one canonical source location. Setuptools installs
repository-root assets as distribution data files under:

```text
share/reposense/webui/
share/reposense/rulesets/
share/reposense/presets/
share/reposense/specs/
share/reposense/sql/
```

The package-owned concept graph remains at:

```text
reposense/shared/concepts/concepts.json
```

No persistent build-time copy is committed. Tests, docs, screenshots, local
workspaces, smoke outputs, databases, logs, and temporary files are not
included.

## Runtime Resolver

`reposense/runtime_resources.py` defines the shared runtime asset manifest and
all resource lookup APIs.

Installed distributions are resolved from `importlib.metadata` file records.
Package-owned concepts use `importlib.resources`. A source checkout may use the
canonical directories relative to the resolver module, never the current
working directory.

Installed mode does not search an unrelated source checkout when distribution
resources are missing. Missing resources raise an error containing the
resource ID and missing relative file, without exposing a private machine path.

Consumers include:

- Studio static serving
- Report and Learn static asset copying
- default rulesets and profiles
- budget and gate presets
- runtime specs and case schemas
- Learn concepts
- SQLite initialization schema

Explicit user-supplied ruleset and spec paths retain their existing behavior.

## Packaging Gate A

Run:

```powershell
.\.venv\Scripts\python.exe tools/release/package_runtime_smoke.py --mode asset-and-target
```

The command stages only packaging inputs under the ignored
`.tmp_test_runs/package_runtime_smoke/` directory and then:

1. builds a wheel with `pip wheel --no-deps --no-build-isolation`;
2. inspects wheel metadata and every required manifest asset;
3. rejects forbidden local/test content;
4. installs the wheel with `pip install --no-deps --target`;
5. runs Python in isolated mode from outside the repository root;
6. confirms RepoSense imports from the target installation;
7. checks CLI help, Learn concepts, runtime specs, and a default-profile scan;
8. checks installed Studio HTTP endpoints.

The generated ignored summaries are:

- `package_runtime_smoke.json`
- `package_runtime_smoke.md`

Gate A intentionally reports:

```text
dependency-neutral target smoke passed; fresh-venv offline dependency smoke pending
```

## Gate A Versus Gate B

Gate A verifies wheel layout, resource resolution, and installed module wiring.
It intentionally uses the current interpreter's already installed runtime
dependencies. It is not a fresh-venv dependency test.

Packaging Gate B uses a controlled offline wheelhouse for:

- PyYAML
- requests
- certifi
- charset-normalizer
- idna
- urllib3

Gate B creates a fresh venv without system packages, installs only with
`--no-index`, runs `pip check`, and repeats CLI, Studio, Learn, scan, review,
strict verification, and quality-gate checks without a source fallback.

Run the locked, offline validation with:

```powershell
.\.venv\Scripts\python.exe tools/release/offline_wheelhouse.py --verify
.\.venv\Scripts\python.exe tools/release/fresh_venv_runtime_smoke.py
```

The committed lock is specific to CPython 3.11 on Windows AMD64. Downloaded
wheels, the fresh venv, and reports remain under ignored `.tmp_test_runs/`
paths. See
[Offline Wheelhouse and Fresh-Venv Validation](OFFLINE_WHEELHOUSE_FRESH_VENV.md)
for preparation, verification, and lock-refresh procedures.

Local Gate B completion removes the packaging-specific blocker. It does not
replace the full release readiness audit, remote CI execution, version update,
tagging, or public release approval.

## Boundaries

Packaging these assets does not change scanner, review, rule, transaction,
messaging, Context Pack, Run Manifest, or SQLite schema semantics. It only makes
the existing source-checkout runtime assets available to an installed wheel.
