#!/usr/bin/env python3
"""Validate TypeORM DB facts without executing the analyzed repository."""

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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n")


def _stable_id(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def build_validation(
    run_dir: str | Path,
    repo_path: str | Path,
    *,
    case_id: str = "",
    commit_sha: str = "",
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    artifact = _read_json(run_root / "typeorm_db_operations.json", {})
    operations = [
        item
        for item in artifact.get("operations", [])
        if isinstance(item, dict)
    ]
    evidence_issues: list[dict[str, Any]] = []
    evidence_checked = 0
    for operation in operations:
        for ref_index, ref in enumerate(operation.get("evidence_refs") or []):
            if not isinstance(ref, dict):
                continue
            evidence_checked += 1
            evidence_issues.extend(
                validate_evidence_location(
                    ref,
                    repo_root,
                    artifact="typeorm_db_operations.json",
                    item_id=f"{operation.get('operation_id', '')}:{ref_index}",
                    require_snippet=False,
                )
            )

    kind_counts = Counter(str(item.get("kind") or "") for item in operations)
    receiver_counts = Counter(
        str(item.get("receiver_kind") or "unknown")
        for item in operations
    )
    operation_counts = Counter(
        str(item.get("operation") or "")
        for item in operations
    )
    transaction_contexts = Counter(
        str(item.get("transaction_context") or "unknown")
        for item in operations
    )
    correlation_summary = _read_json(
        run_root / "transaction_correlation_summary.json", {}
    )
    typeorm_correlation_summary = (
        correlation_summary.get("by_language_framework") or {}
    ).get("typescript/typeorm") or {}
    unique_keys = {
        (
            item.get("file"),
            item.get("line_start"),
            item.get("receiver_name"),
            item.get("operation"),
            item.get("kind"),
        )
        for item in operations
    }
    imports = 0
    injected_repositories = 0
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".ts", ".tsx"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            continue
        imports += text.count("from 'typeorm'") + text.count('from "typeorm"')
        imports += text.count("from '@nestjs/typeorm'") + text.count(
            'from "@nestjs/typeorm"'
        )
        injected_repositories += text.count("@InjectRepository")

    summary = {
        "typeorm_imports": imports,
        "injected_repositories": injected_repositories,
        "data_source_operations": receiver_counts["data_source"],
        "entity_manager_operations": receiver_counts["entity_manager"],
        "query_runner_operations": receiver_counts["query_runner"],
        "db_reads": kind_counts["db.read"],
        "db_writes": kind_counts["db.write"],
        "transaction_signals": kind_counts["db.transaction"],
        "query_builder_reads": sum(
            item.get("receiver_kind") == "query_builder"
            and item.get("kind") == "db.read"
            for item in operations
        ),
        "query_builder_writes": sum(
            item.get("receiver_kind") == "query_builder"
            and item.get("kind") == "db.write"
            for item in operations
        ),
        "raw_sql_classified": operation_counts["query"]
        - kind_counts["db.query_unknown"],
        "raw_sql_unknown": kind_counts["db.query_unknown"],
        "duplicate_events": max(0, len(operations) - len(unique_keys)),
        "writes_with_explicit_transaction_context": sum(
            item.get("kind") == "db.write"
            and item.get("transaction_context")
            in {"explicit_callback", "query_runner_explicit"}
            for item in operations
        ),
        "writes_with_unresolved_transaction_coverage": sum(
            item.get("kind") == "db.write"
            and item.get("transaction_context")
            not in {"explicit_callback", "query_runner_explicit"}
            for item in operations
        ),
        "evidence_checked": evidence_checked,
        "evidence_valid": max(0, evidence_checked - len(evidence_issues)),
        "evidence_errors": len(evidence_issues),
        "transaction_correlation_coverage": (
            typeorm_correlation_summary.get("counts_by_coverage_status") or {}
        ),
    }
    limitations = [
        "TypeORM receiver correlation is static and does not implement a complete TypeScript type system.",
        "Unknown transaction context does not prove that a write executes outside a transaction.",
        "Dynamic SQL is retained as db.query_unknown and requires human confirmation.",
        "Validation does not execute the target repository.",
    ]
    if evidence_issues:
        limitations.append("One or more TypeORM evidence locations failed validation.")
    return {
        "version": "typeorm_db_validation_v1",
        "case_id": str(case_id or ""),
        "commit_sha": str(commit_sha or ""),
        "run_dir": "<RUN_DIR>",
        "summary": summary,
        "counts_by_receiver_kind": dict(sorted(receiver_counts.items())),
        "counts_by_operation": dict(sorted(operation_counts.items())),
        "counts_by_transaction_context": dict(
            sorted(transaction_contexts.items())
        ),
        "operations": operations,
        "evidence_issues": evidence_issues,
        "limitations": limitations,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# TypeORM DB Validation",
        "",
        "This report validates static TypeORM DB observations. It does not execute the target repository.",
        "",
        "## Summary",
        "",
        f"- TypeORM imports: {summary.get('typeorm_imports', 0)}",
        f"- Injected repositories: {summary.get('injected_repositories', 0)}",
        f"- DB reads/writes/transactions: {summary.get('db_reads', 0)}/{summary.get('db_writes', 0)}/{summary.get('transaction_signals', 0)}",
        f"- QueryBuilder reads/writes: {summary.get('query_builder_reads', 0)}/{summary.get('query_builder_writes', 0)}",
        f"- Raw SQL classified/unknown: {summary.get('raw_sql_classified', 0)}/{summary.get('raw_sql_unknown', 0)}",
        f"- Explicit/unresolved write transaction context: {summary.get('writes_with_explicit_transaction_context', 0)}/{summary.get('writes_with_unresolved_transaction_coverage', 0)}",
        f"- Evidence checked/valid/errors: {summary.get('evidence_checked', 0)}/{summary.get('evidence_valid', 0)}/{summary.get('evidence_errors', 0)}",
        "",
        "## Receiver Coverage",
        "",
    ]
    receiver_counts = payload.get("counts_by_receiver_kind") or {}
    if receiver_counts:
        lines.extend(
            f"- {name}: {count}"
            for name, count in sorted(receiver_counts.items())
        )
    else:
        lines.append("- No TypeORM receivers observed.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in payload.get("limitations") or [])
    return "\n".join(lines) + "\n"


def build_triage_template(payload: dict[str, Any]) -> dict[str, Any]:
    operations = payload.get("operations") or []
    selected: list[dict[str, Any]] = []
    groups = [
        [item for item in operations if item.get("kind") == "db.read"][:5],
        [item for item in operations if item.get("kind") == "db.write"][:5],
        [
            item
            for item in operations
            if item.get("kind") == "db.transaction"
        ],
        [
            item
            for item in operations
            if item.get("receiver_kind") == "query_builder"
            and item.get("kind") == "db.write"
        ],
        [
            item
            for item in operations
            if item.get("kind") == "db.query_unknown"
        ],
    ]
    seen: set[str] = set()
    for group in groups:
        for item in group:
            operation_id = str(item.get("operation_id") or "")
            if operation_id in seen:
                continue
            seen.add(operation_id)
            selected.append(
                {
                    "item_id": _stable_id(operation_id, item.get("kind")),
                    "source_artifact": "typeorm_db_operations.json",
                    "operation_id": operation_id,
                    "receiver": item.get("receiver_name"),
                    "receiver_kind": item.get("receiver_kind"),
                    "kind": item.get("kind"),
                    "operation": item.get("operation"),
                    "file": item.get("file"),
                    "line": item.get("line_start"),
                    "evidence": item.get("evidence_refs") or [],
                    "transaction_context": item.get("transaction_context"),
                    "triage_status": "unreviewed",
                    "reviewer_note": "",
                }
            )
    return {
        "version": "typeorm_db_triage_v1",
        "allowed_statuses": TRIAGE_STATUSES,
        "items": selected,
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
    _write_json(run_root / "typeorm_db_validation.json", payload)
    _write_text(run_root / "typeorm_db_validation.md", markdown)
    if case_dir:
        case_root = Path(case_dir).resolve()
        _write_json(case_root / "typeorm_db_validation.json", payload)
        _write_text(case_root / "typeorm_db_validation.md", markdown)
        _write_json(case_root / "typeorm_db_triage_template.json", triage)
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
        "TypeORM validation: "
        f"reads={summary['db_reads']} writes={summary['db_writes']} "
        f"transactions={summary['transaction_signals']} "
        f"evidence_errors={summary['evidence_errors']}"
    )
    return 1 if summary["evidence_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
