import re

from ..analysis.routes.typescript_decorator_classifier import (
    classify_typescript_decorators,
)
from .typescript_queue_cache import (
    detect_ts_cache_ops,
    detect_ts_queue_consume,
    detect_ts_queue_dispatch,
)
from .typescript_typeorm import detect_typeorm_transactions

_VERBS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "ALL"}


def _norm_path(p):
    s = str(p or "").strip()
    if not s:
        return "/"
    s = s.replace("\\", "/")
    while "//" in s:
        s = s.replace("//", "/")
    if not s.startswith("/"):
        s = "/" + s
    if len(s) > 1 and s.endswith("/"):
        s = s[:-1]
    return s


def _join_path(a, b):
    aa = _norm_path(a)
    bb = _norm_path(b)
    if bb == "/":
        return aa
    if aa == "/":
        return bb
    return _norm_path(aa + "/" + bb.lstrip("/"))


def detect_ts_express_routes(lines):
    out = []
    router_prefix = {}
    rx_use = re.compile(r"\bapp\.use\s*\(\s*(['\"])([^'\"]+)\1\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")
    for line in lines:
        mu = rx_use.search(line)
        if mu:
            router_prefix[mu.group(3)] = _norm_path(mu.group(2))
    rx = re.compile(r"\b(app|router)\.(get|post|put|delete|patch)\s*\(\s*(['\"])([^'\"]+)\3")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        method = m.group(2).upper()
        path = m.group(4)
        if method not in _VERBS or not path:
            continue
        sym = m.group(1)
        rp = ""
        if sym == "router":
            rp = router_prefix.get("router") or ""
        path_out = _join_path(rp, _norm_path(path)) if rp else _norm_path(path)
        out.append(
            {
                "framework": "express",
                "method": method,
                "path": path_out,
                "start_line": i,
                "end_line": i,
                "symbol": sym,
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_nest_routes(lines):
    result = classify_typescript_decorators(lines)
    return [
        {
            "framework": "nestjs",
            "method": route["method"],
            "path": route["path"],
            "start_line": route["line_start"],
            "end_line": route["line_end"],
            "symbol": route.get("handler_name") or "",
            "controller_prefix": route.get("controller_prefix") or "/",
            "parse_level": "L2",
        }
        for route in result["routes"]
    ]


def detect_ts_prisma_transactions(lines):
    out = []
    rx = re.compile(r"([A-Za-z0-9_$.]+)\.\$transaction\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        callee = m.group(1) + ".$transaction"
        out.append(
            {
                "framework": "prisma",
                "transaction_style": "prisma.$transaction",
                "callee_expr": callee,
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    return out


def detect_ts_typeorm_transactions(lines):
    out = []
    rx = re.compile(r"([A-Za-z0-9_$.]+)\.transaction\s*\(")
    for i, line in enumerate(lines, start=1):
        m = rx.search(line)
        if not m:
            continue
        callee_base = m.group(1)
        lb = callee_base.lower()
        if not any(x in lb for x in ["datasource", "manager", "connection"]):
            continue
        out.append(
            {
                "framework": "typeorm",
                "transaction_style": "typeorm.transaction",
                "callee_expr": callee_base + ".transaction",
                "start_line": i,
                "end_line": i,
                "parse_level": "L2",
            }
        )
    seen = {
        (item["start_line"], item["callee_expr"]): index
        for index, item in enumerate(out)
    }
    for item in detect_typeorm_transactions(lines):
        receiver_name = item.get("receiver_name") or ""
        operation = item.get("operation") or "transaction"
        callee = (
            f"{receiver_name}.{operation}"
            if receiver_name
            else operation
        )
        key = (item["line_start"], callee)
        if key in seen:
            existing = out[seen[key]]
            existing.update(
                {
                    "transaction_style": operation,
                    "receiver_kind": item.get("receiver_kind") or "unknown",
                    "receiver_name": receiver_name,
                    "transaction_context": item.get("transaction_context") or "unknown",
                    "signals": item.get("signals") or [],
                    "limitations": item.get("limitations") or [],
                    "scope": item.get("scope") or {},
                }
            )
            continue
        seen[key] = len(out)
        out.append(
            {
                "framework": "typeorm",
                "transaction_style": item.get("operation") or "typeorm.transaction",
                "callee_expr": callee,
                "receiver_kind": item.get("receiver_kind") or "unknown",
                "receiver_name": item.get("receiver_name") or "",
                "transaction_context": item.get("transaction_context") or "unknown",
                "signals": item.get("signals") or [],
                "limitations": item.get("limitations") or [],
                "scope": item.get("scope") or {},
                "start_line": item["line_start"],
                "end_line": item["line_end"],
                "parse_level": "L2",
            }
        )
    return sorted(out, key=lambda item: (item["start_line"], item["callee_expr"]))


def _extract_literal_arg(call_text):
    m = re.search(r"\(\s*(['\"])([^'\"]+)\1", call_text or "")
    if not m:
        return ""
    return m.group(2)
