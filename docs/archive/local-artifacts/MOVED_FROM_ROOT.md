# Moved From Root

This migration was executed in **non-destructive mode**.

- Only `Move-Item` was used for artifact relocation.
- No delete command was executed in this migration step.
- Files that were already missing were not recreated.
- Current OSS cleanup continues from the present workspace state.

## Moved files/directories

| original_path | new_path | reason |
|---|---|---|
| `.reposense_demo_localvenv` | `docs/archive/local-artifacts/root-moved/.reposense_demo_localvenv` | Local demo output should not stay in root for OSS release prep |
| `.reposense_demo_localvenv_fix` | `docs/archive/local-artifacts/root-moved/.reposense_demo_localvenv_fix` | Local demo output should not stay in root for OSS release prep |
| `.reposense_demo_prod05` | `docs/archive/local-artifacts/root-moved/.reposense_demo_prod05` | Local demo output should not stay in root for OSS release prep |
| `.reposense_demo_release_assets` | `docs/archive/local-artifacts/root-moved/.reposense_demo_release_assets` | Local demo output should not stay in root for OSS release prep |
| `ROADMAP.md` | `docs/archive/local-artifacts/root-moved/ROADMAP.md` | Legacy root roadmap moved out of root; docs roadmap is canonical under `docs/roadmap/ROADMAP.md` |
| `learn/` | `docs/archive/local-artifacts/root-moved/learn/` | Root-level learn static resources moved out of root; source code lives under `reposense/learn` |

## Already missing before migration

| original_path | observed_status | note |
|---|---|---|
| `RepoSense_PROJECT_SUMMARY*.md` | missing | No matching files found in root at migration time |
| `*PROJECT_SUMMARY*.md` | missing | No matching files found in root at migration time |
| `*LATEST*.md` | missing | No matching files found in root at migration time |
| `*UPDATED*.md` | missing | No matching files found in root at migration time |
| `RepoSense_context_pack_*.zip` | missing | No matching files found in root at migration time |
| `*.zip` | missing | No matching files found in root at migration time |
| `debug.log` | missing | No matching files found in root at migration time |
| `*.log` | missing | No matching files found in root at migration time |
| `.reposense_ci*` | missing | No matching files found in root at migration time |
| `.reposense_learn_cases` | missing | No matching files found in root at migration time |

## Not moved

| path | reason |
|---|---|
| `.venv/` | Kept in place by requirement; ignored by `.gitignore` |
| `.tmp_test_runs/` | Kept in place for local test temp root; ignored by `.gitignore` |
| `.tmp_test/` | Kept in place in this step; not moved to avoid destructive side effects |
| `analysis_runs/` | Kept in place in this step; ignored by `.gitignore` |
| `.reposense_studio/` | Kept in place in this step; local runtime/state folder |
| $src | $dst | archive legacy demo output directory |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | $dst | archive previous canonical release demo |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | $dst | archive previous canonical release demo |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | $dst | archive previous canonical release demo |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | $dst | archive previous canonical release demo |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |
| $src | missing | legacy demo directory not present |

## Canonical release demo migration (latest)

| original_path | new_path | reason |
|---|---|---|
| .reposense_demo_release_assets_current | docs/archive/local-artifacts/root-moved/.reposense_demo_release_assets_current-20260516-104146 | archived legacy demo output directory |
| .reposense_release_demo/current | docs/archive/local-artifacts/root-moved/current-20260516-104306 | archived previous canonical release demo before regeneration |
