# Pattern Contract

## Role of Patterns in RepoSense

RepoSense uses a layered contract:

Facts -> Patterns -> Insights

Patterns are the deterministic, evidence-backed aggregation layer over Facts. They do not replace Findings/Events/Evidence; they organize them into auditable engineering modes for prioritization.

## Pattern Goals

Patterns aim to make backend transaction and side-effect signals:

- auditable
- rankable
- explainable
- stable across repeated runs

## Public Pattern Contract

The public pattern contract is open.

Detection logic and evidence matching are open.

Deep explanation playbooks, repair playbooks, and advanced AI collaboration prompts may be reserved in hosted/commercial layers.

## Public Contract Fields

Authoring/public contract fields are defined in `schemas/pattern.schema.json`:

- `rule_id`
- `category`
- `severity`
- `language`
- `signals`
- `evidence_required`
- `confidence_policy`
- `public_description`
- `commercial_insight_reserved`

These fields describe how a pattern rule should be authored and shared.

## Runtime Artifact vs Public Contract

RepoSense runtime-emitted pattern artifacts may contain additional fields such as:

- `pattern_id`
- `pattern_type`
- `status`
- `summary`
- `evidence_refs`
- `supporting_findings`
- `supporting_events`

Those runtime fields are output-oriented and can evolve with pipeline needs.

The public contract is the minimum open authoring contract; runtime payloads may carry richer execution metadata.

## Stability Requirements

Pattern rules should preserve:

- deterministic outputs for same run artifacts and rule version
- stable ordering in emitted lists
- conservative confidence behavior
- explicit evidence linkage

## Conservative / Evidence-backed Principles

- Pattern claims must map to observable evidence.
- If evidence is weak, pattern status/confidence must be conservative.
- Absence of a signal should be described as "not observed" rather than proof of absence.

## Open-source Boundary

Open:

- pattern detection logic
- evidence matching logic
- public rule contract and schema
- rule authoring guide

## Commercial Boundary

Reserved/commercial layers may provide:

- deep explanation enrichment
- advanced repair playbooks
- enterprise prioritization and collaboration workflows
- hosted AI coordination prompts and memory

## Example Pattern (Public Contract Shape)

```json
{
  "rule_id": "db_write_outside_tx",
  "category": "transaction",
  "severity": "warning",
  "language": "python",
  "signals": ["db_write", "transaction_boundary_absent"],
  "evidence_required": true,
  "confidence_policy": "conservative",
  "public_description": "Detects database write signals without an observed transaction boundary.",
  "commercial_insight_reserved": true
}
```
