import os

from .authz_matrix_schema import normalize_diff, normalize_diff_payload


LIMITATIONS = [
    "AuthZ Matrix diff is evidence-backed and conservative.",
    "It does not prove authorization correctness.",
    "Missing means expected signal not observed, not proven absent.",
]


def _route_key(method, path):
    return (str(method or "").upper(), str(path or ""))


def _route_evidence(route, rule_id):
    refs = route.get("source_refs") if isinstance(route.get("source_refs"), list) else []
    if refs:
        out = []
        for r in refs[:3]:
            x = dict(r)
            x["rule_id"] = rule_id
            out.append(x)
        return out
    return [{"source_type": "authz_matrix", "rule_id": rule_id, "file": route.get("file"), "start_line": route.get("line_start"), "snippet": f"{route.get('method')} {route.get('path')}"}]


def _observed_for(route, tx_files):
    text = " ".join((route.get("auth_signals") or []) + (route.get("role_permission_signals") or []) + (route.get("ownership_signals") or []) + (route.get("tenant_boundary_signals") or []))
    low = text.lower() + " " + str(route.get("path") or "").lower()
    file_path = str(route.get("file") or "")
    return {
        "auth": bool(route.get("auth_signals")),
        "permission": bool(route.get("role_permission_signals")),
        "ownership_check": any(x in low for x in ["owner", "user", "createdby", "created_by"]),
        "tenant_boundary": any(x in low for x in ["tenant", "org", "organization", "workspace", "team"]),
        "transaction": file_path in tx_files,
        "audit_log": any(x in low for x in ["audit", "log", "history", "event"]),
        "source_file": file_path,
    }


def _tx_files_from_event_graph(event_graph):
    files = set()
    for n in event_graph.get("nodes") or []:
        if str(n.get("type") or "") != "tx_boundary":
            continue
        meta = n.get("meta") if isinstance(n.get("meta"), dict) else {}
        p = str(meta.get("path") or meta.get("file") or "").replace("\\", "/")
        if p:
            files.add(p)
    return files


def diff_authz_matrix(expected_contract, permission_surface, event_graph):
    routes = permission_surface.get("routes") if isinstance(permission_surface.get("routes"), list) else []
    actual = {_route_key(r.get("method"), r.get("path")): r for r in routes}
    tx_files = _tx_files_from_event_graph(event_graph if isinstance(event_graph, dict) else {})
    diffs = []
    matched = 0
    for exp in expected_contract.get("routes") or []:
        key = _route_key(exp.get("method"), exp.get("path"))
        route = actual.get(key)
        expected = exp.get("expected") or {}
        if route:
            matched += 1
        else:
            route = {"method": exp.get("method"), "path": exp.get("path"), "file": "", "line_start": 1, "source_refs": []}
        obs = _observed_for(route, tx_files)

        def add(rule_id, field, severity, status, reason):
            diffs.append(
                normalize_diff(
                    {
                        "rule_id": rule_id,
                        "route": {"method": exp.get("method"), "path": exp.get("path")},
                        "resource": exp.get("resource"),
                        "action": exp.get("action"),
                        "expected": expected,
                        "observed": obs,
                        "missing": [field],
                        "severity": severity,
                        "status": status,
                        "evidence_refs": _route_evidence(route, rule_id),
                        "reason": reason,
                        "suggested_human_decision": [f"Confirm whether {field} is required and where it should be enforced."],
                    }
                )
            )

        if expected.get("auth") == "required" and not obs["auth"]:
            add("AUTHZ-MATRIX-001", "auth", "high", "confirmed" if route.get("file") else "suspected", "Expected auth signal not observed.")
        if expected.get("permissions") and not obs["permission"]:
            add("AUTHZ-MATRIX-002", "permission", "high", "suspected", "Expected permission signal not observed.")
        if expected.get("ownership_check") == "required" and not obs["ownership_check"]:
            add("AUTHZ-MATRIX-003", "ownership_check", "medium", "suspected", "Expected ownership check signal not observed.")
        if expected.get("tenant_boundary") == "required" and not obs["tenant_boundary"]:
            add("AUTHZ-MATRIX-004", "tenant_boundary", "high", "suspected", "Expected tenant boundary signal not observed.")
        if expected.get("transaction") == "required" and not obs["transaction"]:
            add("AUTHZ-MATRIX-005", "transaction", "high", "suspected", "Expected transaction signal not observed.")
        if expected.get("audit_log") == "required" and not obs["audit_log"]:
            add("AUTHZ-MATRIX-006", "audit_log", "medium", "suspected", "Expected audit log signal not observed.")

    summary = {
        "total_routes": len(expected_contract.get("routes") or []),
        "matched_routes": matched,
        "missing_auth": len([d for d in diffs if "auth" in d.get("missing", [])]),
        "missing_permission": len([d for d in diffs if "permission" in d.get("missing", [])]),
        "missing_ownership_check": len([d for d in diffs if "ownership_check" in d.get("missing", [])]),
        "missing_tenant_boundary": len([d for d in diffs if "tenant_boundary" in d.get("missing", [])]),
        "missing_transaction": len([d for d in diffs if "transaction" in d.get("missing", [])]),
        "missing_audit_log": len([d for d in diffs if "audit_log" in d.get("missing", [])]),
    }
    return normalize_diff_payload({"mode": "contract_diff", "summary": summary, "diffs": diffs, "limitations": LIMITATIONS[:]})


def inferred_only_diff(permission_surface):
    routes = permission_surface.get("routes") if isinstance(permission_surface.get("routes"), list) else []
    return normalize_diff_payload(
        {
            "mode": "inferred_only",
            "summary": {"total_routes": len(routes), "matched_routes": 0},
            "diffs": [],
            "limitations": LIMITATIONS[:] + ["No authority contract provided; inferred matrix requires human confirmation."],
        }
    )

