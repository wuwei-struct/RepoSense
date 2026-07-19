import json
import os
import re

from .authz_rules import (
    AUTH_WORDS,
    FRONTEND_WORDS,
    NEGATIVE_TEST_WORDS,
    ROLE_WORDS,
    SENSITIVE_WORDS,
    SKIP_DIRS,
    SOURCE_EXTENSIONS,
    WRITE_METHODS,
    is_frontend_path,
    is_test_path,
    language_for_path,
)
from .authz_schema import normalize_frontend_signal, normalize_guard, normalize_risk, normalize_route
from .authz_summary import LIMITATIONS
from ..context.route_intent import classify_route_intents
from ..routes.typescript_decorator_classifier import (
    classify_typescript_decorators,
)
from .route_guard_correlation import (
    apply_guard_correlations,
    build_route_guard_correlation,
)


ROUTE_RE = re.compile(r"(app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
JAVA_DECORATOR_RE = re.compile(
    r"@(RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)"
    r"\b\s*\(\s*['\"]?([^'\"\)]*)['\"]?",
)
PY_ROUTE_RE = re.compile(r"@(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")


def _repo_relative_file(repo_path, file_path):
    raw = str(file_path or "").strip()
    if not raw:
        return ""
    if not os.path.isabs(raw):
        return raw.replace("\\", "/")
    root = os.path.abspath(repo_path)
    candidate = os.path.abspath(raw)
    try:
        if os.path.commonpath([root, candidate]) == root:
            return _rel(root, candidate)
    except (OSError, ValueError):
        pass
    return raw.replace("\\", "/")


def _iter_source_files(repo_path):
    root = os.path.abspath(repo_path)
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".reposense_")]
        for name in files:
            if os.path.splitext(name)[1].lower() not in SOURCE_EXTENSIONS:
                continue
            path = os.path.join(cur, name)
            rel = _rel(root, path)
            yield rel, path


def _contains_any(text, words):
    low = text.lower()
    return [w for w in words if str(w).lower() in low]


def _is_sensitive(path):
    p = str(path or "").lower()
    return any(w in p for w in SENSITIVE_WORDS)


def _route_window(lines, idx):
    start = max(0, idx - 4)
    end = min(len(lines), idx + 12)
    return "\n".join(lines[start:end])


def _evidence(rule_id, route, file_path, line, snippet):
    return [
        {
            "source_type": "permission",
            "rule_id": rule_id,
            "file": file_path,
            "start_line": int(line or 1),
            "end_line": int(line or 1),
            "snippet": snippet,
            "method": route.get("method"),
            "path": route.get("path"),
        }
    ]


def _risk(
    rule_id,
    title,
    severity,
    status,
    confidence,
    route,
    reason,
    signals,
    limitations=None,
    suggested_human_review=True,
):
    return normalize_risk(
        {
            "rule_id": rule_id,
            "title": title,
            "severity": severity,
            "status": status,
            "confidence": confidence,
            "route": {"method": route.get("method"), "path": route.get("path")},
            "file": route.get("file"),
            "line_start": route.get("line_start"),
            "line_end": route.get("line_end"),
            "snippet": (route.get("source_refs") or [{}])[0].get("snippet") if route.get("source_refs") else "",
            "reason": reason,
            "signals": signals,
            "evidence_refs": _evidence(rule_id, route, route.get("file"), route.get("line_start"), (route.get("source_refs") or [{}])[0].get("snippet") if route.get("source_refs") else ""),
            "limitations": limitations or LIMITATIONS[:1],
            "suggested_human_review": suggested_human_review,
        }
    )


def _routes_from_api_surface(run_dir, repo_path):
    api = _read_json(os.path.join(run_dir, "api_surface.json"), {})
    rows = api.get("endpoints") if isinstance(api.get("endpoints"), list) else []
    out = []
    for ep in rows:
        src = ep.get("source") if isinstance(ep.get("source"), dict) else {}
        method = str(ep.get("method") or "").upper()
        path = str(ep.get("path") or "")
        file_path = _repo_relative_file(repo_path, src.get("path") or ep.get("file") or "")
        line = int(src.get("line_start") or src.get("start_line") or ep.get("line_start") or 1)
        out.append(
            normalize_route(
                {
                    "method": method,
                    "path": path,
                    "file": file_path,
                    "line_start": line,
                    "language": src.get("language") or ep.get("language"),
                    "framework": src.get("framework") or ep.get("framework"),
                    "source_kind": str(ep.get("source_kind") or "api_surface"),
                    "write_like": method in WRITE_METHODS,
                    "sensitive": _is_sensitive(path),
                    "source_refs": [{"source_type": "api_surface", "file": file_path, "start_line": line, "snippet": f"{method} {path}"}],
                }
            )
        )
    return out


def _event_side_effect_files(run_dir):
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": []})
    out = set()
    for n in graph.get("nodes") or []:
        if str(n.get("type") or "") not in {"db_op", "queue_dispatch", "cache_op"}:
            continue
        meta = n.get("meta") if isinstance(n.get("meta"), dict) else {}
        kind = str(meta.get("db.kind") or meta.get("cache.kind") or n.get("type") or "")
        if kind in {"db.read", "cache.read"}:
            continue
        path = str(meta.get("path") or meta.get("file") or "").replace("\\", "/")
        if path:
            out.add(path)
    return out


def _routes_from_source(repo_path):
    routes = []
    guards = []
    frontend = []
    test_signals = []
    file_text = {}
    for rel, path in _iter_source_files(repo_path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        text = "\n".join(lines)
        file_text[rel] = text
        extension = os.path.splitext(rel)[1].lower()
        if extension in {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx"}:
            classified = classify_typescript_decorators(lines, rel)
            for canonical in classified["routes"]:
                line_no = int(canonical.get("line_start") or 0)
                decorator_text = "\n".join(
                    item.get("text") or ""
                    for item in (
                        (canonical.get("controller_decorators") or [])
                        + (canonical.get("method_decorators") or [])
                    )
                )
                window = decorator_text + "\n" + _route_window(
                    lines,
                    max(1, line_no),
                )
                routes.append(
                    normalize_route(
                        {
                            "method": canonical.get("method"),
                            "path": canonical.get("path"),
                            "file": rel,
                            "line_start": line_no,
                            "language": language_for_path(rel),
                            "framework": "nestjs",
                            "source_kind": "code",
                            "write_like": canonical.get("method") in WRITE_METHODS,
                            "sensitive": _is_sensitive(canonical.get("path"))
                            or _is_sensitive(rel),
                            "auth_signals": _contains_any(window, AUTH_WORDS),
                            "role_permission_signals": _contains_any(
                                window,
                                ROLE_WORDS,
                            ),
                            "source_refs": canonical.get("source_refs") or [],
                        }
                    )
                )
        for idx, line in enumerate(lines, 1):
            auth = _contains_any(line, AUTH_WORDS)
            role = _contains_any(line, ROLE_WORDS)
            if auth:
                guards.append(normalize_guard({"guard_type": "auth", "file": rel, "line_start": idx, "snippet": line.strip(), "signals": auth, "confidence": 0.75}))
            if role:
                guards.append(normalize_guard({"guard_type": "role", "file": rel, "line_start": idx, "snippet": line.strip(), "signals": role, "confidence": 0.75}))
            if is_frontend_path(rel):
                fs = _contains_any(line, FRONTEND_WORDS)
                if fs:
                    frontend.append(normalize_frontend_signal({"file": rel, "line_start": idx, "snippet": line.strip(), "signals": fs, "possible_action": line.strip(), "confidence": 0.7}))
            if is_test_path(rel):
                ns = _contains_any(line, NEGATIVE_TEST_WORDS)
                if ns:
                    test_signals.append({"file": rel, "line_start": idx, "snippet": line.strip(), "signals": ns})
            for m in ROUTE_RE.finditer(line):
                method = m.group(2).upper()
                route_path = m.group(3)
                win = line
                routes.append(
                    normalize_route(
                        {
                            "method": method,
                            "path": route_path,
                            "file": rel,
                            "line_start": idx,
                            "language": language_for_path(rel),
                            "framework": "express",
                            "source_kind": "code",
                            "write_like": method in WRITE_METHODS,
                            "sensitive": _is_sensitive(route_path),
                            "auth_signals": _contains_any(win, AUTH_WORDS),
                            "role_permission_signals": _contains_any(win, ROLE_WORDS),
                            "source_refs": [{"source_type": "source", "file": rel, "start_line": idx, "snippet": line.strip()}],
                        }
                    )
                )
            pm = PY_ROUTE_RE.search(line)
            if pm:
                method = pm.group(1).upper()
                route_path = pm.group(2)
                win = line
                routes.append(
                    normalize_route(
                        {
                            "method": method,
                            "path": route_path,
                            "file": rel,
                            "line_start": idx,
                            "language": language_for_path(rel),
                            "framework": "python",
                            "source_kind": "code",
                            "write_like": method in WRITE_METHODS,
                            "sensitive": _is_sensitive(route_path),
                            "auth_signals": _contains_any(win, AUTH_WORDS),
                            "role_permission_signals": _contains_any(win, ROLE_WORDS),
                            "source_refs": [{"source_type": "source", "file": rel, "start_line": idx, "snippet": line.strip()}],
                        }
                    )
                )
            dm = JAVA_DECORATOR_RE.search(line) if extension == ".java" else None
            if dm:
                raw = dm.group(1).lower()
                route_path = dm.group(2) or ""
                method = {"getmapping": "GET", "postmapping": "POST", "putmapping": "PUT", "patchmapping": "PATCH", "deletemapping": "DELETE", "requestmapping": ""}.get(raw, raw.upper())
                win = _route_window(lines, idx)
                routes.append(
                    normalize_route(
                        {
                            "method": method,
                            "path": route_path,
                            "file": rel,
                            "line_start": idx,
                            "language": language_for_path(rel),
                            "framework": "decorator",
                            "source_kind": "code",
                            "write_like": method in WRITE_METHODS,
                            "sensitive": _is_sensitive(route_path) or _is_sensitive(rel),
                            "auth_signals": _contains_any(win, AUTH_WORDS),
                            "role_permission_signals": _contains_any(win, ROLE_WORDS),
                            "source_refs": [{"source_type": "source", "file": rel, "start_line": idx, "snippet": line.strip()}],
                        }
                    )
                )
    return routes, guards, frontend, test_signals, file_text


def _merge_routes(api_routes, source_routes, side_effect_files):
    by_key = {}
    for r in api_routes + source_routes:
        key = (r.get("method"), r.get("path"), r.get("file"))
        cur = by_key.get(key)
        if not cur:
            cur = dict(r)
            by_key[key] = cur
        else:
            cur["auth_signals"] = sorted(set((cur.get("auth_signals") or []) + (r.get("auth_signals") or [])))
            cur["role_permission_signals"] = sorted(set((cur.get("role_permission_signals") or []) + (r.get("role_permission_signals") or [])))
            cur["source_refs"] = (cur.get("source_refs") or []) + (r.get("source_refs") or [])
        if r.get("file") in side_effect_files:
            cur["write_like"] = True
    return [normalize_route(v) for v in by_key.values()]


def _negative_test_observed(route, test_signals):
    if not test_signals:
        return False
    route_path = str(route.get("path") or "").lower()
    basename = os.path.splitext(os.path.basename(route.get("file") or ""))[0].lower()
    for sig in test_signals:
        text = f"{sig.get('file','')} {sig.get('snippet','')}".lower()
        if route_path and route_path in text:
            return True
        if basename and basename in text:
            return True
    return False


def _risks_from_surface(routes, frontend, test_signals):
    risks = []
    for r in routes:
        auth = r.get("auth_signals") or []
        role = r.get("role_permission_signals") or []
        intent = str(r.get("intent") or "unknown")
        intent_confidence = float(r.get("intent_confidence") or 0.0)
        intent_limitations = list(r.get("intent_limitations") or [])
        public_auth = intent == "public_auth_entrypoint" and intent_confidence >= 0.8
        possible_public = "possible_public_auth_entrypoint" in intent_limitations
        effective_auth = str(r.get("effective_auth_status") or "unknown")
        effective_role = str(r.get("effective_role_status") or "unknown")
        code_protected = effective_auth in {
            "protected_method",
            "protected_controller",
            "protected_global",
        }
        intentional_public = effective_auth == "intentional_public_bypass"
        public_bypass_auth = intentional_public and public_auth
        openapi_only = str(r.get("guard_correlation_match_status") or "") == "openapi_only"
        guard_limitations = list(r.get("guard_correlation_limitations") or [])
        if r.get("openapi_security_expectation") == "protected" and not code_protected:
            guard_limitations.append("openapi_security_without_code_guard")
        missing_auth = not bool(auth) and not code_protected
        if r.get("write_like") and missing_auth and not public_auth and not public_bypass_auth:
            risks.append(
                _risk(
                    "AUTHZ-001",
                    "Public write endpoint",
                    "high" if r.get("method") in {"DELETE", "PATCH"} else "medium",
                    "suspected"
                    if possible_public or openapi_only or effective_auth == "unknown"
                    else ("confirmed" if r.get("file") else "suspected"),
                    0.6 if possible_public else 0.78,
                    r,
                    "Write-like endpoint observed without auth guard evidence.",
                    ["write_like", "missing_auth_guard"] + (["possible_public_auth_entrypoint"] if possible_public else []),
                    LIMITATIONS[:1]
                    + (["possible_public_auth_entrypoint"] if possible_public else [])
                    + intent_limitations
                    + guard_limitations,
                )
            )
        if r.get("sensitive") and missing_auth and not public_auth and not public_bypass_auth:
            sev = "high" if r.get("write_like") else "medium"
            risks.append(
                _risk(
                    "AUTHZ-002",
                    "Sensitive route missing auth guard",
                    sev,
                    "suspected",
                    0.66,
                    r,
                    "Sensitive route path observed without auth guard evidence.",
                    ["sensitive_route", "missing_auth_guard"],
                    LIMITATIONS[:1] + intent_limitations + guard_limitations,
                )
            )
        role_observed = bool(role) or effective_role in {
            "role_guard_observed",
            "permission_guard_observed",
        }
        if r.get("sensitive") and (auth or code_protected) and not role_observed and not public_auth:
            risks.append(_risk("AUTHZ-003", "Sensitive route missing role or permission guard", "medium", "suspected", 0.64, r, "Sensitive route has auth evidence but no role or permission guard evidence was observed.", ["sensitive_route", "auth_observed", "missing_role_guard"]))
        if public_auth and not _negative_test_observed(r, test_signals):
            risks.append(
                _risk(
                    "AUTHZ-005",
                    "Public authentication negative test gap",
                    "low",
                    "suspected",
                    0.58,
                    r,
                    "No invalid-credential or malformed authentication request test evidence was observed for this public authentication entrypoint.",
                    ["negative_test_gap", "public_auth_entrypoint"],
                    ["Negative test gap is inferred from file-name and keyword matching only."],
                    suggested_human_review=False,
                )
            )
    if frontend:
        backend_missing_guard = [
            r
            for r in routes
            if (r.get("sensitive") or r.get("write_like"))
            and str(r.get("effective_role_status") or "")
            not in {"role_guard_observed", "permission_guard_observed"}
            and not r.get("role_permission_signals")
        ]
        for sig in frontend[:10]:
            related = backend_missing_guard[0] if backend_missing_guard else {"method": "", "path": "", "file": sig.get("file"), "line_start": sig.get("line_start"), "source_refs": [{"snippet": sig.get("snippet")}]} 
            risks.append(_risk("AUTHZ-004", "Frontend-only permission signal", "medium" if backend_missing_guard else "low", "suspected", 0.55, related, "Frontend permission signal observed; backend guard evidence was not observed for a related sensitive/write route.", ["frontend_permission_signal"] + (sig.get("signals") or []), ["Route correspondence is heuristic in the MVP."]))
    existing = list(risks)
    for risk in existing:
        if risk.get("rule_id") not in {"AUTHZ-001", "AUTHZ-002", "AUTHZ-003"}:
            continue
        route = {"method": (risk.get("route") or {}).get("method"), "path": (risk.get("route") or {}).get("path"), "file": risk.get("file"), "line_start": risk.get("line_start"), "source_refs": [{"snippet": risk.get("snippet")}]}
        if not _negative_test_observed(route, test_signals):
            risks.append(_risk("AUTHZ-005", "Permission negative test gap", "medium", "suspected", 0.6, route, "No negative permission test evidence observed for this permission-sensitive route.", ["negative_test_gap"], ["Negative test gap is inferred from file-name and keyword matching only."]))
    risks.sort(key=lambda x: (x.get("rule_id"), x.get("file"), (x.get("route") or {}).get("path"), x.get("risk_id")))
    return risks


def scan_permission_auditor(run_dir, repo_path, guard_payload=None, guard_summary=None):
    api_routes = _routes_from_api_surface(run_dir, repo_path)
    source_routes, guards, frontend, test_signals, _file_text = _routes_from_source(repo_path)
    routes = _merge_routes(api_routes, source_routes, _event_side_effect_files(run_dir))
    route_intents, routes = classify_route_intents(routes, repo_path)
    if guard_payload is None:
        guard_payload, built_summary, _openapi, _nest = build_route_guard_correlation(repo_path)
        guard_summary = guard_summary or built_summary
    routes = apply_guard_correlations(routes, guard_payload)
    routes = [normalize_route(route) for route in routes]
    risks = _risks_from_surface(routes, frontend, test_signals)
    surface = {
        "version": "permission_surface_v1",
        "generated_from": run_dir,
        "repo_path": os.path.abspath(repo_path),
        "routes": routes,
        "guards": guards,
        "frontend_permission_signals": frontend,
        "test_signals": test_signals,
        "route_intent_annotations": route_intents,
        "route_guard_summary": guard_summary if isinstance(guard_summary, dict) else {},
        "limitations": LIMITATIONS[:],
    }
    return surface, {"version": "permission_risks_v1", "risks": risks, "limitations": LIMITATIONS[:]}
