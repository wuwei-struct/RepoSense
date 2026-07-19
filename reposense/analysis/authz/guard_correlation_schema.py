import hashlib


MATCH_STATUSES = {
    "exact_match",
    "template_match",
    "code_only",
    "openapi_only",
    "ambiguous",
}
AUTH_STATUSES = {
    "protected_method",
    "protected_controller",
    "protected_global",
    "intentional_public_bypass",
    "unprotected",
    "unknown",
}
ROLE_STATUSES = {
    "role_guard_observed",
    "permission_guard_observed",
    "no_role_guard_observed",
    "not_applicable",
    "unknown",
}


def stable_id(prefix, *parts):
    material = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha1(material.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _refs(value):
    rows = value if isinstance(value, list) else []
    return [dict(row) for row in rows if isinstance(row, dict)]


def normalize_correlation(item):
    row = item if isinstance(item, dict) else {}
    method = str(row.get("method") or "").upper()
    path = str(row.get("path") or "")
    match_status = str(row.get("match_status") or "code_only")
    auth_status = str(row.get("effective_auth_status") or "unknown")
    role_status = str(row.get("effective_role_status") or "unknown")
    if match_status not in MATCH_STATUSES:
        match_status = "ambiguous"
    if auth_status not in AUTH_STATUSES:
        auth_status = "unknown"
    if role_status not in ROLE_STATUSES:
        role_status = "unknown"
    sources = row.get("guard_sources") if isinstance(row.get("guard_sources"), list) else []
    bypasses = row.get("public_bypass_sources") if isinstance(row.get("public_bypass_sources"), list) else []
    limitations = sorted({str(value) for value in (row.get("limitations") or []) if str(value)})
    return {
        "correlation_id": str(
            row.get("correlation_id")
            or stable_id(
                "route-guard",
                method,
                path,
                match_status,
                auth_status,
                role_status,
                ",".join(str(source.get("guard_id") or "") for source in sources),
            )
        ),
        "method": method,
        "path": path,
        "code_route_refs": _refs(row.get("code_route_refs")),
        "openapi_route_refs": _refs(row.get("openapi_route_refs")),
        "match_status": match_status,
        "effective_auth_status": auth_status,
        "effective_role_status": role_status,
        "guard_sources": [dict(source) for source in sources if isinstance(source, dict)],
        "public_bypass_sources": [dict(source) for source in bypasses if isinstance(source, dict)],
        "openapi_security_expectation": str(row.get("openapi_security_expectation") or "not_available"),
        "confidence": round(float(row.get("confidence") or 0.0), 4),
        "evidence_refs": _refs(row.get("evidence_refs")),
        "limitations": limitations,
    }


def normalize_payload(correlations, limitations=None):
    rows = [normalize_correlation(row) for row in correlations or []]
    rows.sort(
        key=lambda row: (
            row["method"],
            row["path"],
            row["match_status"],
            row["correlation_id"],
        )
    )
    return {
        "version": "route_guard_correlations_v1",
        "correlations": rows,
        "limitations": sorted({str(value) for value in (limitations or []) if str(value)}),
    }
