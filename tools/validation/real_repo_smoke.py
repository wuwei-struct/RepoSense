#!/usr/bin/env python3
"""Validate RepoSense review artifacts produced from pinned external repositories."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import yaml

from reposense.evidence.validation import validate_evidence_location


REQUIRED_ARTIFACTS = [
    "report.html",
    "backend_verifier_report.json",
    "backend_verifier_report.md",
    "patterns.json",
    "code_health.json",
    "permission_surface.json",
    "permission_risks.json",
    "authz_matrix_inferred.yaml",
    "authz_matrix_diff.json",
    "repository_review_report.json",
    "repository_review_report.md",
    "review_risk_matrix.json",
    "human_review_required.md",
    "transaction_correlations.json",
    "transaction_correlation_summary.json",
    "route_intent_annotations.json",
    "file_context_annotations.json",
    "review_context_summary.json",
    "route_guard_correlations.json",
    "route_guard_summary.json",
    "openapi_security_surface.json",
    "route_decorator_classifications.json",
    "route_decorator_summary.json",
    "queue_cache_validation.json",
    "queue_cache_validation.md",
    "typeorm_db_operations.json",
    "typeorm_db_summary.json",
    "typeorm_db_validation.json",
    "typeorm_db_validation.md",
    "typescript_transaction_validation.json",
    "typescript_transaction_validation.md",
    "context_pack/REVIEW/README.md",
    "run_manifest.json",
]

TRIAGE_CATEGORIES = [
    "backend_pattern",
    "code_health",
    "permission_risk",
    "authz_inferred",
    "human_review_required",
]

MAX_SNIPPET_CHARS = 4000


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _read_yaml(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
        return value if value is not None else default
    except (OSError, yaml.YAMLError):
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


def load_case_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    payload = _read_json(Path(path), {})
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise ValueError("real repo case config must contain a cases array")
    return payload


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any, limit: int = 400) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _stable_id(*parts: Any) -> str:
    material = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(material.encode("utf-8")).hexdigest()[:12]


def _path_from_value(value: Any, repo_root: Path) -> tuple[Path | None, str, bool]:
    raw = str(value or "").strip()
    if not raw or raw.startswith("("):
        return None, "", False
    raw = raw.removeprefix("file://")
    normalized = raw.replace("\\", "/")
    for marker in ("<REPO_ROOT>", "${REPO_ROOT}"):
        if normalized == marker:
            return repo_root, ".", False
        if normalized.startswith(marker + "/"):
            rel = normalized[len(marker) + 1 :]
            return (repo_root / rel).resolve(), rel, False
    is_absolute = os.path.isabs(raw) or bool(re.match(r"^[A-Za-z]:[\\/]", raw))
    candidate = Path(raw).expanduser().resolve() if is_absolute else (repo_root / raw).resolve()
    try:
        rel = candidate.relative_to(repo_root)
        return candidate, rel.as_posix() or ".", is_absolute
    except ValueError:
        return candidate, f"outside-repo:{candidate.name}", is_absolute


def _source_record(source: str, item_id: str, obj: dict[str, Any], require_snippet: bool) -> dict[str, Any] | None:
    file_value = obj.get("file") or obj.get("path") or obj.get("repo_path") or obj.get("absolute_path")
    if not file_value:
        return None
    return {
        "source": source,
        "item_id": str(item_id or ""),
        "file": file_value,
        "line": obj.get("line_start") or obj.get("start_line") or obj.get("line") or 0,
        "line_end": obj.get("line_end") if obj.get("line_end") is not None else obj.get("end_line"),
        "snippet": obj.get("snippet"),
        "require_snippet": require_snippet,
    }


def _records_from_items(
    source: str,
    items: Iterable[Any],
    id_fields: tuple[str, ...],
    require_snippet: bool,
    include_direct: bool = True,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_id = next((item.get(field) for field in id_fields if item.get(field)), str(index))
        if include_direct:
            direct = _source_record(source, str(item_id), item, require_snippet)
            if direct:
                records.append(direct)
        for ref_index, ref in enumerate(_list(item.get("evidence_refs"))):
            if isinstance(ref, dict):
                record = _source_record(f"{source}.evidence_refs", f"{item_id}:{ref_index}", ref, False)
                if record:
                    records.append(record)
    return records


def _evidence_records(run_dir: Path) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    records: list[dict[str, Any]] = []
    refs: list[tuple[str, str]] = []

    report = _read_json(run_dir / "report.json", {})
    records += _records_from_items("report.findings", _list(report.get("findings")), ("fid", "rule_id"), True)
    for finding in _list(report.get("findings")):
        if isinstance(finding, dict) and finding.get("primary_eid") is not None:
            refs.append((f"finding:{finding.get('fid')}", f"E{finding.get('primary_eid')}"))

    patterns = _read_json(run_dir / "patterns.json", {})
    records += _records_from_items("patterns", _list(patterns.get("patterns")), ("pattern_id", "rule_id"), False)

    health = _read_json(run_dir / "code_health.json", {})
    records += _records_from_items("code_health", _list(health.get("findings")), ("health_id", "rule_id"), True)

    permissions = _read_json(run_dir / "permission_risks.json", {})
    records += _records_from_items("permission_risks", _list(permissions.get("risks")), ("risk_id", "rule_id"), True)

    route_intents = _read_json(run_dir / "route_intent_annotations.json", {})
    records += _records_from_items(
        "route_intent_annotations",
        _list(route_intents.get("annotations")),
        ("annotation_id",),
        False,
    )

    file_contexts = _read_json(run_dir / "file_context_annotations.json", {})
    records += _records_from_items(
        "file_context_annotations",
        _list(file_contexts.get("annotations")),
        ("annotation_id",),
        False,
        include_direct=False,
    )

    route_decorators = _read_json(
        run_dir / "route_decorator_classifications.json",
        {},
    )
    records += _records_from_items(
        "route_decorator_classifications",
        _list(route_decorators.get("classifications")),
        ("classification_id",),
        False,
        include_direct=False,
    )

    queue_cache = _read_json(run_dir / "queue_cache_validation.json", {})
    records += _records_from_items(
        "queue_cache_validation.queue_observations",
        _list(queue_cache.get("queue_observations")),
        ("event_id",),
        False,
        include_direct=False,
    )
    records += _records_from_items(
        "queue_cache_validation.cache_observations",
        _list(queue_cache.get("cache_observations")),
        ("event_id",),
        False,
        include_direct=False,
    )
    typeorm_validation = _read_json(
        run_dir / "typeorm_db_validation.json", {}
    )
    records += _records_from_items(
        "typeorm_db_validation.operations",
        _list(typeorm_validation.get("operations")),
        ("operation_id",),
        False,
        include_direct=True,
    )
    typescript_transaction_validation = _read_json(
        run_dir / "typescript_transaction_validation.json", {}
    )
    records += _records_from_items(
        "typescript_transaction_validation.correlations",
        _list(typescript_transaction_validation.get("correlations")),
        ("correlation_id",),
        False,
        include_direct=False,
    )

    review = _read_json(run_dir / "repository_review_report.json", {})
    for index, item in enumerate(_list(review.get("human_review_required"))):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("item_id") or item.get("path") or index)
        for ref_index, ref in enumerate(_list(item.get("evidence_refs"))):
            if isinstance(ref, dict):
                record = _source_record("human_review_required.evidence_refs", f"{item_id}:{ref_index}", ref, False)
                if record:
                    records.append(record)

    correlations = _read_json(run_dir / "transaction_correlations.json", {})
    for index, item in enumerate(_list(correlations.get("correlations"))):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("correlation_id") or index)
        for field in ("transaction_evidence_refs", "callsite_evidence_refs", "db_write_evidence_refs"):
            for ref_index, ref in enumerate(_list(item.get(field))):
                if isinstance(ref, dict):
                    record = _source_record(f"transaction_correlations.{field}", f"{item_id}:{ref_index}", ref, False)
                    if record:
                        records.append(record)

    guard_correlations = _read_json(
        run_dir / "route_guard_correlations.json", {}
    )
    for index, item in enumerate(_list(guard_correlations.get("correlations"))):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("correlation_id") or index)
        for field in ("code_route_refs", "openapi_route_refs", "evidence_refs"):
            for ref_index, ref in enumerate(_list(item.get(field))):
                if isinstance(ref, dict):
                    record = _source_record(
                        f"route_guard_correlations.{field}",
                        f"{item_id}:{ref_index}",
                        ref,
                        False,
                    )
                    if record:
                        records.append(record)
        for field in ("guard_sources", "public_bypass_sources"):
            for source_index, source in enumerate(_list(item.get(field))):
                if not isinstance(source, dict):
                    continue
                for ref_index, ref in enumerate(
                    _list(source.get("evidence_refs"))
                ):
                    if isinstance(ref, dict):
                        record = _source_record(
                            f"route_guard_correlations.{field}",
                            f"{item_id}:{source_index}:{ref_index}",
                            ref,
                            False,
                        )
                        if record:
                            records.append(record)

    openapi_surface = _read_json(
        run_dir / "openapi_security_surface.json", {}
    )
    for field in ("specs", "routes"):
        records += _records_from_items(
            f"openapi_security_surface.{field}",
            _list(openapi_surface.get(field)),
            ("route_id", "file"),
            False,
            include_direct=False,
        )

    inferred = _read_yaml(run_dir / "authz_matrix_inferred.yaml", {})
    routes = _dict(inferred.get("routes"))
    for route_key, route in sorted(routes.items()):
        if not isinstance(route, dict):
            continue
        for ref_index, ref in enumerate(_list(route.get("evidence_refs"))):
            if isinstance(ref, dict):
                record = _source_record("authz_inferred", f"{route_key}:{ref_index}", ref, False)
                if record:
                    records.append(record)

    graph = _read_json(run_dir / "event_graph.json", {})
    for node in _list(graph.get("nodes")):
        if not isinstance(node, dict):
            continue
        for ref in _list(node.get("evidence")):
            if isinstance(ref, str):
                refs.append((f"event:{node.get('event_id')}", ref))

    evidence_dir = run_dir / "evidence"
    if evidence_dir.is_dir():
        for evidence_file in sorted(evidence_dir.glob("E*.json")):
            evidence = _read_json(evidence_file, {})
            record = _source_record("evidence_file", evidence_file.stem, _dict(evidence), True)
            if record:
                records.append(record)

    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for record in records:
        key = (record["source"], record["item_id"], str(record["file"]), record["line"], record.get("snippet"))
        unique[key] = record
    return list(unique.values()), refs


def validate_evidence(run_dir: str | os.PathLike[str], repo_path: str | os.PathLike[str]) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    records, id_refs = _evidence_records(run_root)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    valid = 0
    line_counts: dict[Path, int] = {}

    for record in records:
        candidate, display, was_absolute = _path_from_value(record.get("file"), repo_root)
        if candidate is None:
            warnings.append({"type": "empty_evidence_path", "source": record["source"], "item_id": record["item_id"]})
            continue
        ref = {
            "file": record.get("file"),
            "start_line": record.get("line"),
            "end_line": record.get("line_end"),
            "snippet": record.get("snippet"),
        }
        allow_repo_absolute = record["source"] in {"report.findings", "code_health", "permission_risks", "evidence_file"}
        location_issues = validate_evidence_location(
            ref,
            repo_root,
            artifact=record["source"],
            item_id=record["item_id"],
            require_snippet=bool(record.get("require_snippet")),
            allow_repo_absolute=allow_repo_absolute,
        )
        if location_issues:
            for issue in location_issues:
                safe_ref = dict(issue.get("evidence_ref") or {})
                if "file" in safe_ref:
                    safe_ref["file"] = display
                issue["evidence_ref"] = safe_ref
                issue["source"] = record["source"]
                issue["file"] = display
                issue["type"] = issue.get("error_code")
                errors.append(issue)
            continue
        snippet = record.get("snippet")
        if snippet is not None and len(str(snippet)) > MAX_SNIPPET_CHARS:
            errors.append(
                {
                    "type": "snippet_budget_exceeded",
                    "source": record["source"],
                    "item_id": record["item_id"],
                    "file": display,
                    "chars": len(str(snippet)),
                    "budget": MAX_SNIPPET_CHARS,
                }
            )
            continue
        valid += 1

    evidence_files = {path.stem for path in (run_root / "evidence").glob("E*.json")} if (run_root / "evidence").is_dir() else set()
    for owner, ref in id_refs:
        if not re.fullmatch(r"E\d+", str(ref or "")) or ref not in evidence_files:
            errors.append({"type": "unresolved_evidence_ref", "source": owner, "evidence_ref": str(ref or "")})

    return {
        "passed": not errors,
        "records_checked": len(records),
        "records_valid": valid,
        "evidence_refs_checked": len(id_refs),
        "errors": errors,
        "warnings": warnings,
        "limits": {"max_snippet_chars": MAX_SNIPPET_CHARS},
    }


def _event_counts(event_graph: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for node in _list(event_graph.get("nodes")):
        if not isinstance(node, dict):
            continue
        event_type = str(node.get("type") or "")
        meta = _dict(node.get("meta"))
        if event_type == "cache_op" and meta.get("cache.kind"):
            event_type = str(meta["cache.kind"])
        aliases = {
            "tx_boundary": "transaction",
            "queue_dispatch": "queue.dispatch",
            "queue_consume": "queue.consume",
            "cache_read": "cache.read",
            "cache_write": "cache.write",
            "cache_invalidate": "cache.invalidate",
        }
        counts[aliases.get(event_type, event_type)] += 1
    return counts


def _status_counts(*item_groups: Iterable[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for items in item_groups:
        for item in items:
            if isinstance(item, dict):
                status = str(item.get("status") or "unknown").lower()
                counts[status] += 1
    return dict(sorted(counts.items()))


def _artifact_completeness(run_dir: Path) -> dict[str, Any]:
    artifacts = []
    for rel in REQUIRED_ARTIFACTS:
        present = (run_dir / Path(rel)).is_file()
        artifacts.append({"path": rel, "status": "available" if present else "missing"})
    missing = [row["path"] for row in artifacts if row["status"] == "missing"]
    return {
        "complete": not missing,
        "available_count": len(artifacts) - len(missing),
        "required_count": len(artifacts),
        "missing": missing,
        "artifacts": artifacts,
    }


def _execution_summary(pipeline_meta: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    stages = _list(pipeline_meta.get("stages"))
    failed = [stage for stage in stages if isinstance(stage, dict) and not stage.get("ok", False)]
    warnings = _list(coverage.get("warnings"))
    unsupported = [warning for warning in warnings if isinstance(warning, dict) and warning.get("type") == "unsupported_detected"]
    parse_warnings = [warning for warning in warnings if not (isinstance(warning, dict) and warning.get("type") == "unsupported_detected")]
    walk = _dict(coverage.get("walk"))
    return {
        "pipeline_completed": bool(pipeline_meta.get("completed")) and not failed,
        "failed_stage": str(pipeline_meta.get("failed_stage") or (failed[0].get("stage") if failed else "")),
        "duration_ms": int(pipeline_meta.get("duration_ms") or sum(int(stage.get("duration_ms") or 0) for stage in stages if isinstance(stage, dict))),
        "scanned_files": int(walk.get("included_files") or 0),
        "unsupported_count": len(unsupported),
        "unsupported_languages": sorted({str(item.get("language") or "unknown") for item in unsupported}),
        "unsupported_frameworks": sorted({str(item.get("framework") or "unknown") for item in unsupported}),
        "parse_warning_count": len(parse_warnings),
        "stage_count": len(stages),
    }


def _strict_verification_summary(pipeline_meta: dict[str, Any]) -> dict[str, Any]:
    stages = _list(pipeline_meta.get("stages"))
    stage = next((row for row in stages if isinstance(row, dict) and row.get("stage") == "verify_strict"), None)
    return {
        "attempted": stage is not None,
        "passed": bool(stage and stage.get("ok")),
        "exit_code": int(stage.get("exit_code") or 0) if stage else None,
        "output_summary": _clean_text(stage.get("output_summary"), 1000) if stage else "",
    }


def _review_statistics(run_dir: Path) -> dict[str, Any]:
    api = _read_json(run_dir / "api_surface.json", {})
    graph = _read_json(run_dir / "event_graph.json", {})
    patterns = _read_json(run_dir / "patterns.json", {})
    health = _read_json(run_dir / "code_health.json", {})
    permissions = _read_json(run_dir / "permission_risks.json", {})
    inferred = _read_yaml(run_dir / "authz_matrix_inferred.yaml", {})
    matrix = _read_json(run_dir / "review_risk_matrix.json", {})
    review = _read_json(run_dir / "repository_review_report.json", {})
    tx_correlations = _read_json(run_dir / "transaction_correlation_summary.json", {})
    review_context = _read_json(run_dir / "review_context_summary.json", {})
    guard_summary = _read_json(run_dir / "route_guard_summary.json", {})
    decorator_summary = _read_json(
        run_dir / "route_decorator_summary.json",
        {},
    )
    queue_cache = _read_json(
        run_dir / "queue_cache_validation.json",
        {},
    )
    queue_cache_summary = _dict(queue_cache.get("summary"))
    typeorm_validation = _read_json(
        run_dir / "typeorm_db_validation.json", {}
    )
    typeorm_summary = _dict(typeorm_validation.get("summary"))
    typescript_transaction_validation = _read_json(
        run_dir / "typescript_transaction_validation.json", {}
    )
    typescript_transaction_summary = _dict(
        typescript_transaction_validation.get("summary")
    )
    counts = _event_counts(graph)
    endpoints = _list(api.get("endpoints"))
    pattern_items = _list(patterns.get("patterns"))
    health_items = _list(health.get("findings"))
    permission_items = _list(permissions.get("risks"))
    human_items = _list(review.get("human_review_required"))
    inferred_routes = _dict(inferred.get("routes"))
    return {
        "api_endpoints": len(endpoints),
        "db_operations": counts.get("db.read", 0) + counts.get("db.write", 0) + counts.get("db_op", 0),
        "transaction_signals": counts.get("transaction", 0),
        "transaction_correlations": int(tx_correlations.get("total_correlations") or 0),
        "transaction_coverage": _dict(tx_correlations.get("counts_by_coverage_status")),
        "queue_dispatch": counts.get("queue.dispatch", 0),
        "queue_consume": counts.get("queue.consume", 0),
        "cache_operations": counts.get("cache.read", 0) + counts.get("cache.write", 0) + counts.get("cache.invalidate", 0),
        "queue_cache_validation": queue_cache_summary,
        "typeorm_db_validation": typeorm_summary,
        "typescript_transaction_validation": typescript_transaction_summary,
        "patterns": len(pattern_items),
        "code_health_findings": len(health_items),
        "permission_risks": len(permission_items),
        "authz_inferred_routes": len(inferred_routes),
        "review_decision": str(matrix.get("decision") or "UNKNOWN"),
        "human_review_required": int(matrix.get("human_review_required_count") or len(human_items)),
        "public_auth_entrypoints": int(review_context.get("public_auth_route_count") or 0),
        "protected_auth_operations": int(review_context.get("protected_auth_operation_count") or 0),
        "generated_files": int(review_context.get("generated_file_count") or 0),
        "seed_files": int(review_context.get("seed_file_count") or 0),
        "template_files": int(review_context.get("template_file_count") or 0),
        "findings_downweighted": int(review_context.get("findings_downweighted_count") or 0),
        "findings_excluded_from_primary_review": int(review_context.get("findings_excluded_from_primary_review_count") or 0),
        "route_guard_correlation": {
            "method_guards": int(guard_summary.get("method_guards") or 0),
            "controller_guards": int(
                guard_summary.get("controller_guards") or 0
            ),
            "global_guards": int(guard_summary.get("global_guards") or 0),
            "protected_method": int(
                guard_summary.get("protected_method") or 0
            ),
            "protected_controller": int(
                guard_summary.get("protected_controller") or 0
            ),
            "protected_global": int(
                guard_summary.get("protected_global") or 0
            ),
            "intentional_public_bypasses": int(
                guard_summary.get("intentional_public_bypasses") or 0
            ),
            "exact_matches": int(guard_summary.get("exact_matches") or 0),
            "template_matches": int(
                guard_summary.get("template_matches") or 0
            ),
            "openapi_only_routes": int(
                guard_summary.get("openapi_only_routes") or 0
            ),
            "openapi_protected_without_code_guard": int(
                guard_summary.get("openapi_protected_without_code_guard") or 0
            ),
            "unknown_routes": int(guard_summary.get("unknown_routes") or 0),
        },
        "route_decorator_classification": {
            "candidate_count": int(
                decorator_summary.get("candidate_count") or 0
            ),
            "accepted_route_count": int(
                decorator_summary.get("accepted_route_count") or 0
            ),
            "rejected_non_route_count": int(
                decorator_summary.get("rejected_non_route_count") or 0
            ),
            "unknown_count": int(
                decorator_summary.get("unknown_count") or 0
            ),
            "rejected_counts_by_decorator": _dict(
                decorator_summary.get("rejected_counts_by_decorator")
            ),
        },
        "status_distribution": _status_counts(pattern_items, health_items, permission_items),
    }


def build_case_validation(
    case_id: str,
    run_dir: str | os.PathLike[str],
    repo_path: str | os.PathLike[str],
    source_meta: dict[str, Any] | None = None,
    pipeline_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    coverage = _read_json(run_root / "coverage.json", {})
    matrix = _read_json(run_root / "authz_matrix_diff.json", {})
    evidence = validate_evidence(run_root, repo_path)
    completeness = _artifact_completeness(run_root)
    execution = _execution_summary(pipeline_meta or {}, coverage)
    strict_verification = _strict_verification_summary(pipeline_meta or {})
    matrix_mode = str(matrix.get("mode") or "missing")
    matrix_ok = matrix_mode == "inferred_only" and not (run_root / "authz_matrix_loaded.json").exists()
    validation_errors = []
    if matrix_mode != "inferred_only":
        validation_errors.append("real repository smoke must use inferred_only mode when no authority contract is provided")
    if (run_root / "authz_matrix_loaded.json").exists():
        validation_errors.append("authz_matrix_loaded.json must not be generated for an uncontracted real repository")
    return {
        "version": "real_repo_validation_v1",
        "case_id": case_id,
        "generated_at": _utc_now(),
        "source": source_meta or {},
        "execution": execution,
        "strict_verification": strict_verification,
        "artifact_completeness": completeness,
        "review_statistics": _review_statistics(run_root),
        "authz_matrix": {
            "mode": matrix_mode,
            "inferred_only_contract_respected": matrix_ok,
            "needs_confirmation": matrix_mode == "inferred_only",
        },
        "evidence_integrity": evidence,
        "validation_errors": validation_errors,
        "ready_for_manual_calibration": bool(
            execution["pipeline_completed"] and strict_verification["passed"] and completeness["complete"] and evidence["passed"] and matrix_ok and not validation_errors
        ),
        "limitations": [
            "This validation does not prove repository safety or backend correctness.",
            "Expected capabilities indicate observation opportunities, not required finding counts.",
            "Triage remains unreviewed until a human inspects the cited source.",
        ],
    }


def _relative_evidence(value: Any, repo_root: Path) -> Any:
    if isinstance(value, list):
        return [_relative_evidence(item, repo_root) for item in value[:5]]
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key in {"file", "path", "repo_path", "absolute_path"}:
                _candidate, display, _absolute = _path_from_value(item, repo_root)
                out[key] = display
            elif key == "snippet":
                out[key] = _clean_text(item, 300)
            else:
                out[key] = _relative_evidence(item, repo_root)
        return out
    return value


def _triage_item(category: str, artifact: str, item: dict[str, Any], repo_root: Path, index: int) -> dict[str, Any]:
    route = _dict(item.get("route"))
    raw_file = item.get("file") or item.get("path") or ""
    _candidate, display_file, _absolute = _path_from_value(raw_file, repo_root)
    rule_id = str(item.get("rule_id") or item.get("pattern_type") or "")
    item_id = str(item.get("pattern_id") or item.get("health_id") or item.get("risk_id") or item.get("item_id") or "")
    if not item_id:
        item_id = f"triage-{_stable_id(category, artifact, display_file, index)}"
    reason = item.get("reason") or item.get("summary") or item.get("title") or ""
    evidence = item.get("evidence_refs") or item.get("evidence") or item.get("source_refs") or []
    return {
        "item_id": item_id,
        "category": category,
        "source_artifact": artifact,
        "rule_id": rule_id,
        "file": display_file,
        "line": int(item.get("line_start") or item.get("start_line") or 0),
        "route": {"method": route.get("method"), "path": route.get("path")} if route else {},
        "reason": _clean_text(reason, 600),
        "evidence": _relative_evidence(evidence, repo_root),
        "triage_status": "unreviewed",
        "reviewer_note": "",
    }


def build_triage_template(case_id: str, run_dir: str | os.PathLike[str], repo_path: str | os.PathLike[str]) -> dict[str, Any]:
    run_root = Path(run_dir).resolve()
    repo_root = Path(repo_path).resolve()
    patterns = _list(_read_json(run_root / "patterns.json", {}).get("patterns"))
    health = _list(_read_json(run_root / "code_health.json", {}).get("findings"))
    permissions = _list(_read_json(run_root / "permission_risks.json", {}).get("risks"))
    review = _list(_read_json(run_root / "repository_review_report.json", {}).get("human_review_required"))
    inferred_payload = _read_yaml(run_root / "authz_matrix_inferred.yaml", {})
    inferred = []
    for route_key, route in sorted(_dict(inferred_payload.get("routes")).items()):
        row = dict(route) if isinstance(route, dict) else {}
        row.setdefault("item_id", f"authz-inferred-{_stable_id(route_key)}")
        row.setdefault("title", f"Inferred AuthZ route: {route_key}")
        refs = _list(row.get("evidence_refs"))
        if refs and isinstance(refs[0], dict):
            row.setdefault("file", refs[0].get("file") or refs[0].get("path"))
            row.setdefault("line_start", refs[0].get("start_line") or refs[0].get("line_start"))
        row.setdefault("source_refs", refs)
        inferred.append(row)
    groups = [
        ("backend_pattern", "patterns.json", patterns),
        ("code_health", "code_health.json", health),
        ("permission_risk", "permission_risks.json", permissions),
        ("authz_inferred", "authz_matrix_inferred.yaml", inferred),
        ("human_review_required", "repository_review_report.json", review),
    ]
    items = []
    for category, artifact, source_items in groups:
        for index, item in enumerate(source_items[:5]):
            if isinstance(item, dict):
                items.append(_triage_item(category, artifact, item, repo_root, index))
    counts = Counter(item["category"] for item in items)
    return {
        "version": "real_repo_triage_v1",
        "case_id": case_id,
        "generated_at": _utc_now(),
        "items": items,
        "counts_by_category": {category: int(counts.get(category, 0)) for category in TRIAGE_CATEGORIES},
        "note": "All entries are unreviewed by default. The harness never claims human confirmation.",
    }


def render_case_markdown(validation: dict[str, Any]) -> str:
    execution = _dict(validation.get("execution"))
    artifacts = _dict(validation.get("artifact_completeness"))
    stats = _dict(validation.get("review_statistics"))
    evidence = _dict(validation.get("evidence_integrity"))
    strict = _dict(validation.get("strict_verification"))
    lines = [
        f"# Real Repository Validation: {validation.get('case_id')}",
        "",
        "## Execution",
        "",
        f"- pipeline completed: {str(bool(execution.get('pipeline_completed'))).lower()}",
        f"- failed stage: {execution.get('failed_stage') or 'none'}",
        f"- duration ms: {execution.get('duration_ms', 0)}",
        f"- scanned files: {execution.get('scanned_files', 0)}",
        f"- unsupported signals: {execution.get('unsupported_count', 0)}",
        f"- parse warnings: {execution.get('parse_warning_count', 0)}",
        f"- strict verify attempted: {str(bool(strict.get('attempted'))).lower()}",
        f"- strict verify passed: {str(bool(strict.get('passed'))).lower()}",
        "",
        "## Artifact Completeness",
        "",
        f"- complete: {str(bool(artifacts.get('complete'))).lower()}",
        f"- available: {artifacts.get('available_count', 0)}/{artifacts.get('required_count', 0)}",
    ]
    for missing in _list(artifacts.get("missing")):
        lines.append(f"- missing: `{missing}`")
    lines += ["", "## Review Statistics", ""]
    for key, value in stats.items():
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## Evidence Integrity",
        "",
        f"- passed: {str(bool(evidence.get('passed'))).lower()}",
        f"- records checked: {evidence.get('records_checked', 0)}",
        f"- errors: {len(_list(evidence.get('errors')))}",
        f"- warnings: {len(_list(evidence.get('warnings')))}",
    ]
    for error in _list(evidence.get("errors"))[:20]:
        lines.append(f"- error: `{error.get('type')}` in `{error.get('file') or error.get('source')}`")
    lines += [
        "",
        "## Boundary",
        "",
        "This smoke result is evidence-guided validation, not a correctness or security proof.",
    ]
    return "\n".join(lines)


def write_case_outputs(
    case_dir: str | os.PathLike[str],
    validation: dict[str, Any],
    triage: dict[str, Any],
) -> None:
    root = Path(case_dir)
    _write_json(root / "validation.json", validation)
    _write_text(root / "validation.md", render_case_markdown(validation))
    _write_json(root / "triage-template.json", triage)


def build_overall_summary(root_dir: str | os.PathLike[str], config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root_dir)
    cases = []
    for validation_path in sorted((root / "cases").glob("*/validation.json")):
        validation = _read_json(validation_path, {})
        source = _dict(validation.get("source"))
        stats = _dict(validation.get("review_statistics"))
        cases.append(
            {
                "case_id": validation.get("case_id") or validation_path.parent.name,
                "name": source.get("name") or validation.get("case_id") or validation_path.parent.name,
                "repository_url": source.get("repository_url") or "local fixture",
                "commit_sha": source.get("commit_sha") or source.get("resolved_commit") or "local",
                "license": source.get("license") or "n/a",
                "pipeline_completed": bool(_dict(validation.get("execution")).get("pipeline_completed")),
                "artifacts_complete": bool(_dict(validation.get("artifact_completeness")).get("complete")),
                "evidence_integrity_passed": bool(_dict(validation.get("evidence_integrity")).get("passed")),
                "strict_verify_passed": bool(_dict(validation.get("strict_verification")).get("passed")),
                "authz_matrix_mode": _dict(validation.get("authz_matrix")).get("mode") or "missing",
                "ready_for_manual_calibration": bool(validation.get("ready_for_manual_calibration")),
                "review_statistics": stats,
                "validation_error_count": len(_list(validation.get("validation_errors"))) + len(_list(_dict(validation.get("evidence_integrity")).get("errors"))),
            }
        )
    status = "complete" if cases and all(case["ready_for_manual_calibration"] for case in cases) else "needs_review"
    return {
        "version": "real_repo_smoke_summary_v1",
        "generated_at": _utc_now(),
        "status": status,
        "case_count": len(cases),
        "cases": cases,
        "manual_triage_status": "unreviewed",
        "calibration_notes": [
            "Review triage-template.json before changing any detection rule.",
            "A single repository sample is insufficient to justify rule changes.",
        ],
        "limitations": [
            "The smoke does not execute target repository code.",
            "Results do not prove that a repository is safe or correct.",
            "Inferred AuthZ matrices require project-owner confirmation.",
        ],
        "configured_case_count": len(_list((config or {}).get("cases"))),
    }


def render_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Real Repository Review Smoke Summary",
        "",
        f"- status: {summary.get('status')}",
        f"- cases: {summary.get('case_count', 0)}",
        f"- manual triage: {summary.get('manual_triage_status')}",
        "",
        "## Cases",
        "",
        "| Case | Commit | Pipeline | Artifacts | Evidence | AuthZ mode | Review decision |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for case in _list(summary.get("cases")):
        stats = _dict(case.get("review_statistics"))
        lines.append(
            "| {case} | `{commit}` | {pipeline} | {artifacts} | {evidence} | {authz} | {decision} |".format(
                case=case.get("case_id"),
                commit=str(case.get("commit_sha") or "")[:12],
                pipeline="complete" if case.get("pipeline_completed") else "failed",
                artifacts="complete" if case.get("artifacts_complete") else "missing",
                evidence="pass" if case.get("evidence_integrity_passed") else "fail",
                authz=case.get("authz_matrix_mode"),
                decision=stats.get("review_decision") or "UNKNOWN",
            )
        )
    lines += [
        "",
        "## Manual Calibration",
        "",
        "Triage templates are generated with `unreviewed` status. No automated result is presented as human confirmation.",
        "",
        "## Boundary",
        "",
        "This protocol checks reproducibility, artifact completeness, and evidence integrity. It does not prove repository safety or correctness.",
    ]
    return "\n".join(lines)


def write_summary_outputs(root_dir: str | os.PathLike[str], summary: dict[str, Any]) -> None:
    root = Path(root_dir)
    _write_json(root / "summary.json", summary)
    _write_text(root / "summary.md", render_summary_markdown(summary))


def write_inferred_authz_outputs(run_dir: str | os.PathLike[str]) -> None:
    """Generate inferred-only AuthZ outputs without auto-discovering a local fixture contract."""
    from reposense.analysis.authz.authz_matrix_diff import inferred_only_diff
    from reposense.analysis.authz.authz_matrix_infer import infer_authz_matrix, render_inferred_yaml
    from reposense.analysis.authz.authz_matrix_render import render_matrix_negative_test_plan, render_matrix_report

    root = Path(run_dir)
    surface = _read_json(root / "permission_surface.json", {})
    risks = _read_json(root / "permission_risks.json", {})
    inferred = infer_authz_matrix(surface, risks)
    diff = inferred_only_diff(surface)
    _write_text(root / "authz_matrix_inferred.yaml", render_inferred_yaml(inferred))
    _write_json(root / "authz_matrix_diff.json", diff)
    _write_text(root / "authz_matrix_report.md", render_matrix_report(None, inferred, diff))
    _write_text(root / "authz_negative_test_plan.md", render_matrix_negative_test_plan(risks, diff))


def _cmd_validate(args: argparse.Namespace) -> int:
    source_meta = _read_json(Path(args.source_meta), {}) if args.source_meta else {}
    pipeline_meta = _read_json(Path(args.pipeline_meta), {}) if args.pipeline_meta else {}
    validation = build_case_validation(args.case_id, args.run_dir, args.repo_path, source_meta, pipeline_meta)
    triage = build_triage_template(args.case_id, args.run_dir, args.repo_path)
    write_case_outputs(args.case_dir, validation, triage)
    print(json.dumps({"case_id": args.case_id, "ready": validation["ready_for_manual_calibration"]}))
    return 0 if validation["ready_for_manual_calibration"] else 2


def _cmd_summary(args: argparse.Namespace) -> int:
    config = load_case_config(args.config) if args.config else {}
    summary = build_overall_summary(args.root, config)
    write_summary_outputs(args.root, summary)
    print(json.dumps({"status": summary["status"], "case_count": summary["case_count"]}))
    return 0 if summary["status"] == "complete" else 2


def _cmd_inferred_authz(args: argparse.Namespace) -> int:
    write_inferred_authz_outputs(args.run_dir)
    print(json.dumps({"mode": "inferred_only", "run_dir": args.run_dir}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--case-id", required=True)
    validate.add_argument("--case-dir", required=True)
    validate.add_argument("--run-dir", required=True)
    validate.add_argument("--repo-path", required=True)
    validate.add_argument("--source-meta")
    validate.add_argument("--pipeline-meta")
    validate.set_defaults(func=_cmd_validate)
    summary = sub.add_parser("summary")
    summary.add_argument("--root", required=True)
    summary.add_argument("--config")
    summary.set_defaults(func=_cmd_summary)
    inferred = sub.add_parser("inferred-authz")
    inferred.add_argument("--run-dir", required=True)
    inferred.set_defaults(func=_cmd_inferred_authz)
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
