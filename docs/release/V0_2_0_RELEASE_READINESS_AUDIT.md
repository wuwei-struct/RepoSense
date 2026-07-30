# RepoSense v0.2.0 Release Readiness Audit

## 1. Audit Scope

- Audit date: 2026-07-30
- Audited local `main`: `edb05dcfa08446fcfa5fe6bf163eba97260902c8`
- Audit branch: `pr-release-02c-v020-readiness-audit-rerun`
- Public OSS tag at audit time: `v0.1.0`
- Product/package version at audit time: `0.1.0`
- Audit mode: local, offline except for previously prepared and hash-locked wheels

This audit reruns release readiness after fixing packaged runtime assets,
fresh-venv offline installation, and Studio run API local-path disclosure. It
does not change product behavior, the product version, tags, or remote state.

Remote state was not refreshed during this local readiness audit.

## 2. Git / Version State

- `v0.1.0` points to `52f8b05808d109d4cff232331f5a611a9688e98a`.
- Local `main` is 26 commits ahead of `v0.1.0`.
- Local `main` is 17 commits ahead of the local `origin/main` reference.
- The working tree was clean before and after runtime validation.
- No feature branch was found unmerged into local `main`.
- No release wheel, wheelhouse, venv, smoke output, or workspace is tracked.

The product version is consistent at `0.1.0` in package metadata, runtime
imports, CLI output, and the audited wheel. Version authority is distributed,
not centralized: `pyproject.toml`, `reposense/__init__.py`, runtime artifact
producers, a CLI fallback, the Studio footer, packaging scripts, lock metadata,
and version-specific tests contain product-version literals. Artifact,
ruleset, SARIF, and schema versions are independent contracts and must not be
changed as part of a product-version update.

The recommended candidate is `0.2.0rc1`. RC Preparation must first establish a
single product-version authority or perform a reviewed synchronized update of
all product-version consumers.

## 3. Readiness Verdict

**READY_WITH_KNOWN_WARNINGS**

No release blocker was reproduced. RepoSense may enter
`PR-RELEASE-03 | v0.2.0 RC Preparation`. This verdict is not authorization to
publish, push, or tag. RC Preparation must complete the required metadata,
version, remote-divergence, and final-gate work listed below.

## 4. Blocking Issues

None observed in this audit.

The previously identified blockers are resolved:

| Blocker | Audit result |
| --- | --- |
| Wheel missing runtime assets | Resolved: 52/52 required assets packaged |
| No controlled fresh-venv offline install | Resolved: two consecutive Gate B runs passed |
| Studio run APIs disclosed local paths | Resolved: list and canonical detail leak count 0 |

## 5. Non-blocking Warnings

| Warning | Release treatment |
| --- | --- |
| Full tests emitted 626 `ResourceWarning` log lines, primarily from unclosed test file handles | Disclose and track cleanup; no test failed |
| Prod-lite gate returned `warn` because `api.missing_in_spec_count=3` | Disclose as the known fixture OpenAPI coverage gap |
| Gate B lock covers CPython 3.11 on Windows AMD64 only | Do not claim cross-platform installed-wheel validation |
| No pinned real repository contains statically explicit queue retry configuration | Rely on synthetic positive coverage and disclose the real-sample gap |
| Spring `SecurityFilterChain` inference is not implemented | Keep Spring OpenAPI-only authorization conclusions unknown |
| Remote state was not fetched or refreshed | Fetch and audit divergence before any RC push |
| Two equivalent wheel builds had different ZIP SHA-256 values | Do not claim bit-for-bit reproducible wheels |
| Product-version literals are distributed across runtime code and packaging gates | Consolidate or synchronously update during RC Preparation |
| Wheel includes `LICENSE`, but `pyproject.toml` lacks explicit license/readme metadata | Add and inspect public package metadata before RC publication |
| A historical archive document contains a repository-root absolute path; other path examples are explicitly illustrative | Remove or neutralize the historical absolute path during RC documentation cleanup |

## 6. Packaging Gate A / B

### Gate A

| Check | Result |
| --- | --- |
| `asset_packaging` | pass |
| `target_install_smoke` | pass |
| Wheel | `reposense-0.1.0-py3-none-any.whl` |
| Wheel size | 386,801 bytes |
| Wheel files | 243 |
| Runtime assets | 52/52 |
| Missing assets | 0 |
| Forbidden content | 0 |
| LICENSE | present |
| Installed target source shadowing | not observed |
| CLI help commands | 6 passed |
| Studio HTTP | `/`, JS, CSS, and `/api/runs` returned 200 |
| Learn/default rules/presets/specs/schema | pass |

An sdist was not checked because the optional build module was unavailable.
This does not invalidate the audited wheel, but RC Preparation must build and
inspect both wheel and sdist.

### Gate B

The committed lock verified six dependency wheels with exact versions and
SHA-256:

| Package | Version |
| --- | --- |
| certifi | 2026.7.22 |
| charset-normalizer | 3.4.9 |
| idna | 3.18 |
| PyYAML | 6.0.3 |
| requests | 2.34.2 |
| urllib3 | 2.7.0 |

Wheelhouse integrity, metadata identity, compatible tags, dependency closure,
and the no-sdist/no-extra-package policy passed. Two consecutive fresh-venv
runs passed:

- `--no-index` offline installation;
- no system site packages;
- `pip check`;
- installed package identity and source-shadow checks;
- console script and seven CLI checks;
- Studio, Learn, and installed resource loading;
- report, review, Context Pack, manifest, SARIF, strict verify, and gate.

This Gate B result is specific to CPython 3.11 on Windows AMD64.

## 7. Verified Capabilities

- Evidence-first Repository Review and Human Review Required outputs.
- Code Health Radar with deterministic heuristic boundaries.
- Permission Auditor and expected-vs-observed AuthZ Matrix.
- Spring transaction correlation with pinned real-repository evidence.
- TypeORM operations, TypeScript transaction correlation, and conservative
  cross-file alias/wrapper resolution.
- Queue/cache facts and conservative producer/consumer matching.
- Queue retry/idempotency correlation with synthetic positive coverage and
  clear producer-versus-consumer idempotency boundaries.
- NestJS route, guard, public-bypass, and OpenAPI correlation.
- Cross-language API link artifacts.
- Context Pack REVIEW and AI maintenance constraints.
- Studio Artifact Cards, status summaries, and private public-run payloads.
- Learn concept graph and local deterministic AI-derived artifacts.
- Four pinned real-repository offline validation cases.

## 8. CLI / UX

The following source-checkout commands exited successfully:

- `reposense --help`
- `reposense --version`
- `reposense review --help`
- `reposense health --help`
- `reposense authz --help`
- `reposense studio --help`
- `reposense learn --help`
- `reposense ai --help`

CLI version output was `0.1.0`. README Quickstart, Studio, Review Demo, release
demo, and Context Pack entry paths exist and match the CLI. No README statement
claims that v0.2.0 is already released.

## 9. Tests / Gates

- Full suite: 203 tests in 94.665 seconds.
- Passed: 202.
- Skipped: 1.
- Failures/errors: 0.
- Wall time: 95.162 seconds.
- Temp permission errors: 0.
- `compileall`: pass.
- `git diff --check`: pass.
- Release Demo strict verify: pass with no warnings.
- Review Demo strict verify: pass with no warnings.
- Patch exports: pass.
- Run manifest: pass.
- Demo gate: pass.
- Prod-lite gate: warn for the known OpenAPI fixture coverage gap.

No flaky failure was observed in this run. Resource warnings remain a cleanup
item.

## 10. Demo / Studio

Both canonical demos completed and rotated prior `current` directories into
ignored history without modifying tracked files.

The Review Demo generated report, Backend Verifier, Repository Review, Human
Review Required, Code Health, Permission, AuthZ, Transaction, TypeORM, Queue
Reliability, Context Pack REVIEW, ZIP, run manifest, and SARIF artifacts.

Studio validation against canonical run `run-1785373708-af7e4069` returned HTTP
200 for the page, JS, CSS, run list, detail, and an artifact. Across 226 run
list entries and the canonical detail:

- local-path leaks: 0;
- forbidden internal path fields: 0;
- Recommended First: 4;
- Artifact Groups: 9;
- missing artifacts with fabricated URLs: 0;
- residual port 8010 listeners after shutdown: 0.

The seven Review PNGs have valid signatures, are below 2 MB, and contain no PNG
text metadata chunks. Asset Index captured status and README references match.
No visual-layer Studio HTML/JS/CSS change occurred after the recorded manual
QA.

## 11. Real Repository Validation

All cases used existing ignored workspaces. RepoSense did not execute target
repository code.

| Case | Commit | License | Files | Evidence / strict / gate | Decision | Key observations |
| --- | --- | --- | ---: | --- | --- | --- |
| NestJS Boilerplate | `549cc37a3925ab87a4e61b45efb3b86d2d8e234e` | MIT | 471 | pass / pass / pass | REVIEW | 57 DB ops; 41 TypeORM writes; tx 0 covered, 10 uncovered, 31 unknown; 11 resolved and 11 ambiguous wrapper receivers |
| Spring PetClinic REST | `c7b5f5e9e90af2e5b94a40dd77b2a53dc33f67bd` | Apache-2.0 | 151 | pass / pass / pass | WARN | 68 DB ops; 46/46 transaction correlations covered explicitly |
| Ecommerce Store API | `147231b54ed8f8a7f3a0b5110db757a39650892c` | MIT | 739 | pass / pass / pass | REVIEW | 46 writes; 13 covered, 12 uncovered, 21 unknown; queue 3/3, matched 2; cache 45 |
| Spring Kafka Reactive | `46492f9147673513338505049eff09bc796dd166` | Apache-2.0 | 40 | pass / pass / pass | WARN | queue dispatch 3, consume 2, matched 2; 3 unresolved retry configs |

No real case contained statically explicit retry configuration. That absence is
reported as a real-repository coverage gap, not converted into synthetic
evidence. Spring `SecurityFilterChain` remains outside the implemented
correlation scope. OpenAPI-only evidence remains documentation/contract
evidence rather than guard implementation proof.

## 12. Documentation / Links

- 90 tracked Markdown files were checked locally.
- Missing relative Markdown links: 0.
- README image references resolve.
- Captured/pending screenshot status is consistent.
- English and Chinese README command paths align.
- No dead CLI command was observed.
- v0.2.0 is not described as published.

Tracked path review found illustrative interpreter/path examples and one
historical absolute repository-root entry in
`docs/archive/local-artifacts/MOVED_FROM_ROOT.md`. No username, credential, or
private home directory was present in that entry.

## 13. Claims Matrix

| Capability | Status | Recommended public wording | Supporting evidence | Limitations / prohibited wording |
| --- | --- | --- | --- | --- |
| Repository Review | SUPPORTED | Generates evidence-grounded repository review artifacts | Review Demo; repository review tests | Not a correctness or security certification |
| Human Review Required | SUPPORTED | Prioritizes items needing human confirmation | `human_review_required.md` | Not an automatic verdict |
| Code Health Radar | SUPPORTED_WITH_LIMITATIONS | Reports deterministic maintainability signals | Code Health docs/tests | Experimental score; not code quality proof |
| Permission Auditor | SUPPORTED_WITH_LIMITATIONS | Reports observed permission and guard gaps | Permission docs/tests | Missing evidence is not a proven vulnerability |
| AuthZ Matrix | SUPPORTED_WITH_LIMITATIONS | Compares expected and observed authorization signals | AuthZ docs/tests | Inferred matrices require owner confirmation |
| Spring transaction correlation | SUPPORTED_WITH_LIMITATIONS | Correlates explicit Spring transaction evidence | PetClinic 46/46 covered | Does not prove runtime rollback behavior |
| TypeORM DB operations | SUPPORTED_WITH_LIMITATIONS | Extracts conservative TypeORM read/write operations | TypeORM docs and two real cases | Dynamic receivers and SQL can remain unknown |
| TypeScript transaction correlation | SUPPORTED_WITH_LIMITATIONS | Correlates explicit local transaction scopes | TypeScript transaction tests | No complete TypeScript call graph |
| TypeORM alias resolution | SUPPORTED_WITH_LIMITATIONS | Resolves unique imports and one-hop wrappers | Alias tests and real validation | Dynamic DI, ambiguity, and multi-hop calls remain unresolved |
| Queue / Cache | SUPPORTED_WITH_LIMITATIONS | Detects supported queue/cache facts and static matches | Ecommerce validation | Runtime delivery and consistency are not proven |
| Queue Retry / Idempotency | SUPPORTED_WITH_LIMITATIONS | Correlates static retry, side effect, and guard evidence | Synthetic fixture and validation docs | No real explicit-retry positive case; producer identity is not consumer idempotency |
| OpenAPI / Guard correlation | SUPPORTED_WITH_LIMITATIONS | Separates code guard and OpenAPI contract evidence | Guard correlation docs/tests | OpenAPI security is not implementation proof |
| Route Decorator classification | SUPPORTED_WITH_LIMITATIONS | Rejects common non-route decorators conservatively | Classification fixture/tests | Dynamic decorator behavior can remain unknown |
| Cross-language links | SUPPORTED_WITH_LIMITATIONS | Emits static API link and mismatch evidence | Context Pack and demo artifacts | Repository boundaries and dynamic callers can be unresolved |
| Context Pack REVIEW | SUPPORTED | Packages review artifacts and maintenance constraints | Review Demo and strict verify | Does not grant unrestricted source access |
| Studio Artifact Cards | SUPPORTED_WITH_LIMITATIONS | Organizes generated review artifacts read-only | Visual QA and HTTP smoke | Desktop QA is not a browser/device matrix |
| Learn UI | SUPPORTED_WITH_LIMITATIONS | Renders packaged concepts and cases | Gate A/B Learn smoke | Small curated concept graph |
| Local AI outputs | SUPPORTED_WITH_LIMITATIONS | Produces local deterministic summaries/explanations from artifacts | Demo AI outputs | Not unrestricted autonomous reasoning |
| Real-repository validation | SUPPORTED_WITH_LIMITATIONS | Validated offline against four pinned public repositories | Real smoke summaries | Four samples do not prove ecosystem-wide accuracy |
| Packaging / fresh-venv install | SUPPORTED_WITH_LIMITATIONS | Wheel and offline install validated for the tested target | Gate A/B | CPython 3.11 Windows AMD64 only |
| Cross-platform packaging | NOT_YET_SUPPORTED | Other platforms require their own release validation | Platform-specific lock docs | Do not claim tested cross-platform installation |
| Replace code review | DO_NOT_CLAIM | Use as evidence and review support | Product boundary docs | Never claim replacement of human code review |
| Security guarantee | DO_NOT_CLAIM | Report observed static signals only | Grounded principles | Never claim a repository is secure or safe |
| Automatic repair | NOT_YET_SUPPORTED | No automatic source repair is offered | CLI surface audit | Do not promise automatic fixes |
| Complete business-intent understanding | DO_NOT_CLAIM | Require project-owner context for intent | Review limitations | Static evidence cannot prove complete business intent |

## 14. License / Third-party Content

- Project license: MIT.
- The wheel contains `reposense-0.1.0.dist-info/licenses/LICENSE`.
- Wheel metadata records `License-File: LICENSE`.
- `pyproject.toml` does not yet declare explicit license or README metadata.
- The four real repositories record URL, pinned commit, and MIT or Apache-2.0
  license metadata.
- No third-party workspace, source tree, wheel binary, venv, or smoke output is
  tracked.
- The wheelhouse lock contains metadata and hashes, not dependency binaries.

No license blocker was identified. A project NOTICE is not required for the MIT
project itself. A `THIRD_PARTY_NOTICES.md` file is optional but recommended if
future release assets redistribute third-party material; the current wheel and
source tree do not redistribute the four validation repositories.

## 15. Security / Privacy

Tracked secret scans produced only documentation wording, detector logic,
GitHub Actions secret placeholders, and synthetic fixtures. Token matches were
identifier/authentication semantics, not credentials. No private key,
credential, real API key, user home path, tracked `.env`, wheelhouse binary,
local database, log, workspace, or venv was found.

Studio public run APIs passed recursive path scanning. PNG text metadata did
not expose paths. Tracked test paths use synthetic identities such as `alice`
and are privacy regression fixtures.

## 16. Known Limitations

- Static analysis cannot prove runtime behavior, authorization correctness,
  transaction behavior, consumer idempotency, or business intent.
- Queue retry real-positive evidence is absent from the pinned public samples.
- Spring `SecurityFilterChain` correlation is not implemented.
- TypeORM and TypeScript correlation retains ambiguous and unknown cases.
- OpenAPI evidence remains separate from code guard proof.
- Gate B validation is platform-specific.
- Studio visual QA covers Chromium at 1440 x 900, not a device matrix.
- Build ZIP bytes are not bit-for-bit reproducible.

## 17. Required RC Preparation

1. Refresh remote references and audit divergence before pushing.
2. Create an RC branch from the approved local main.
3. Use `0.2.0rc1` and centralize or synchronously update product-version
   authority, runtime stamps, Studio footer, packaging scripts, lock metadata,
   and version tests.
4. Add explicit package license and README metadata.
5. Finalize changelog and release notes without overstating static evidence.
6. Neutralize the historical tracked absolute repository path.
7. Build and inspect both wheel and sdist.
8. Recreate the platform lock if the project wheel version changes.
9. Rerun Gate A, Gate B twice, full tests, demos, all real-repository smoke,
   Studio privacy checks, strict verify, and gates.
10. Record the Prod-lite warning and ResourceWarning trend.
11. Push only after remote refresh and final sign-off; tag only the approved
    commit.

## 18. Final Recommendation

Proceed to `PR-RELEASE-03 | v0.2.0 RC Preparation` with the warnings and
mandatory RC work above. Do not publish v0.2.0 from the audited `0.1.0`
metadata state. A final release decision must be made after RC versioning,
metadata updates, remote refresh, rebuilt artifacts, and the complete final
gate chain.
