#!/usr/bin/env python3
"""Validate queue retry/idempotency correlations without executing target code."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reposense.evidence.validation import validate_evidence_location


ALLOWED_TRIAGE_STATUSES = [
    "unreviewed",
    "confirmed_by_source",
    "plausible",
    "likely_false_positive",
    "needs_context",
    "duplicate",
    "unsupported",
]


def _read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _stable_id(*parts: Any) -> str:
    material = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]


def _all_evidence_refs(correlation: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for field in ("producer_refs", "consumer_refs", "evidence_refs"):
        refs.extend(correlation.get(field) or [])
    for effect in correlation.get("consumer_side_effects") or []:
        refs.extend(effect.get("evidence_refs") or [])
    return [ref for ref in refs if isinstance(ref, dict)]


def _validate_refs(
    correlations: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    repo_root: Path,
) -> tuple[int, list[dict[str, Any]]]:
    checked = 0
    issues = []
    for item in correlations:
        item_id = str(item.get("correlation_id") or "")
        for ref in _all_evidence_refs(item):
            checked += 1
            issues.extend(
                validate_evidence_location(
                    ref,
                    repo_root,
                    artifact="queue_reliability_correlations.json",
                    item_id=item_id,
                    require_snippet=True,
                )
            )
    for item in risks:
        item_id = str(item.get("risk_id") or "")
        for ref in item.get("evidence_refs") or []:
            if not isinstance(ref, dict):
                continue
            checked += 1
            issues.extend(
                validate_evidence_location(
                    ref,
                    repo_root,
                    artifact="queue_reliability_risks.json",
                    item_id=item_id,
                    require_snippet=True,
                )
            )
    return checked, issues


def build_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    correlation_payload = _read_json(
        run_root / "queue_reliability_correlations.json", {}
    )
    risk_payload = _read_json(run_root / "queue_reliability_risks.json", {})
    correlations = [
        item
        for item in correlation_payload.get("correlations") or []
        if isinstance(item, dict)
    ]
    risks = [
        item
        for item in risk_payload.get("risks") or []
        if isinstance(item, dict)
    ]
    checked, evidence_issues = _validate_refs(
        correlations, risks, repo_root
    )
    coverage = Counter(
        str(item.get("coverage_status") or "") for item in correlations
    )
    retries = Counter(
        str(item.get("retry_status") or "") for item in correlations
    )
    identity = Counter(
        str(item.get("producer_identity_status") or "")
        for item in correlations
    )
    guards = Counter(
        str(item.get("consumer_idempotency_status") or "")
        for item in correlations
    )
    duplicate_count = len(correlations) - len(
        {str(item.get("correlation_id") or "") for item in correlations}
    )
    limitations = sorted(
        {
            str(value)
            for item in correlations
            for value in (item.get("limitations") or [])
            if str(value)
        }
        | {
            "Static retry configuration may differ from deployed runtime configuration.",
            "Producer identity and transport idempotence do not prove consumer business idempotency.",
            "Missing idempotency evidence is not proof that no runtime guard exists.",
        }
    )
    if evidence_issues:
        limitations.append(
            "One or more queue reliability evidence locations failed validation."
        )
    return {
        "version": "queue_retry_idempotency_validation_v1",
        "case_id": str(case_id or ""),
        "commit_sha": str(commit_sha or ""),
        "run_dir": "<RUN_DIR>",
        "summary": {
            "matched_channels": sum(
                item.get("match_status") == "matched"
                for item in correlations
            ),
            "explicit_retries": retries["explicit_retry"],
            "unresolved_retry_configs": (
                retries["dynamic_or_unresolved"]
                + retries["framework_default_or_unknown"]
            ),
            "producer_dedupe_signals": (
                identity["stable_job_id"]
                + identity["deduplication_option"]
                + identity["message_key_observed"]
            ),
            "transport_idempotence_signals": identity[
                "transport_idempotence_observed"
            ],
            "side_effecting_consumers": sum(
                bool(item.get("consumer_side_effects"))
                for item in correlations
            ),
            "consumer_guards": sum(
                status.endswith("_observed")
                and status not in {"none_observed", "guard_signal_observed"}
                for status, count in guards.items()
                for _ in range(count)
            ),
            "retry_without_guard_risks": sum(
                item.get("pattern_type")
                == "queue_retry_without_idempotency_guard"
                for item in risks
            ),
            "side_effect_without_guard_risks": sum(
                item.get("pattern_type")
                == "queue_consumer_side_effect_without_idempotency_evidence"
                for item in risks
            ),
            "counts_by_coverage_status": dict(sorted(coverage.items())),
            "duplicate_correlations": duplicate_count,
            "evidence_checked": checked,
            "evidence_valid": max(0, checked - len(evidence_issues)),
            "evidence_errors": len(evidence_issues),
        },
        "correlations": correlations,
        "risks": risks,
        "evidence_issues": evidence_issues,
        "limitations": limitations,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Queue Retry / Idempotency Validation",
        "",
        "This validation reads static RepoSense artifacts and does not execute the target repository.",
        "",
        "## Summary",
        "",
        f"- Matched channels: {summary.get('matched_channels', 0)}",
        f"- Explicit retries: {summary.get('explicit_retries', 0)}",
        f"- Unresolved retry configurations: {summary.get('unresolved_retry_configs', 0)}",
        f"- Producer identity/dedupe signals: {summary.get('producer_dedupe_signals', 0)}",
        f"- Transport idempotence signals: {summary.get('transport_idempotence_signals', 0)}",
        f"- Side-effecting consumers: {summary.get('side_effecting_consumers', 0)}",
        f"- Consumer guards: {summary.get('consumer_guards', 0)}",
        f"- Retry-without-guard risks: {summary.get('retry_without_guard_risks', 0)}",
        f"- Evidence checked/valid/errors: {summary.get('evidence_checked', 0)}/{summary.get('evidence_valid', 0)}/{summary.get('evidence_errors', 0)}",
        "",
        "## Boundaries",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("limitations") or [])
    return "\n".join(lines) + "\n"


def build_triage_template(payload: dict[str, Any]) -> dict[str, Any]:
    items = []
    for item in payload.get("correlations") or []:
        if not (
            item.get("retry_status") == "explicit_retry"
            or item.get("consumer_side_effects")
            or item.get("producer_identity_status")
            not in {"none_observed", "unknown"}
        ):
            continue
        refs = _all_evidence_refs(item)
        primary = refs[0] if refs else {}
        items.append(
            {
                "item_id": _stable_id(item.get("correlation_id")),
                "source_artifact": "queue_reliability_correlations.json",
                "correlation_id": item.get("correlation_id"),
                "framework": item.get("framework"),
                "queue_or_topic": item.get("queue_or_topic"),
                "coverage_status": item.get("coverage_status"),
                "file": primary.get("file", ""),
                "line": primary.get("start_line", 0),
                "evidence": refs,
                "triage_status": "unreviewed",
                "reviewer_note": "",
            }
        )
    return {
        "version": "queue_retry_idempotency_triage_v1",
        "allowed_statuses": ALLOWED_TRIAGE_STATUSES,
        "items": items,
    }


def write_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
    case_dir: str | Path | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    payload = build_validation(
        run_root,
        repo_path,
        case_id=case_id,
        commit_sha=commit_sha,
    )
    markdown = render_markdown(payload)
    triage = build_triage_template(payload)
    _write_json(
        run_root / "queue_retry_idempotency_validation.json", payload
    )
    _write_text(
        run_root / "queue_retry_idempotency_validation.md", markdown
    )
    if case_dir:
        case_root = Path(case_dir).resolve()
        _write_json(
            case_root / "queue_retry_idempotency_validation.json", payload
        )
        _write_text(
            case_root / "queue_retry_idempotency_validation.md", markdown
        )
        _write_json(
            case_root / "queue_retry_idempotency_triage_template.json",
            triage,
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate queue retry/idempotency correlation artifacts."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--commit", default="")
    parser.add_argument("--case-dir")
    args = parser.parse_args(argv)
    payload = write_validation(
        args.run_dir,
        args.repo_path,
        case_id=args.case_id,
        commit_sha=args.commit,
        case_dir=args.case_dir,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 1 if payload["summary"]["evidence_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
