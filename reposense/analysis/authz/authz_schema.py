import hashlib


VALID_SEVERITIES = {"low", "medium", "high"}
VALID_STATUSES = {"confirmed", "suspected"}


def _clean(value, limit=260):
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def stable_id(prefix, *parts):
    digest = hashlib.sha1("|".join(str(p or "") for p in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def normalize_route(item):
    x = item if isinstance(item, dict) else {}
    method = str(x.get("method") or "").upper()
    path = str(x.get("path") or "")
    file_path = str(x.get("file") or "").replace("\\", "/")
    line = int(x.get("line_start") or 1)
    return {
        "surface_id": str(x.get("surface_id") or stable_id("ps", method, path, file_path, line)),
        "method": method,
        "path": path,
        "file": file_path,
        "line_start": line,
        "line_end": int(x.get("line_end") or line),
        "language": str(x.get("language") or "unknown"),
        "framework": str(x.get("framework") or "unknown"),
        "source_kind": str(x.get("source_kind") or "code"),
        "write_like": bool(x.get("write_like")),
        "sensitive": bool(x.get("sensitive")),
        "auth_signals": x.get("auth_signals") if isinstance(x.get("auth_signals"), list) else [],
        "role_permission_signals": x.get("role_permission_signals") if isinstance(x.get("role_permission_signals"), list) else [],
        "ownership_signals": x.get("ownership_signals") if isinstance(x.get("ownership_signals"), list) else [],
        "tenant_boundary_signals": x.get("tenant_boundary_signals") if isinstance(x.get("tenant_boundary_signals"), list) else [],
        "source_refs": x.get("source_refs") if isinstance(x.get("source_refs"), list) else [],
        "intent": str(x.get("intent") or "unknown"),
        "intent_confidence": float(x.get("intent_confidence") or 0.0),
        "intent_signals": x.get("intent_signals") if isinstance(x.get("intent_signals"), list) else [],
        "intent_limitations": x.get("intent_limitations") if isinstance(x.get("intent_limitations"), list) else [],
        "auth_guard_expected": bool(x.get("auth_guard_expected", True)),
        "intent_annotation_id": str(x.get("intent_annotation_id") or ""),
        "effective_auth_status": str(x.get("effective_auth_status") or "unknown"),
        "effective_role_status": str(x.get("effective_role_status") or "unknown"),
        "guard_scope": str(x.get("guard_scope") or ""),
        "public_bypass": bool(x.get("public_bypass")),
        "guard_correlation_id": str(x.get("guard_correlation_id") or ""),
        "guard_correlation_confidence": float(x.get("guard_correlation_confidence") or 0.0),
        "guard_correlation_limitations": x.get("guard_correlation_limitations") if isinstance(x.get("guard_correlation_limitations"), list) else [],
        "guard_correlation_match_status": str(x.get("guard_correlation_match_status") or ""),
        "openapi_security_expectation": str(x.get("openapi_security_expectation") or "not_available"),
        "guard_sources": x.get("guard_sources") if isinstance(x.get("guard_sources"), list) else [],
        "public_bypass_sources": x.get("public_bypass_sources") if isinstance(x.get("public_bypass_sources"), list) else [],
    }


def normalize_guard(item):
    x = item if isinstance(item, dict) else {}
    file_path = str(x.get("file") or "").replace("\\", "/")
    line = int(x.get("line_start") or 1)
    gtype = str(x.get("guard_type") or "auth")
    return {
        "guard_id": str(x.get("guard_id") or stable_id("guard", gtype, file_path, line, x.get("snippet"))),
        "guard_type": gtype,
        "file": file_path,
        "line_start": line,
        "snippet": _clean(x.get("snippet")),
        "signals": x.get("signals") if isinstance(x.get("signals"), list) else [],
        "confidence": float(x.get("confidence") or 0.0),
    }


def normalize_frontend_signal(item):
    x = item if isinstance(item, dict) else {}
    file_path = str(x.get("file") or "").replace("\\", "/")
    line = int(x.get("line_start") or 1)
    return {
        "signal_id": str(x.get("signal_id") or stable_id("fps", file_path, line, x.get("snippet"))),
        "file": file_path,
        "line_start": line,
        "snippet": _clean(x.get("snippet")),
        "signals": x.get("signals") if isinstance(x.get("signals"), list) else [],
        "possible_action": _clean(x.get("possible_action"), limit=120),
        "confidence": float(x.get("confidence") or 0.0),
    }


def normalize_risk(item):
    x = item if isinstance(item, dict) else {}
    route = x.get("route") if isinstance(x.get("route"), dict) else {}
    severity = str(x.get("severity") or "low").lower()
    if severity not in VALID_SEVERITIES:
        severity = "low"
    status = str(x.get("status") or "suspected").lower()
    if status not in VALID_STATUSES:
        status = "suspected"
    rule_id = str(x.get("rule_id") or "")
    file_path = str(x.get("file") or "").replace("\\", "/")
    line = int(x.get("line_start") or 1)
    signals = x.get("signals") if isinstance(x.get("signals"), list) else []
    return {
        "risk_id": str(x.get("risk_id") or stable_id("authz", rule_id, route.get("method"), route.get("path"), file_path, line, ",".join(signals))),
        "rule_id": rule_id,
        "category": "permission",
        "title": _clean(x.get("title"), limit=160),
        "severity": severity,
        "status": status,
        "confidence": float(x.get("confidence") or 0.0),
        "route": {"method": str(route.get("method") or "").upper(), "path": str(route.get("path") or "")},
        "file": file_path,
        "line_start": line,
        "line_end": int(x.get("line_end") or line),
        "snippet": _clean(x.get("snippet")),
        "reason": _clean(x.get("reason"), limit=340),
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "signals": [str(v) for v in signals if str(v or "").strip()],
        "limitations": x.get("limitations") if isinstance(x.get("limitations"), list) else [],
        "suggested_human_review": bool(x.get("suggested_human_review", True)),
    }
