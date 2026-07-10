import hashlib


VALID_MODES = {"contract_diff", "inferred_only"}
VALID_SEVERITIES = {"low", "medium", "high"}
VALID_STATUSES = {"confirmed", "suspected"}


def stable_matrix_id(*parts):
    digest = hashlib.sha1("|".join(str(p or "") for p in parts).encode("utf-8")).hexdigest()[:12]
    return "azm-" + digest


def normalize_expected_route(key, item):
    x = item if isinstance(item, dict) else {}
    parts = str(key or "").split(" ", 1)
    method = parts[0].upper() if parts else ""
    path = parts[1] if len(parts) > 1 else ""
    expected = x.get("expected") if isinstance(x.get("expected"), dict) else {}
    return {
        "route_key": f"{method} {path}".strip(),
        "method": method,
        "path": path,
        "resource": str(x.get("resource") or ""),
        "action": str(x.get("action") or ""),
        "expected": {
            "auth": str(expected.get("auth") or "unknown"),
            "roles": expected.get("roles") if isinstance(expected.get("roles"), list) else [],
            "permissions": expected.get("permissions") if isinstance(expected.get("permissions"), list) else [],
            "ownership_check": str(expected.get("ownership_check") or "unknown"),
            "tenant_boundary": str(expected.get("tenant_boundary") or "unknown"),
            "transaction": str(expected.get("transaction") or "unknown"),
            "audit_log": str(expected.get("audit_log") or "unknown"),
        },
        "unrecognized": {k: v for k, v in x.items() if k not in {"resource", "action", "expected"}},
    }


def normalize_diff(item):
    x = item if isinstance(item, dict) else {}
    route = x.get("route") if isinstance(x.get("route"), dict) else {}
    severity = str(x.get("severity") or "medium").lower()
    if severity not in VALID_SEVERITIES:
        severity = "medium"
    status = str(x.get("status") or "suspected").lower()
    if status not in VALID_STATUSES:
        status = "suspected"
    rule_id = str(x.get("rule_id") or "")
    missing = x.get("missing") if isinstance(x.get("missing"), list) else []
    return {
        "diff_id": str(x.get("diff_id") or stable_matrix_id(rule_id, route.get("method"), route.get("path"), ",".join(missing))),
        "rule_id": rule_id,
        "route": {"method": str(route.get("method") or "").upper(), "path": str(route.get("path") or "")},
        "resource": str(x.get("resource") or ""),
        "action": str(x.get("action") or ""),
        "expected": x.get("expected") if isinstance(x.get("expected"), dict) else {},
        "observed": x.get("observed") if isinstance(x.get("observed"), dict) else {},
        "missing": [str(v) for v in missing],
        "severity": severity,
        "status": status,
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "reason": str(x.get("reason") or ""),
        "suggested_human_decision": x.get("suggested_human_decision") if isinstance(x.get("suggested_human_decision"), list) else [],
    }


def normalize_diff_payload(obj):
    x = obj if isinstance(obj, dict) else {}
    mode = str(x.get("mode") or "inferred_only")
    if mode not in VALID_MODES:
        mode = "inferred_only"
    summary = x.get("summary") if isinstance(x.get("summary"), dict) else {}
    keys = [
        "total_routes",
        "matched_routes",
        "missing_auth",
        "missing_permission",
        "missing_ownership_check",
        "missing_tenant_boundary",
        "missing_transaction",
        "missing_audit_log",
    ]
    return {
        "version": "authz_matrix_diff_v1",
        "mode": mode,
        "summary": {k: int(summary.get(k) or 0) for k in keys},
        "diffs": [normalize_diff(v) for v in (x.get("diffs") or [])],
        "limitations": x.get("limitations") if isinstance(x.get("limitations"), list) else [],
    }

