import json
import os
import sqlite3
from pathlib import Path

from .location import canonicalize_evidence_ref, is_absolute_path


EVIDENCE_FILE_MISSING = "EVIDENCE_FILE_MISSING"
EVIDENCE_ABSOLUTE_PATH = "EVIDENCE_ABSOLUTE_PATH"
EVIDENCE_LINE_START_INVALID = "EVIDENCE_LINE_START_INVALID"
EVIDENCE_LINE_RANGE_INVALID = "EVIDENCE_LINE_RANGE_INVALID"
EVIDENCE_LINE_OUT_OF_RANGE = "EVIDENCE_LINE_OUT_OF_RANGE"
EVIDENCE_SNIPPET_MISSING = "EVIDENCE_SNIPPET_MISSING"


def _issue(artifact, item_id, evidence_ref, code, reason):
    return {
        "artifact": str(artifact or ""),
        "item_id": str(item_id or ""),
        "evidence_ref": evidence_ref if isinstance(evidence_ref, dict) else {},
        "error_code": code,
        "reason": reason,
    }


def _raw_location(ref):
    file_value = ref.get("file") or ref.get("path") or ref.get("repo_path") or ref.get("absolute_path")
    start = ref.get("start_line") if ref.get("start_line") is not None else ref.get("line_start")
    end = ref.get("end_line") if ref.get("end_line") is not None else ref.get("line_end")
    try:
        start = int(start)
    except (TypeError, ValueError):
        start = None
    try:
        end = int(end) if end is not None else start
    except (TypeError, ValueError):
        end = None
    return str(file_value or "").strip(), start, end


def _path_is_within_repository(raw_file, repo_root, allow_repo_absolute):
    normalized = raw_file.replace("\\", "/")
    for token in ("<REPO_ROOT>", "${REPO_ROOT}"):
        if normalized.startswith(token + "/"):
            normalized = normalized[len(token) + 1 :]
            break
    if is_absolute_path(raw_file):
        if not allow_repo_absolute or not repo_root:
            return False
        try:
            Path(raw_file).resolve().relative_to(Path(repo_root).resolve())
            return True
        except (OSError, ValueError):
            return False
    path = Path(normalized)
    return bool(normalized) and not any(part == ".." for part in path.parts)


def validate_evidence_location(
    ref,
    repo_root,
    artifact="",
    item_id="",
    require_snippet=False,
    allow_repo_absolute=False,
    check_file=True,
):
    """Validate one code evidence location and return stable issue dictionaries."""
    if not isinstance(ref, dict):
        return [_issue(artifact, item_id, {}, EVIDENCE_FILE_MISSING, "evidence reference is not an object")]
    raw_file, start, end = _raw_location(ref)
    issues = []
    if not raw_file:
        issues.append(_issue(artifact, item_id, ref, EVIDENCE_FILE_MISSING, "source file is missing"))
        return issues
    if is_absolute_path(raw_file) and not allow_repo_absolute:
        issues.append(_issue(artifact, item_id, ref, EVIDENCE_ABSOLUTE_PATH, "source file must be repository-relative"))
        return issues
    canonical = canonicalize_evidence_ref(ref, repo_root=repo_root, allow_repo_absolute=allow_repo_absolute)
    if start is None or start < 1:
        issues.append(_issue(artifact, item_id, ref, EVIDENCE_LINE_START_INVALID, "line_start must be an integer >= 1"))
    if start is not None and end is not None and end < start:
        issues.append(_issue(artifact, item_id, ref, EVIDENCE_LINE_RANGE_INVALID, "line_end must be >= line_start"))
    path_valid = _path_is_within_repository(raw_file, repo_root, allow_repo_absolute)
    if canonical is None:
        path_code = EVIDENCE_ABSOLUTE_PATH if is_absolute_path(raw_file) else EVIDENCE_FILE_MISSING
        if not path_valid and not any(issue.get("error_code") == path_code for issue in issues):
            reason = "source path is outside the repository" if is_absolute_path(raw_file) else "source path escapes the repository"
            issues.append(_issue(artifact, item_id, ref, path_code, reason))
        return issues
    if require_snippet and not str(ref.get("snippet") or "").strip():
        issues.append(_issue(artifact, item_id, ref, EVIDENCE_SNIPPET_MISSING, "source snippet is missing"))
    if check_file and repo_root:
        source_path = Path(repo_root).resolve() / canonical["file"]
        if not source_path.is_file():
            issues.append(_issue(artifact, item_id, ref, EVIDENCE_FILE_MISSING, "source file does not exist"))
        else:
            try:
                with source_path.open("r", encoding="utf-8", errors="replace") as handle:
                    line_count = sum(1 for _ in handle)
                if canonical["end_line"] > line_count:
                    issues.append(
                        _issue(
                            artifact,
                            item_id,
                            ref,
                            EVIDENCE_LINE_OUT_OF_RANGE,
                            f"line_end {canonical['end_line']} exceeds source line count {line_count}",
                        )
                    )
            except OSError:
                issues.append(_issue(artifact, item_id, ref, EVIDENCE_FILE_MISSING, "source file could not be read"))
    return issues


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return default


def _items(obj, key):
    value = obj.get(key) if isinstance(obj, dict) else []
    return value if isinstance(value, list) else []


def _item_id(item, index):
    for key in ("pattern_id", "risk_id", "health_id", "diff_id", "fid", "event_id", "item_id", "rule_id"):
        if isinstance(item, dict) and item.get(key) not in (None, ""):
            return str(item[key])
    return str(index)


def _validate_items(issues, artifact, items, repo_root, direct=False, direct_snippet=False):
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_id = _item_id(item, index)
        if direct and (item.get("file") or item.get("path")):
            issues.extend(
                validate_evidence_location(
                    item,
                    repo_root,
                    artifact=artifact,
                    item_id=item_id,
                    require_snippet=direct_snippet,
                    allow_repo_absolute=True,
                )
            )
        for ref_index, ref in enumerate(item.get("evidence_refs") if isinstance(item.get("evidence_refs"), list) else []):
            issues.extend(
                validate_evidence_location(
                    ref,
                    repo_root,
                    artifact=artifact,
                    item_id=f"{item_id}:evidence:{ref_index}",
                )
            )


def _validate_sqlite_evidence(run_dir, repo_root):
    path = os.path.join(run_dir, "detections.sqlite")
    if not os.path.isfile(path):
        return []
    issues = []
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("select eid, path, start_line, end_line, snippet from evidence").fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()
    for eid, file_path, start, end, snippet in rows:
        issues.extend(
            validate_evidence_location(
                {"file": file_path, "start_line": start, "end_line": end, "snippet": snippet},
                repo_root,
                artifact="detections.sqlite:evidence",
                item_id=f"E{eid}",
                require_snippet=True,
                allow_repo_absolute=True,
            )
        )
    return issues


def validate_run_evidence_locations(run_dir, repo_root):
    """Validate structured code evidence across run artifacts."""
    issues = _validate_sqlite_evidence(run_dir, repo_root)
    specs = [
        ("report.json", "findings", True, True),
        ("patterns.json", "patterns", False, False),
        (os.path.join("ai_risks", "risks.json"), "risk_items", False, False),
        ("code_health.json", "findings", True, True),
        ("maintainability_risks.json", "risks", False, False),
        ("permission_risks.json", "risks", True, True),
        ("authz_matrix_diff.json", "diffs", False, False),
        ("route_intent_annotations.json", "annotations", False, False),
        ("file_context_annotations.json", "annotations", False, False),
        (
            "route_decorator_classifications.json",
            "classifications",
            False,
            False,
        ),
        ("queue_cache_validation.json", "queue_observations", False, False),
        ("queue_cache_validation.json", "cache_observations", False, False),
        ("queue_reliability_risks.json", "risks", False, False),
        (
            "queue_retry_idempotency_validation.json",
            "triage_items",
            False,
            False,
        ),
        ("typeorm_db_operations.json", "operations", True, False),
        ("typeorm_db_validation.json", "operations", True, False),
        (
            "typescript_transaction_validation.json",
            "correlations",
            False,
            False,
        ),
    ]
    for rel, key, direct, snippet in specs:
        obj = _read_json(os.path.join(run_dir, rel), {})
        _validate_items(issues, rel.replace("\\", "/"), _items(obj, key), repo_root, direct, snippet)

    review = _read_json(os.path.join(run_dir, "repository_review_report.json"), {})
    _validate_items(
        issues,
        "repository_review_report.json",
        _items(review, "human_review_required"),
        repo_root,
    )
    matrix = _read_json(os.path.join(run_dir, "review_risk_matrix.json"), {})
    _validate_items(issues, "review_risk_matrix.json", _items(matrix, "top_risks"), repo_root)
    correlations = _read_json(os.path.join(run_dir, "transaction_correlations.json"), {})
    for index, item in enumerate(_items(correlations, "correlations")):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("correlation_id") or index)
        for field in ("transaction_evidence_refs", "callsite_evidence_refs", "db_write_evidence_refs"):
            refs = item.get(field) if isinstance(item.get(field), list) else []
            for ref_index, ref in enumerate(refs):
                issues.extend(validate_evidence_location(
                    ref, repo_root, artifact="transaction_correlations.json",
                    item_id=f"{item_id}:{field}:{ref_index}",
                ))
    queue_correlations = _read_json(
        os.path.join(run_dir, "queue_reliability_correlations.json"), {}
    )
    for index, item in enumerate(
        _items(queue_correlations, "correlations")
    ):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("correlation_id") or index)
        for field in ("producer_refs", "consumer_refs", "evidence_refs"):
            refs = item.get(field) if isinstance(item.get(field), list) else []
            for ref_index, ref in enumerate(refs):
                issues.extend(
                    validate_evidence_location(
                        ref,
                        repo_root,
                        artifact="queue_reliability_correlations.json",
                        item_id=f"{item_id}:{field}:{ref_index}",
                    )
                )
        for effect_index, effect in enumerate(
            item.get("consumer_side_effects") or []
        ):
            refs = (
                effect.get("evidence_refs")
                if isinstance(effect, dict)
                and isinstance(effect.get("evidence_refs"), list)
                else []
            )
            for ref_index, ref in enumerate(refs):
                issues.extend(
                    validate_evidence_location(
                        ref,
                        repo_root,
                        artifact="queue_reliability_correlations.json",
                        item_id=(
                            f"{item_id}:consumer_side_effects:"
                            f"{effect_index}:{ref_index}"
                        ),
                    )
                )
    guard_correlations = _read_json(
        os.path.join(run_dir, "route_guard_correlations.json"), {}
    )
    for index, item in enumerate(_items(guard_correlations, "correlations")):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("correlation_id") or index)
        for field in (
            "code_route_refs",
            "openapi_route_refs",
            "evidence_refs",
        ):
            refs = item.get(field) if isinstance(item.get(field), list) else []
            for ref_index, ref in enumerate(refs):
                issues.extend(
                    validate_evidence_location(
                        ref,
                        repo_root,
                        artifact="route_guard_correlations.json",
                        item_id=f"{item_id}:{field}:{ref_index}",
                    )
                )
        for field in ("guard_sources", "public_bypass_sources"):
            sources = item.get(field) if isinstance(item.get(field), list) else []
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict):
                    continue
                refs = (
                    source.get("evidence_refs")
                    if isinstance(source.get("evidence_refs"), list)
                    else []
                )
                for ref_index, ref in enumerate(refs):
                    issues.extend(
                        validate_evidence_location(
                            ref,
                            repo_root,
                            artifact="route_guard_correlations.json",
                            item_id=(
                                f"{item_id}:{field}:{source_index}:"
                                f"evidence:{ref_index}"
                            ),
                        )
                    )
    openapi_surface = _read_json(
        os.path.join(run_dir, "openapi_security_surface.json"), {}
    )
    for key in ("specs", "routes"):
        _validate_items(
            issues,
            "openapi_security_surface.json",
            _items(openapi_surface, key),
            repo_root,
        )
    return issues
