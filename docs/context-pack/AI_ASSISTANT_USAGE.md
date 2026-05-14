# AI_ASSISTANT_USAGE

## AI assistant usage

Use Context Pack as a facts-first handoff before asking an assistant to plan or modify backend code.

## Recommended Reading Order

1. `README.md`
2. `MAP/index.json`
3. `ARTIFACTS/quality_gate.json`
4. `ARTIFACTS/backend_verifier_report.*` (if present)
5. `ARTIFACTS/patterns.json` and risk/explain artifacts
6. top evidence references under `EVIDENCE/*`

## Facts-first vs Drilldown

Facts-only is usually enough for:

- repository overview
- API/event surface summary
- baseline risk triage
- gate status and readiness checks

Source-on-demand drilldown is needed when:

- a high-risk signal is still ambiguous
- implementation order/boundary details are required
- a change plan needs concrete line-level verification

## Default Safety Rule

Do not start with unrestricted whole-repository source roaming.

Start from Context Pack facts, then selectively drill down by evidence references.

## Recommended Prompt/Task Types

- summarize this backend using context pack facts
- inspect transaction signals and side-effect map
- explain high-risk findings with evidence refs
- prepare next upgrade context from baseline/gate/patterns

## Prohibited Conclusion Style

- do not treat Context Pack as correctness proof
- do not provide deterministic conclusions without evidence
- do not claim safe upgrade guarantees from pack-only signals

## Operating Principles

- Facts first, source on demand
- Evidence-first
- Deterministic
- Reproducible
