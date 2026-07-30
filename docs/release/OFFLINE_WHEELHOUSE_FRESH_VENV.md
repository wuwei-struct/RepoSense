# Controlled Offline Wheelhouse and Fresh-Venv Validation

## Purpose

Packaging Gate A proves that the RepoSense wheel contains its runtime assets
and works in a dependency-neutral target installation. Packaging Gate B adds a
stronger check: install RepoSense and its complete runtime dependency closure
into a new venv without network access or system site packages.

v0.2.0 has not been released. RepoSense remains version `0.1.0`, and the full
`PR-RELEASE-02` v0.2.0 release readiness audit must be repeated before RC
preparation.

## Target Boundary

The committed lock at `tools/release/wheelhouse.lock.json` targets:

- CPython 3.11
- Windows AMD64
- the `reposense-0.1.0-py3-none-any.whl` project wheel

It is a release-validation lock for that environment, not a universal
cross-platform dependency lock. A different Python ABI or platform requires a
separately reviewed lock refresh.

The locked dependency closure is:

- PyYAML
- requests
- certifi
- charset-normalizer
- idna
- urllib3

Every third-party wheel has an exact version, compatible wheel tag, metadata
identity, dependency relationship, and SHA-256 digest. Source distributions,
extra packages, VCS dependencies, and editable installs are rejected.

## Preparing the Wheelhouse

Preparation is the only network-enabled step. It is restricted to official
PyPI and binary wheels:

```powershell
.\.venv\Scripts\python.exe tools/release/offline_wheelhouse.py --prepare --allow-network
```

The command writes third-party wheels and reports below the ignored directory:

```text
.tmp_test_runs/release_wheelhouse/
```

Downloaded wheels, pip cache data, venv files, and smoke reports must never be
committed.

An existing lock is not refreshed implicitly. A deliberate dependency update
requires:

```powershell
.\.venv\Scripts\python.exe tools/release/offline_wheelhouse.py --prepare --allow-network --refresh-lock
```

Review the resulting versions, metadata, dependency closure, and hashes before
committing the lock.

## Offline Verification

After preparation, all remaining steps are network-free:

```powershell
.\.venv\Scripts\python.exe tools/release/offline_wheelhouse.py --verify
.\.venv\Scripts\python.exe tools/release/fresh_venv_runtime_smoke.py
```

Wheelhouse verification checks:

- every locked file exists and matches its SHA-256;
- filename and wheel metadata names and versions agree;
- wheel tags match the target environment;
- the dependency closure is complete;
- no extra wheel, source archive, or installer is present.

## Fresh-Venv Contract

The smoke script creates a new venv without `--system-site-packages`, builds the
RepoSense wheel, and installs everything with:

```text
pip install --no-index --find-links <wheelhouse> <reposense-wheel>
```

It runs from an external working directory and does not set a source
`PYTHONPATH`. It verifies:

- `pip check` and the installed dependency set;
- package locations are inside the fresh venv;
- the source checkout and original development venv are not imported;
- the console script and CLI help commands;
- Studio HTML, JavaScript, CSS, and runs API responses;
- Learn ConceptGraph loading with UTF-8 content;
- installed default rulesets, presets, specs, and SQLite initialization schema;
- fixture scan, reports, Context Pack, manifest, SARIF, strict verify, and gate.

Generated evidence is written to the ignored reports directory, including
`fresh_venv_smoke.json`, `fresh_venv_smoke.md`, `pip-freeze.txt`,
`pip-check.txt`, `package-locations.json`, and
`wheelhouse-verification.json`.

## Gate Interpretation

- Gate A: asset packaging and dependency-neutral target-install validation.
- Gate B: hash-locked dependency closure and fresh-venv offline validation.

Passing Gate B means the tested Windows/CPython environment can install and run
without the source checkout. It is not evidence that every supported platform
has been validated, and it is not approval to push, tag, or publish.
