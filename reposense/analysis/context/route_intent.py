import os
import re

from .context_schema import normalize_route_intent


PUBLIC_PATTERNS = [
    ("login", re.compile(r"(?:^|[^a-z0-9])(login|sign[-_]?in)(?:[^a-z0-9]|$)", re.I)),
    ("register", re.compile(r"(?:^|[^a-z0-9])(register|sign[-_]?up)(?:[^a-z0-9]|$)", re.I)),
    ("forgot_password", re.compile(r"forgot[/_.-]*(password)?|password[/_.-]*forgot", re.I)),
    ("reset_password", re.compile(r"reset[/_.-]*password|password[/_.-]*reset", re.I)),
    ("email_verification", re.compile(r"(email[/_.-]*)?confirm|verify[/_.-]*email", re.I)),
    ("oauth_callback", re.compile(r"(oauth|oidc|google|facebook|apple).*(callback|login)", re.I)),
]
PROTECTED_PATTERNS = [
    ("logout", re.compile(r"(?:^|[^a-z0-9])logout(?:[^a-z0-9]|$)", re.I)),
    ("revoke_token", re.compile(r"revoke|invalidate[/_.-]*token", re.I)),
    ("change_password", re.compile(r"change[/_.-]*password|password[/_.-]*change", re.I)),
    ("change_email", re.compile(r"change[/_.-]*email|email[/_.-]*change", re.I)),
    ("update_profile", re.compile(r"update[/_.-]*profile|(?:^|[^a-z0-9])profile(?:[^a-z0-9]|$)", re.I)),
    ("session_management", re.compile(r"(?:^|[^a-z0-9])sessions?(?:[^a-z0-9]|$)", re.I)),
]
CONFLICT_WORDS = {"delete", "refund", "payment", "billing", "role", "permission", "tenant", "workspace"}
SENSITIVE_WORDS = CONFLICT_WORDS | {"admin", "organization", "account"}
AUTH_CONTEXT_WORDS = {
    "auth",
    "login",
    "credential",
    "password",
    "token",
    "oauth",
    "oidc",
    "validatelogin",
    "validatesociallogin",
    "forgotpassword",
    "resetpassword",
}


def _source_window(repo_path, route):
    file_path = str(route.get("file") or "")
    line = int(route.get("line_start") or 1)
    candidate = os.path.join(repo_path, file_path.replace("/", os.sep))
    try:
        with open(candidate, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return "", ""
    start = max(0, line - 1)
    end = min(len(lines), line + 24)
    for index in range(line, end):
        if index > line and re.match(
            r"\s*@(Get|Post|Put|Patch|Delete|RequestMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\b",
            lines[index],
            flags=re.I,
        ):
            end = index
            break
    window = "\n".join(lines[start:end])
    snippet = lines[line - 1].strip() if 1 <= line <= len(lines) else ""
    return window, snippet


def _route_evidence(route, snippet):
    refs = []
    for ref in route.get("source_refs") or []:
        if not isinstance(ref, dict):
            continue
        file_path = str(ref.get("file") or route.get("file") or "").replace("\\", "/")
        line = int(ref.get("start_line") or route.get("line_start") or 0)
        if file_path and line >= 1:
            refs.append(
                {
                    "source_type": "route_intent",
                    "file": file_path,
                    "start_line": line,
                    "end_line": int(ref.get("end_line") or line),
                    "snippet": str(ref.get("snippet") or snippet or f"{route.get('method')} {route.get('path')}")[:500],
                }
            )
    if refs:
        return refs[:3]
    file_path = str(route.get("file") or "").replace("\\", "/")
    line = int(route.get("line_start") or 0)
    if file_path and line >= 1:
        return [
            {
                "source_type": "route_intent",
                "file": file_path,
                "start_line": line,
                "end_line": line,
                "snippet": str(snippet or f"{route.get('method')} {route.get('path')}")[:500],
            }
        ]
    return []


def _classify_route(route, repo_path):
    method = str(route.get("method") or "").upper()
    path = str(route.get("path") or "")
    file_path = str(route.get("file") or "").replace("\\", "/")
    window, snippet = _source_window(repo_path, route)
    combined = f"{path}\n{file_path}\n{window}"
    normalized = re.sub(r"[^a-z0-9]+", "/", combined.lower())
    tokens = set(normalized.split("/"))
    signals = []
    limitations = []

    protected = [name for name, pattern in PROTECTED_PATTERNS if pattern.search(combined)]
    account_delete = method == "DELETE" and (
        re.search(r"(^|[/_.-])(account|me)([/_.-]|$)", path, re.I)
        or re.search(r"\b(delete|softDelete)\s*\(", window)
    )
    if account_delete:
        protected.append("delete_account")
    if protected:
        signals.extend(f"protected:{name}" for name in sorted(set(protected)))
        intent = "protected_auth_operation"
        confidence = 0.94 if "auth" in tokens else 0.82
    else:
        public = [name for name, pattern in PUBLIC_PATTERNS if pattern.search(combined)]
        conflicts = sorted(word for word in CONFLICT_WORDS if word in tokens)
        auth_context = any(word in combined.lower() for word in AUTH_CONTEXT_WORDS)
        allowed_method = method in {"GET", "POST"}
        if public and conflicts:
            intent = "unknown"
            confidence = 0.55
            signals.extend(f"public_candidate:{name}" for name in public)
            signals.extend(f"sensitive_conflict:{name}" for name in conflicts)
            limitations.append("route_intent_conflict")
        elif public and auth_context and allowed_method:
            intent = "public_auth_entrypoint"
            confidence = 0.94
            signals.extend(f"public_auth:{name}" for name in public)
            signals.append("auth_context_observed")
        elif public:
            intent = "unknown"
            confidence = 0.58
            signals.extend(f"public_candidate:{name}" for name in public)
            limitations.append("possible_public_auth_entrypoint")
        elif any(word in tokens for word in SENSITIVE_WORDS):
            intent = "sensitive_business_operation"
            confidence = 0.76
            signals.append("sensitive_operation_keyword")
        else:
            intent = "unknown"
            confidence = 0.4
            signals.append("no_high_confidence_route_intent")

    return normalize_route_intent(
        {
            "method": method,
            "path": path,
            "file": file_path,
            "line_start": int(route.get("line_start") or 1),
            "intent": intent,
            "confidence": confidence,
            "signals": signals,
            "evidence_refs": _route_evidence(route, snippet),
            "limitations": limitations,
        }
    )


def classify_route_intents(routes, repo_path):
    annotations = [_classify_route(route, repo_path) for route in routes or []]
    annotations.sort(key=lambda row: (row["method"], row["path"], row["file"], row["line_start"], row["annotation_id"]))
    by_surface = {
        (row["method"], row["path"], row["file"], row["line_start"]): row
        for row in annotations
    }
    annotated_routes = []
    for route in routes or []:
        row = dict(route)
        key = (
            str(route.get("method") or "").upper(),
            str(route.get("path") or ""),
            str(route.get("file") or "").replace("\\", "/"),
            int(route.get("line_start") or 1),
        )
        annotation = by_surface.get(key)
        if annotation:
            row["intent"] = annotation["intent"]
            row["intent_confidence"] = annotation["confidence"]
            row["intent_signals"] = annotation["signals"]
            row["intent_limitations"] = annotation["limitations"]
            row["auth_guard_expected"] = annotation["intent"] != "public_auth_entrypoint"
            row["intent_annotation_id"] = annotation["annotation_id"]
        annotated_routes.append(row)
    return annotations, annotated_routes
