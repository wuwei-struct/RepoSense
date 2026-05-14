import os
import re
import hashlib
from ..linking.path_normalize import normalize_path


_HTTP_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH"}


def _literal_to_text(tok):
    t = str(tok or "").strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"', "`"):
        return t[1:-1]
    return t


def _is_dynamic_template(tok):
    t = str(tok or "").strip()
    return t.startswith("`") and "${" in t


def _method_from_fetch_opts(line):
    m = re.search(r"method\s*:\s*['\"](GET|POST|PUT|DELETE|PATCH)['\"]", line or "", flags=re.I)
    if not m:
        return "GET", True
    return m.group(1).upper(), False


def detect_ts_http_callers(file_path, lines):
    callers = []
    unsupported = []
    text = "\n".join(lines)
    alias = set()
    for m in re.finditer(r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*axios\.create\s*\(", text):
        alias.add(m.group(1))
    for i, line in enumerate(lines, start=1):
        m = re.search(r"\bfetch\s*\(\s*(`[^`]*`|'[^']*'|\"[^\"]*\")", line)
        if m:
            lit = m.group(1)
            if _is_dynamic_template(lit):
                unsupported.append({
                    "type": "unsupported_detected",
                    "language": "typescript",
                    "framework": "fetch",
                    "path": file_path,
                    "line_start": i,
                    "reason": "saw_ts_fetch_usage_but_path_dynamic_skipped",
                })
            else:
                method, inferred = _method_from_fetch_opts(line)
                path_raw = _literal_to_text(lit)
                if method in _HTTP_VERBS and path_raw:
                    caller_id = hashlib.sha1(f"{file_path}|{i}|fetch|{method}|{path_raw}".encode("utf-8")).hexdigest()
                    callers.append({
                        "caller_id": caller_id,
                        "language": "typescript",
                        "source_kind": "ts_http_caller_l2",
                        "http_method": method,
                        "path_literal": path_raw,
                        "path_template": "",
                        "path_normalized": normalize_path(path_raw),
                        "client_kind": "fetch",
                        "file": file_path,
                        "line_start": i,
                        "line_end": i,
                        "snippet": line.strip(),
                        "confidence": 0.86 if not inferred else 0.8,
                        "parse_level": "L2",
                        "method_inferred": bool(inferred),
                    })
                    if inferred:
                        unsupported.append({
                            "type": "unsupported_detected",
                            "language": "typescript",
                            "framework": "fetch",
                            "path": file_path,
                            "line_start": i,
                            "reason": "saw_caller_method_unknown_default_get_inferred",
                        })
        for obj, cli in [("axios", "axios")] + [(a, "axios") for a in sorted(alias)]:
            m2 = re.search(rf"\b{re.escape(obj)}\.(get|post|put|delete|patch)\s*\(\s*(`[^`]*`|'[^']*'|\"[^\"]*\")", line)
            if not m2:
                continue
            method = m2.group(1).upper()
            lit = m2.group(2)
            if _is_dynamic_template(lit):
                unsupported.append({
                    "type": "unsupported_detected",
                    "language": "typescript",
                    "framework": "axios",
                    "path": file_path,
                    "line_start": i,
                    "reason": "saw_ts_axios_usage_but_path_dynamic_skipped",
                })
                continue
            path_raw = _literal_to_text(lit)
            if method in _HTTP_VERBS and path_raw:
                caller_id = hashlib.sha1(f"{file_path}|{i}|{obj}|{method}|{path_raw}".encode("utf-8")).hexdigest()
                callers.append({
                    "caller_id": caller_id,
                    "language": "typescript",
                    "source_kind": "ts_http_caller_l2",
                    "http_method": method,
                    "path_literal": path_raw,
                    "path_template": "",
                    "path_normalized": normalize_path(path_raw),
                    "client_kind": cli,
                    "file": file_path,
                    "line_start": i,
                    "line_end": i,
                    "snippet": line.strip(),
                    "confidence": 0.88,
                    "parse_level": "L2",
                    "method_inferred": False,
                })
    callers.sort(key=lambda x: (x["file"], x["line_start"], x["http_method"], x["path_normalized"], x["client_kind"]))
    unsupported.sort(key=lambda x: (x.get("path") or "", int(x.get("line_start") or 0), x.get("reason") or ""))
    return {"callers": callers, "unsupported": unsupported}


def collect_ts_http_callers(repo_root):
    out_callers = []
    out_unsupported = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "dist", "build", "coverage", ".next"}]
        for nm in sorted(files):
            ext = os.path.splitext(nm)[1].lower()
            if ext not in (".ts", ".tsx", ".mts", ".cts"):
                continue
            p = os.path.join(root, nm)
            try:
                txt = open(p, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            lines = txt.splitlines()
            rel = os.path.relpath(p, repo_root).replace("\\", "/")
            one = detect_ts_http_callers(rel, lines)
            out_callers.extend(one.get("callers") or [])
            out_unsupported.extend(one.get("unsupported") or [])
    out_callers.sort(key=lambda x: (x["file"], x["line_start"], x["http_method"], x["path_normalized"], x["client_kind"]))
    out_unsupported.sort(key=lambda x: (x.get("path") or "", int(x.get("line_start") or 0), x.get("reason") or ""))
    return {"callers": out_callers, "unsupported": out_unsupported}
