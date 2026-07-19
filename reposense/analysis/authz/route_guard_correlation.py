from collections import Counter

from ...linking.path_normalize import normalize_path, template_match
from .guard_correlation_schema import normalize_payload
from .guard_extractor import extract_nestjs_guards, extract_openapi_security


LIMITATIONS = [
    "OpenAPI security is contract/documentation evidence, not implementation guard proof.",
    "NestJS global Guard application boundaries are inferred without a complete module graph.",
    "Unknown or ambiguous correlations require human confirmation.",
]


def _guard_role_status(guards, public_bypass):
    if public_bypass:
        return "not_applicable"
    types = {str(row.get("guard_type") or "") for row in guards}
    if "permission" in types:
        return "permission_guard_observed"
    if "role" in types:
        return "role_guard_observed"
    if guards:
        return "no_role_guard_observed"
    return "no_role_guard_observed"


def _effective_status(route, global_guards):
    method_bypass = route.get("method_bypasses") or []
    method_guards = route.get("method_guards") or []
    controller_bypass = route.get("controller_bypasses") or []
    controller_guards = route.get("controller_guards") or []
    if method_bypass:
        return "intentional_public_bypass", [], method_bypass, 0.93
    if method_guards:
        return "protected_method", method_guards, [], 0.95
    if controller_bypass:
        return "intentional_public_bypass", [], controller_bypass, 0.86
    if controller_guards:
        return "protected_controller", controller_guards, [], 0.92
    if global_guards:
        confidence = min(float(row.get("confidence") or 0.0) for row in global_guards)
        return "protected_global", global_guards, [], min(confidence, 0.84)
    return "unprotected", [], [], 0.86


def _match_openapi(route, openapi_routes):
    method = str(route.get("method") or "").upper()
    path = normalize_path(route.get("path"))
    raw_path = str(route.get("raw_path") or route.get("path") or "")
    candidates = [
        row
        for row in openapi_routes
        if str(row.get("method") or "").upper() == method
    ]
    exact = [row for row in candidates if normalize_path(row.get("path")) == path]
    if len(exact) == 1:
        candidate_raw = str(
            exact[0].get("raw_path") or exact[0].get("path") or ""
        )
        if candidate_raw == raw_path:
            return "exact_match", exact
        return "template_match", exact
    if len(exact) > 1:
        return "ambiguous", exact
    templated = [
        row
        for row in candidates
        if template_match(row.get("path"), path) or template_match(path, row.get("path"))
    ]
    if len(templated) == 1:
        return "template_match", templated
    if len(templated) > 1:
        return "ambiguous", templated
    return "code_only", []


def _expectation(matches):
    statuses = {str(row.get("security_status") or "unspecified") for row in matches}
    if len(statuses) == 1:
        return next(iter(statuses))
    if not statuses:
        return "not_available"
    return "ambiguous"


def _correlation_for_code(route, openapi_routes, global_guards):
    match_status, matches = _match_openapi(route, openapi_routes)
    auth_status, guards, bypasses, confidence = _effective_status(route, global_guards)
    expectation = _expectation(matches)
    limitations = []
    if auth_status == "protected_global":
        limitations.append("global_guard_application_boundary_inferred")
    if match_status == "ambiguous":
        limitations.append("route_guard_match_ambiguous")
        confidence = min(confidence, 0.55)
    if expectation == "protected" and auth_status in {"unprotected", "unknown"}:
        limitations.append("openapi_security_without_code_guard")
    if auth_status == "intentional_public_bypass":
        limitations.extend(
            limitation
            for bypass in bypasses
            for limitation in (bypass.get("limitations") or [])
        )
    evidence = list(route.get("source_refs") or [])
    evidence += [
        ref
        for source in guards + bypasses
        for ref in (source.get("evidence_refs") or [])
    ]
    evidence += [
        ref
        for match in matches
        for ref in (match.get("source_refs") or [])
    ]
    return {
        "method": route.get("method"),
        "path": normalize_path(route.get("path")),
        "code_route_refs": route.get("source_refs") or [],
        "openapi_route_refs": [
            ref for match in matches for ref in (match.get("source_refs") or [])
        ],
        "match_status": match_status,
        "effective_auth_status": auth_status,
        "effective_role_status": _guard_role_status(guards, bool(bypasses)),
        "guard_sources": guards,
        "public_bypass_sources": bypasses,
        "openapi_security_expectation": expectation,
        "confidence": confidence,
        "evidence_refs": evidence,
        "limitations": limitations,
    }


def build_route_guard_correlation(repo_path):
    nest = extract_nestjs_guards(repo_path)
    openapi = extract_openapi_security(repo_path)
    correlations = []
    matched_openapi_ids = set()
    for route in nest.get("routes") or []:
        correlation = _correlation_for_code(
            route,
            openapi.get("routes") or [],
            nest.get("global_guards") or [],
        )
        for openapi_route in openapi.get("routes") or []:
            refs = openapi_route.get("source_refs") or []
            if any(ref in correlation.get("openapi_route_refs", []) for ref in refs):
                matched_openapi_ids.add(openapi_route.get("route_id"))
        correlations.append(correlation)
    for route in openapi.get("routes") or []:
        if route.get("route_id") in matched_openapi_ids:
            continue
        correlations.append(
            {
                "method": route.get("method"),
                "path": normalize_path(route.get("path")),
                "code_route_refs": [],
                "openapi_route_refs": route.get("source_refs") or [],
                "match_status": "openapi_only",
                "effective_auth_status": "unknown",
                "effective_role_status": "unknown",
                "guard_sources": [],
                "public_bypass_sources": [],
                "openapi_security_expectation": route.get("security_status") or "unspecified",
                "confidence": 0.55,
                "evidence_refs": route.get("source_refs") or [],
                "limitations": [
                    "openapi_only_route",
                    "OpenAPI security is not implementation guard proof.",
                ],
            }
        )
    payload = normalize_payload(correlations, LIMITATIONS)
    counts = Counter(row.get("match_status") for row in payload["correlations"])
    auth_counts = Counter(row.get("effective_auth_status") for row in payload["correlations"])
    summary = {
        "version": "route_guard_summary_v1",
        "total_code_routes": len(nest.get("routes") or []),
        "total_openapi_routes": len(openapi.get("routes") or []),
        "exact_matches": int(counts.get("exact_match", 0)),
        "template_matches": int(counts.get("template_match", 0)),
        "code_only_routes": int(counts.get("code_only", 0)),
        "openapi_only_routes": int(counts.get("openapi_only", 0)),
        "ambiguous_routes": int(counts.get("ambiguous", 0)),
        "method_guards": len(
            [row for row in (nest.get("guards") or []) if row.get("scope") == "method"]
        ),
        "controller_guards": len(
            [row for row in (nest.get("guards") or []) if row.get("scope") == "controller"]
        ),
        "global_guards": len(nest.get("global_guards") or []),
        "protected_method": int(auth_counts.get("protected_method", 0)),
        "protected_controller": int(auth_counts.get("protected_controller", 0)),
        "protected_global": int(auth_counts.get("protected_global", 0)),
        "intentional_public_bypasses": int(auth_counts.get("intentional_public_bypass", 0)),
        "unprotected_routes": int(auth_counts.get("unprotected", 0)),
        "unknown_routes": int(auth_counts.get("unknown", 0)),
        "openapi_protected_without_code_guard": len(
            [
                row
                for row in payload["correlations"]
                if row.get("openapi_security_expectation") == "protected"
                and row.get("effective_auth_status") in {"unprotected", "unknown"}
            ]
        ),
        "limitations": LIMITATIONS[:],
    }
    return payload, summary, openapi, nest


def apply_guard_correlations(routes, correlations_payload):
    correlations = (
        correlations_payload.get("correlations")
        if isinstance(correlations_payload, dict)
        and isinstance(correlations_payload.get("correlations"), list)
        else []
    )
    annotated = []
    for route in routes or []:
        row = dict(route)
        method = str(row.get("method") or "").upper()
        path = normalize_path(row.get("path"))
        file_path = str(row.get("file") or "").replace("\\", "/")
        line = int(row.get("line_start") or 0)
        candidates = []
        for correlation in correlations:
            if str(correlation.get("method") or "").upper() != method:
                continue
            refs = correlation.get("code_route_refs") or []
            same_location = any(
                str(ref.get("file") or "").replace("\\", "/") == file_path
                and int(ref.get("start_line") or 0) == line
                for ref in refs
            )
            correlation_path = normalize_path(correlation.get("path"))
            same_path = correlation_path == path
            templated = (
                template_match(correlation_path, path)
                or template_match(path, correlation_path)
            )
            if same_location or same_path or templated:
                score = 3 if same_location else (2 if same_path else 1)
                if correlation.get("match_status") == "openapi_only":
                    score -= 1
                candidates.append((score, correlation))
        if candidates:
            candidates.sort(
                key=lambda item: (
                    -item[0],
                    str(item[1].get("correlation_id") or ""),
                )
            )
            best_score, correlation = candidates[0]
            status = str(correlation.get("effective_auth_status") or "unknown")
            role_status = str(correlation.get("effective_role_status") or "unknown")
            guard_sources = correlation.get("guard_sources") or []
            auth_signals = list(row.get("auth_signals") or [])
            role_signals = list(row.get("role_permission_signals") or [])
            if status in {"protected_method", "protected_controller", "protected_global"}:
                auth_signals.append(f"effective_guard:{status}")
                auth_signals.extend(
                    f"guard:{source.get('guard_name')}"
                    for source in guard_sources
                    if source.get("guard_name")
                )
            if role_status in {"role_guard_observed", "permission_guard_observed"}:
                role_signals.append(f"effective_guard:{role_status}")
                role_signals.extend(
                    f"guard:{source.get('guard_name')}"
                    for source in guard_sources
                    if source.get("guard_type") in {"role", "permission"}
                    and source.get("guard_name")
                )
            row["auth_signals"] = sorted(set(auth_signals))
            row["role_permission_signals"] = sorted(set(role_signals))
            row["effective_auth_status"] = status
            row["effective_role_status"] = role_status
            row["guard_scope"] = (
                status.removeprefix("protected_")
                if status.startswith("protected_")
                else ""
            )
            row["public_bypass"] = status == "intentional_public_bypass"
            row["guard_correlation_id"] = correlation.get("correlation_id")
            row["guard_correlation_confidence"] = float(
                correlation.get("confidence") or 0.0
            )
            row["guard_correlation_limitations"] = list(
                correlation.get("limitations") or []
            )
            row["openapi_security_expectation"] = str(
                correlation.get("openapi_security_expectation") or "not_available"
            )
            row["guard_sources"] = guard_sources
            row["public_bypass_sources"] = correlation.get(
                "public_bypass_sources"
            ) or []
            row["guard_correlation_match_status"] = str(
                correlation.get("match_status") or ""
            )
            if best_score == 3 and correlation.get("code_route_refs"):
                row["path"] = str(correlation.get("path") or row.get("path") or "")
        else:
            row["effective_auth_status"] = "unknown"
            row["effective_role_status"] = "unknown"
            row["guard_scope"] = ""
            row["public_bypass"] = False
            row["guard_correlation_id"] = ""
            row["guard_correlation_confidence"] = 0.0
            row["guard_correlation_limitations"] = [
                "route_guard_correlation_unresolved"
            ]
            row["openapi_security_expectation"] = "not_available"
            row["guard_sources"] = []
            row["public_bypass_sources"] = []
            row["guard_correlation_match_status"] = ""
        annotated.append(row)
    return annotated
