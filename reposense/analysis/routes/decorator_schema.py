import hashlib


CONTEXTS = {"class", "method", "property", "parameter", "unknown"}
CLASSIFICATIONS = {"route", "controller", "non_route", "unknown"}
ROUTE_DECORATORS = {
    "Get": "GET",
    "Post": "POST",
    "Put": "PUT",
    "Patch": "PATCH",
    "Delete": "DELETE",
    "Options": "OPTIONS",
    "Head": "HEAD",
    "All": "ALL",
}


def stable_id(*parts):
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def evidence_ref(file_path, line_start, snippet):
    line = int(line_start or 0)
    if not file_path or line < 1:
        return []
    return [
        {
            "source_type": "route_decorator",
            "file": str(file_path).replace("\\", "/"),
            "start_line": line,
            "end_line": line,
            "snippet": str(snippet or "")[:500],
        }
    ]


def normalize_classification(row):
    context = str(row.get("context") or "unknown")
    classification = str(row.get("classification") or "unknown")
    if context not in CONTEXTS:
        raise ValueError(f"invalid decorator context: {context}")
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"invalid decorator classification: {classification}")
    file_path = str(row.get("file") or "").replace("\\", "/")
    line = int(row.get("line_start") or 0)
    decorator = str(row.get("decorator_name") or "")
    return {
        "classification_id": str(
            row.get("classification_id")
            or stable_id(
                "route-decorator",
                file_path,
                line,
                decorator,
                context,
                classification,
            )
        ),
        "file": file_path,
        "line_start": line,
        "decorator_name": decorator,
        "context": context,
        "classification": classification,
        "reason": str(row.get("reason") or ""),
        "route_method": str(row.get("route_method") or ""),
        "evidence_refs": list(row.get("evidence_refs") or []),
        "limitations": sorted(set(row.get("limitations") or [])),
    }


def summarize_classifications(rows, limitations=None):
    rejected = {}
    for row in rows:
        if row.get("classification") != "non_route":
            continue
        name = str(row.get("decorator_name") or "")
        rejected[name] = rejected.get(name, 0) + 1
    return {
        "version": "route_decorator_summary_v1",
        "candidate_count": len(rows),
        "accepted_route_count": len(
            [row for row in rows if row.get("classification") == "route"]
        ),
        "controller_count": len(
            [row for row in rows if row.get("classification") == "controller"]
        ),
        "rejected_non_route_count": len(
            [row for row in rows if row.get("classification") == "non_route"]
        ),
        "unknown_count": len(
            [row for row in rows if row.get("classification") == "unknown"]
        ),
        "rejected_counts_by_decorator": dict(sorted(rejected.items())),
        "limitations": list(limitations or []),
    }
