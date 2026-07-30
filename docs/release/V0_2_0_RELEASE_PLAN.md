# RepoSense v0.2.0 Release Plan

This plan follows the 2026-07-30 local readiness verdict
`READY_WITH_KNOWN_WARNINGS`. v0.2.0 is not published.

## 1. Release Readiness Sign-off

- Review `V0_2_0_RELEASE_READINESS_AUDIT.md`.
- Accept the known warning disclosure.
- Confirm no new blocker has appeared since
  `edb05dcfa08446fcfa5fe6bf163eba97260902c8`.

## 2. RC Branch

- Refresh remotes before branch creation.
- Confirm local/remote divergence and audit open branches.
- Create a dedicated RC branch from the approved main commit.
- Do not rewrite validated feature or audit branch history.

## 3. Version Authority Update

Use `0.2.0rc1` for the first candidate.

Treat product version as a reviewed contract. Consolidate it or update all
product-version consumers together:

- `pyproject.toml`;
- `reposense/__init__.py`;
- CLI fallback and Studio footer;
- runtime artifact stamps in scan, graph, API, entrypoint, baseline, gate,
  upgrade, and cross-language paths;
- packaging smoke expectations;
- `wheelhouse.lock.json` project-wheel version;
- version-specific packaging tests;
- RC/release documentation.

Do not change independent schema, ruleset, SARIF, protocol, or validation
artifact versions.

## 4. CHANGELOG / README / Metadata

- Promote the reviewed changelog draft into the project changelog strategy.
- Finalize release notes with limitations.
- Update README version/install text only where the RC requires it.
- Add explicit package license metadata and `README.md` as package description.
- Neutralize the historical tracked absolute repository path.
- Keep Public OSS/commercial boundaries unchanged unless separately reviewed.

## 5. Wheel Build

- Build wheel and sdist from a clean RC worktree.
- Inspect filename, version, metadata, LICENSE, README metadata, and contents.
- Confirm 52/52 runtime assets and zero forbidden content.
- Record wheel and sdist hashes; do not claim bit-for-bit reproducibility
  unless independently proven.

## 6. Packaging Gate A / B

- Run Gate A asset-and-target validation.
- Refresh the controlled lock only as an explicit reviewed operation if the
  RC project wheel identity requires it.
- Verify all dependency hashes offline.
- Run Gate B twice in fresh venvs.
- Require `pip check`, installed CLI, Studio, Learn, scan/review, Context Pack,
  manifest, SARIF, strict verify, and quality gate to pass.

## 7. Tests / Demos / Real Repository Smoke

- Run focused release and packaging tests.
- Run the full unittest suite and compileall.
- Run Release Demo and Review Demo.
- Run patch exports, manifest, strict verify, Demo Gate, and Prod-lite Gate.
- Rerun all four pinned real repositories without executing third-party code.
- Recheck Studio API path privacy and screenshot references.

## 8. Remote Refresh

Before any push:

```text
git fetch --prune
git rev-list --left-right --count origin/main...main
git branch -r
```

Review remote divergence, tags, protected-branch requirements, and open release
work. The readiness audit deliberately did not refresh remote state.

## 9. Push

- Push the reviewed RC branch.
- Require remote CI, including Packaging Gate A configuration, to pass.
- Record any environment differences from local Windows Gate B.
- Do not force push.

## 10. Tag

- Tag only the signed-off RC/final commit.
- Prefer an annotated candidate tag such as `v0.2.0rc1`.
- Confirm the tag resolves to the exact built source.

## 11. GitHub Release

- Publish reviewed release notes and checksums.
- Attach only intended artifacts.
- Do not attach local wheelhouses, venvs, workspaces, smoke outputs, or logs.
- Describe supported scope and known limitations conservatively.

## 12. Post-release Install Verification

- Download release artifacts from the public release.
- Verify checksums and metadata.
- Install in a clean environment.
- Run CLI version/help, Studio HTTP, Learn, and a minimal scan.
- Confirm source archives contain no ignored local artifacts.

## 13. Rollback / Forward-fix

- Do not move or rewrite a published tag.
- If publication has not occurred, stop and correct the RC branch.
- If an RC is defective, publish a new RC tag.
- If a final release is defective, prefer a documented forward-fix patch.
- Withdraw release assets only for a security, license, or severe packaging
  issue and preserve an audit record.
