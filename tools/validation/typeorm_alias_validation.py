#!/usr/bin/env python3
"""Validate TypeORM cross-file alias resolutions without executing code."""

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
EVIDENCE_FIELDS = [
    "import_evidence_refs",
    "dependency_evidence_refs",
    "callsite_evidence_refs",
    "target_evidence_refs",
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
    artifact = _read_json(run_root / "typeorm_alias_resolutions.json", {})
    rows = [
        item
        for item in artifact.get("resolutions") or []
        if isinstance(item, dict)
    ]
    transactions = _read_json(
        run_root / "transaction_correlations.json", {}
    )
    correlations = [
        item
        for item in transactions.get("correlations") or []
        if isinstance(item, dict)
        and item.get("language") == "typescript"
        and item.get("framework") == "typeorm"
    ]
    issues = []
    checked = 0
    for item in rows:
        for field in EVIDENCE_FIELDS:
            for index, ref in enumerate(item.get(field) or []):
                if not isinstance(ref, dict):
                    continue
                checked += 1
                issues.extend(
                    validate_evidence_location(
                        ref,
                        repo_root,
                        artifact="typeorm_alias_resolutions.json",
                        item_id=(
                            f"{item.get('resolution_id', '')}:{field}:{index}"
                        ),
                    )
                )
    counts = Counter(
        str(item.get("resolution_status") or "unresolved") for item in rows
    )
    ids = [str(item.get("resolution_id") or "") for item in rows]
    resolved_ids = {
        str(value)
        for item in correlations
        for value in (item.get("alias_resolution_ids") or [])
    }
    summary = {
        "candidate_receivers": len(rows),
        "direct_imports": counts["resolved_direct_import"],
        "alias_imports": counts["resolved_alias_import"],
        "reexports": counts["resolved_reexport"],
        "barrel_resolutions": counts["resolved_barrel"],
        "local_assignments": counts["resolved_local_assignment"],
        "resolved_wrapper_calls": sum(
            str(item.get("resolution_status") or "").startswith("resolved_")
            and bool(item.get("db_operation_ids"))
            for item in rows
        ),
        "ambiguous": counts["ambiguous"],
        "unresolved": counts["unresolved"],
        "writes_newly_covered": sum(
            item.get("coverage_status") == "covered_explicit"
            and bool(item.get("alias_resolution_ids"))
            for item in correlations
        ),
        "writes_retained_unknown": sum(
            item.get("coverage_status") == "unknown" for item in correlations
        ),
        "correlations_using_alias_resolution": len(resolved_ids),
        "duplicate_resolutions": max(0, len(ids) - len(set(ids))),
        "evidence_checked": checked,
        "evidence_valid": max(0, checked - len(issues)),
        "evidence_errors": len(issues),
    }
    limitations = [
        "Resolution is limited to repository-relative imports and at most three re-export edges.",
        "Dynamic dependency injection, tsconfig aliases, runtime providers, and multi-hop calls remain unresolved.",
        "A resolved wrapper target does not prove every runtime call path or transaction behavior.",
        "Validation does not execute the target repository.",
    ]
    return {
        "version": "typeorm_alias_validation_v1",
        "case_id": str(case_id or ""),
        "commit_sha": str(commit_sha or ""),
        "run_dir": "<RUN_DIR>",
        "summary": summary,
        "resolutions": rows,
        "triage_items": build_triage_items(rows),
        "evidence_issues": issues,
        "limitations": limitations,
    }


def build_triage_items(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for row in rows:
        resolution_id = str(row.get("resolution_id") or "")
        raw = f"{resolution_id}|{row.get('resolution_status') or ''}"
        items.append(
            {
                "item_id": hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16],
                "resolution_id": resolution_id,
                "source_file": row.get("source_file"),
                "source_method": row.get("source_method"),
                "resolved_file": row.get("resolved_file"),
                "resolved_method": row.get("resolved_method"),
                "resolution_status": row.get("resolution_status"),
                "evidence_refs": (
                    list(row.get("callsite_evidence_refs") or [])
                    + list(row.get("target_evidence_refs") or [])
                ),
                "limitations": row.get("limitations") or [],
                "triage_status": "unreviewed",
                "reviewer_note": "",
            }
        )
    return items


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# TypeORM Alias Validation",
            "",
            "This report validates conservative cross-file TypeScript wrapper resolution. It does not execute the target repository.",
            "",
            "## Summary",
            "",
            f"- Candidate receivers: {summary['candidate_receivers']}",
            f"- Direct / alias / re-export / barrel / local: {summary['direct_imports']} / {summary['alias_imports']} / {summary['reexports']} / {summary['barrel_resolutions']} / {summary['local_assignments']}",
            f"- Resolved wrapper calls: {summary['resolved_wrapper_calls']}",
            f"- Ambiguous / unresolved: {summary['ambiguous']} / {summary['unresolved']}",
            f"- Writes newly covered / retained unknown: {summary['writes_newly_covered']} / {summary['writes_retained_unknown']}",
            f"- Evidence checked/valid/errors: {summary['evidence_checked']}/{summary['evidence_valid']}/{summary['evidence_errors']}",
            "",
            "## Limitations",
            "",
            *[f"- {item}" for item in payload["limitations"]],
            "",
        ]
    )


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
        run_root, repo_path, case_id=case_id, commit_sha=commit_sha
    )
    markdown = render_markdown(payload)
    triage = {
        "version": "typeorm_alias_triage_v1",
        "allowed_statuses": TRIAGE_STATUSES,
        "items": payload["triage_items"],
    }
    _write_json(run_root / "typeorm_alias_validation.json", payload)
    _write_text(run_root / "typeorm_alias_validation.md", markdown)
    if case_dir:
        case_root = Path(case_dir).resolve()
        _write_json(case_root / "typeorm_alias_validation.json", payload)
        _write_text(case_root / "typeorm_alias_validation.md", markdown)
        _write_json(
            case_root / "typeorm_alias_triage_template.json", triage
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
        "TypeORM alias validation: "
        f"resolved={summary['resolved_wrapper_calls']} "
        f"ambiguous={summary['ambiguous']} "
        f"unresolved={summary['unresolved']} "
        f"evidence_errors={summary['evidence_errors']}"
    )
    return 1 if summary["evidence_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
