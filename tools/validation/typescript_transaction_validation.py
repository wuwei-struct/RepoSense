#!/usr/bin/env python3
"""Validate TypeScript/TypeORM transaction correlations without executing code."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reposense.evidence.validation import validate_evidence_location


TRIAGE_STATUSES = [
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
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value.rstrip() + "\n")


def build_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    artifact = _read_json(run_root / "transaction_correlations.json", {})
    correlations = [
        item
        for item in artifact.get("correlations") or []
        if isinstance(item, dict)
        and item.get("language") == "typescript"
        and item.get("framework") == "typeorm"
    ]
    typeorm = _read_json(run_root / "typeorm_db_operations.json", {})
    writes = [
        item
        for item in typeorm.get("operations") or []
        if isinstance(item, dict) and item.get("kind") == "db.write"
    ]
    patterns = _read_json(run_root / "patterns.json", {})
    outside_tx = [
        item
        for item in patterns.get("patterns") or []
        if isinstance(item, dict)
        and item.get("pattern_type") == "db_write_outside_tx"
    ]
    issues: list[dict[str, Any]] = []
    evidence_checked = 0
    for item in correlations:
        for field in (
            "transaction_evidence_refs",
            "callsite_evidence_refs",
            "db_write_evidence_refs",
        ):
            for index, ref in enumerate(item.get(field) or []):
                if not isinstance(ref, dict):
                    continue
                evidence_checked += 1
                issues.extend(
                    validate_evidence_location(
                        ref,
                        repo_root,
                        artifact="transaction_correlations.json",
                        item_id=(
                            f"{item.get('correlation_id', '')}:{field}:{index}"
                        ),
                        require_snippet=False,
                    )
                )
    coverage = Counter(
        str(item.get("coverage_status") or "unknown")
        for item in correlations
    )
    mechanisms = Counter(
        str(item.get("transaction_mechanism") or "unknown")
        for item in correlations
    )
    unique = {
        (
            item.get("db_operation_id"),
            item.get("coverage_status"),
            item.get("transaction_mechanism"),
        )
        for item in correlations
    }
    summary = {
        "typeorm_writes": len(writes),
        "explicit_callback_coverage": mechanisms["typeorm_callback"]
        + mechanisms["entity_manager_callback"],
        "query_runner_coverage": mechanisms["query_runner"],
        "trusted_decorator_coverage": mechanisms["trusted_decorator_method"]
        + mechanisms["trusted_decorator_class"],
        "wrapper_caller_coverage": mechanisms["direct_wrapper_caller"],
        "covered_explicit": coverage["covered_explicit"],
        "uncovered": coverage["uncovered"],
        "partially_covered": coverage["partially_covered"],
        "read_only_transaction": coverage["read_only_transaction"],
        "unknown": coverage["unknown"],
        "migration_unresolved": sum(
            "migration_transaction_policy_requires_confirmation"
            in (item.get("limitations") or [])
            for item in correlations
        ),
        "outside_tx_patterns": len(outside_tx),
        "duplicate_correlations": max(0, len(correlations) - len(unique)),
        "evidence_checked": evidence_checked,
        "evidence_valid": max(0, evidence_checked - len(issues)),
        "evidence_errors": len(issues),
    }
    limitations = [
        "Validation covers explicit local TypeORM transactions and one-hop static wrapper calls only.",
        "Unknown coverage is not proof that a write executes outside a transaction.",
        "Migration transaction policy requires runtime or owner confirmation when no explicit scope is present.",
        "Validation does not execute the target repository.",
    ]
    if issues:
        limitations.append(
            "One or more transaction-correlation evidence locations failed validation."
        )
    return {
        "version": "typescript_transaction_validation_v1",
        "case_id": str(case_id or ""),
        "commit_sha": str(commit_sha or ""),
        "run_dir": "<RUN_DIR>",
        "summary": summary,
        "counts_by_coverage_status": dict(sorted(coverage.items())),
        "counts_by_transaction_mechanism": dict(sorted(mechanisms.items())),
        "correlations": correlations,
        "outside_tx_patterns": outside_tx,
        "evidence_issues": issues,
        "limitations": limitations,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    return "\n".join(
        [
            "# TypeScript Transaction Validation",
            "",
            "This report validates static TypeORM transaction correlations. It does not execute the target repository.",
            "",
            "## Summary",
            "",
            f"- TypeORM writes: {summary.get('typeorm_writes', 0)}",
            f"- Callback / QueryRunner covered: {summary.get('explicit_callback_coverage', 0)} / {summary.get('query_runner_coverage', 0)}",
            f"- Decorator / wrapper correlations: {summary.get('trusted_decorator_coverage', 0)} / {summary.get('wrapper_caller_coverage', 0)}",
            f"- Covered / uncovered / partial: {summary.get('covered_explicit', 0)} / {summary.get('uncovered', 0)} / {summary.get('partially_covered', 0)}",
            f"- Read-only / unknown / migration unresolved: {summary.get('read_only_transaction', 0)} / {summary.get('unknown', 0)} / {summary.get('migration_unresolved', 0)}",
            f"- Outside-tx Patterns: {summary.get('outside_tx_patterns', 0)}",
            f"- Evidence checked/valid/errors: {summary.get('evidence_checked', 0)}/{summary.get('evidence_valid', 0)}/{summary.get('evidence_errors', 0)}",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in payload.get("limitations") or []],
            "",
        ]
    )


def build_triage_template(payload: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in payload.get("correlations") or []:
        correlation_id = str(item.get("correlation_id") or "")
        raw = f"{correlation_id}|{item.get('coverage_status') or ''}"
        rows.append(
            {
                "item_id": hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16],
                "source_artifact": "transaction_correlations.json",
                "correlation_id": correlation_id,
                "db_operation_id": item.get("db_operation_id"),
                "operation": item.get("operation"),
                "file": item.get("target_file"),
                "line": item.get("db_write_line"),
                "coverage_status": item.get("coverage_status"),
                "transaction_mechanism": item.get("transaction_mechanism"),
                "evidence": item.get("db_write_evidence_refs") or [],
                "limitations": item.get("limitations") or [],
                "triage_status": "unreviewed",
                "reviewer_note": "",
            }
        )
    return {
        "version": "typescript_transaction_triage_v1",
        "allowed_statuses": TRIAGE_STATUSES,
        "items": rows,
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
    _write_json(run_root / "typescript_transaction_validation.json", payload)
    _write_text(run_root / "typescript_transaction_validation.md", markdown)
    if case_dir:
        case_root = Path(case_dir).resolve()
        _write_json(
            case_root / "typescript_transaction_validation.json", payload
        )
        _write_text(
            case_root / "typescript_transaction_validation.md", markdown
        )
        _write_json(
            case_root / "typescript_transaction_triage_template.json", triage
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--case-id", default="")
    parser.add_argument("--commit-sha", default="")
    parser.add_argument("--case-dir")
    args = parser.parse_args(argv)
    payload = write_validation(
        args.run_dir,
        args.repo,
        case_id=args.case_id,
        commit_sha=args.commit_sha,
        case_dir=args.case_dir,
    )
    summary = payload["summary"]
    print(
        "TypeScript transaction validation: "
        f"covered={summary['covered_explicit']} "
        f"partial={summary['partially_covered']} "
        f"unknown={summary['unknown']} "
        f"evidence_errors={summary['evidence_errors']}"
    )
    return 1 if summary["evidence_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
