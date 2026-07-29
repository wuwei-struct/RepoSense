import hashlib
import json
from pathlib import PurePosixPath

from ...evidence.location import canonicalize_evidence_ref


RESOLUTION_STATUSES = {
    "resolved_direct_import",
    "resolved_alias_import",
    "resolved_reexport",
    "resolved_barrel",
    "resolved_local_assignment",
    "ambiguous",
    "unresolved",
}


def stable_id(prefix, *parts):
    raw = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return f"{prefix}-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_relative_path(value):
    path = str(value or "").replace("\\", "/")
    if not path or PurePosixPath(path).is_absolute() or ":" in path.split("/", 1)[0]:
        raise ValueError("TypeScript resolution paths must be repository-relative")
    return PurePosixPath(path).as_posix()


def normalize_refs(values):
    refs = []
    seen = set()
    for value in values if isinstance(values, list) else []:
        ref = canonicalize_evidence_ref(value)
        if ref is None:
            continue
        key = (
            ref["file"],
            ref["start_line"],
            ref["end_line"],
            str(ref.get("source_type") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        refs.append(ref)
    return sorted(
        refs,
        key=lambda item: (
            item["file"],
            item["start_line"],
            item["end_line"],
            str(item.get("source_type") or ""),
        ),
    )


def normalize_resolution(raw):
    item = dict(raw or {})
    status = str(item.get("resolution_status") or "unresolved")
    if status not in RESOLUTION_STATUSES:
        raise ValueError(f"unsupported TypeORM alias resolution status: {status}")
    item["resolution_status"] = status
    for key in ("source_file", "resolved_file"):
        item[key] = (
            normalize_relative_path(item[key]) if item.get(key) else ""
        )
    for key in (
        "source_class",
        "source_method",
        "receiver_name",
        "declared_type",
        "imported_symbol",
        "resolved_class",
        "resolved_method",
    ):
        item[key] = str(item.get(key) or "")
    item["callsite_line"] = (
        int(item["callsite_line"])
        if isinstance(item.get("callsite_line"), int)
        and item["callsite_line"] >= 1
        else None
    )
    item["resolution_depth"] = max(0, int(item.get("resolution_depth") or 0))
    item["confidence"] = round(float(item.get("confidence") or 0.0), 3)
    item["db_operation_ids"] = sorted(
        set(str(value) for value in (item.get("db_operation_ids") or []) if value)
    )
    item["limitations"] = sorted(
        set(str(value) for value in (item.get("limitations") or []) if value)
    )
    for key in (
        "import_evidence_refs",
        "dependency_evidence_refs",
        "callsite_evidence_refs",
        "target_evidence_refs",
    ):
        item[key] = normalize_refs(item.get(key))
    if not item.get("resolution_id"):
        item["resolution_id"] = stable_id(
            "ts-resolution",
            item["source_file"],
            item["source_class"],
            item["source_method"],
            item["receiver_name"],
            item["callsite_line"],
            item["resolved_file"],
            item["resolved_class"],
            item["resolved_method"],
            item["resolution_status"],
        )
    return item


def stable_sort_resolutions(values):
    return sorted(
        [normalize_resolution(value) for value in (values or [])],
        key=lambda item: (
            item["source_file"],
            int(item.get("callsite_line") or 0),
            item["receiver_name"],
            item["resolved_file"],
            item["resolved_class"],
            item["resolved_method"],
            item["resolution_id"],
        ),
    )
