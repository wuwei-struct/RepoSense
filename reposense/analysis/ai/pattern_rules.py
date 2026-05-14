from collections import defaultdict
from .pattern_schema import normalize_pattern
from ...events.taxonomy import normalize_event_kind


def _norm_event(node):
    meta = node.get("meta") or {}
    kind = normalize_event_kind(node.get("type"), meta=meta)
    path = str(meta.get("path") or "")
    start = int(meta.get("start_line") or 0)
    end = int(meta.get("end_line") or 0)
    lang = str(meta.get("language") or "unknown")
    fw = str(meta.get("framework") or "unknown")
    queue_name = str(
        meta.get("queue_name")
        or meta.get("topic_name")
        or meta.get("queue.task")
        or meta.get("job_name")
        or ""
    )
    return {
        "event_id": str(node.get("event_id") or ""),
        "raw_type": str(node.get("type") or ""),
        "event_kind": str(kind or ""),
        "key": str(node.get("key") or ""),
        "confidence": float(node.get("confidence") or 0.0),
        "path": path,
        "start_line": start,
        "end_line": end,
        "language": lang,
        "framework": fw,
        "queue_name": queue_name,
        "meta": meta,
    }


def _norm_finding(f):
    rid = str(f.get("rule_id") or "")
    snippet = str(f.get("snippet") or "")
    return {
        "fid": str(f.get("fid") or ""),
        "concept": str(f.get("concept") or ""),
        "rule_id": rid,
        "path": str(f.get("path") or ""),
        "start_line": int(f.get("start_line") or 0),
        "end_line": int(f.get("end_line") or 0),
        "confidence": float(f.get("confidence") or 0.0),
        "snippet": snippet,
        "text": " ".join([rid.lower(), snippet.lower(), str(f.get("concept") or "").lower()]),
        "meta": f.get("meta") if isinstance(f.get("meta"), dict) else {},
    }


def _event_ref(e):
    return {
        "source_type": "event",
        "event_id": e["event_id"],
        "file": e["path"],
        "start_line": e["start_line"],
        "end_line": e["end_line"],
        "rule_id": "",
    }


def _finding_ref(f):
    return {
        "source_type": "finding",
        "finding_id": f["fid"],
        "file": f["path"],
        "start_line": f["start_line"],
        "end_line": f["end_line"],
        "rule_id": f["rule_id"],
    }


def _mk_pattern(
    pattern_type,
    title,
    severity,
    confidence,
    summary,
    findings,
    events,
    status,
    explain_stub,
    metadata=None,
):
    refs = []
    for f in findings:
        refs.append(_finding_ref(f))
    for e in events:
        refs.append(_event_ref(e))
    files = sorted(set([str(r.get("file") or "") for r in refs if str(r.get("file") or "")]))
    langs = sorted(set([str(e.get("language") or "unknown") for e in events if e.get("language")]))
    fws = sorted(set([str(e.get("framework") or "unknown") for e in events if e.get("framework")]))
    return normalize_pattern(
        {
            "pattern_type": pattern_type,
            "title": title,
            "severity": severity,
            "confidence": confidence,
            "summary": summary,
            "supporting_findings": [f["fid"] for f in findings],
            "supporting_events": [e["event_id"] for e in events],
            "evidence_refs": refs,
            "files": files,
            "languages": langs,
            "frameworks": fws,
            "status": status,
            "explain_stub": explain_stub,
            "metadata": metadata or {},
        }
    )


def rule_transaction_missing(ctx):
    out = []
    events = [_norm_event(n) for n in (ctx.get("events") or [])]
    by_path = defaultdict(list)
    for e in events:
        by_path[e["path"]].append(e)
    for path, rows in by_path.items():
        apis = [x for x in rows if x["event_kind"] == "api.route"]
        dbw = [x for x in rows if x["event_kind"] == "db.write"]
        tx = [x for x in rows if x["event_kind"] == "db.transaction"]
        if apis and dbw and not tx:
            support = [apis[0], dbw[0]]
            out.append(
                _mk_pattern(
                    "transaction_missing",
                    "Write path lacks transaction boundary",
                    "high",
                    0.84,
                    f"API and DB write are observed at {path} but no transaction boundary is found.",
                    [],
                    support,
                    "confirmed",
                    "Add explicit transaction boundary around write operations in this API path.",
                    {"path": path},
                )
            )
    return out


def rule_db_write_outside_tx(ctx):
    out = []
    events = [_norm_event(n) for n in (ctx.get("events") or [])]
    by_path = defaultdict(list)
    for e in events:
        by_path[e["path"]].append(e)
    for path, rows in by_path.items():
        dbw = [x for x in rows if x["event_kind"] == "db.write"]
        tx = [x for x in rows if x["event_kind"] == "db.transaction"]
        if dbw and not tx:
            out.append(
                _mk_pattern(
                    "db_write_outside_tx",
                    "DB write outside transaction",
                    "high",
                    0.9,
                    f"DB write is observed at {path} without nearby transaction event.",
                    [],
                    [dbw[0]],
                    "confirmed",
                    "Wrap DB write path with transaction guard or explicit begin/commit boundary.",
                    {"path": path},
                )
            )
    return out


def rule_queue_without_consumer(ctx):
    out = []
    events = [_norm_event(n) for n in (ctx.get("events") or [])]
    dispatch = [x for x in events if x["event_kind"] == "queue.dispatch"]
    consume = [x for x in events if x["event_kind"] == "queue.consume"]
    consume_keys = set([(c.get("framework"), c.get("queue_name")) for c in consume])
    for d in dispatch:
        k = (d.get("framework"), d.get("queue_name"))
        if k in consume_keys:
            continue
        has_queue_name = bool(str(d.get("queue_name") or "").strip())
        status = "confirmed" if has_queue_name else "suspected"
        confidence = 0.8 if has_queue_name else 0.62
        out.append(
            _mk_pattern(
                "queue_without_consumer",
                "Queue dispatch without consumer evidence",
                "medium",
                confidence,
                "Queue dispatch is observed but no matching consume event is found in current run.",
                [],
                [d],
                status,
                "Ensure consumer side is present and observable for this queue/topic.",
                {"queue_name": d.get("queue_name") or "", "framework": d.get("framework") or "unknown"},
            )
        )
    return out


def _has_guard_signal(findings_for_path):
    keys = ["idempot", "dedup", "setnx", "exists", "unique", "guard", "cache key", "request key"]
    for f in findings_for_path:
        txt = f.get("text") or ""
        if any(k in txt for k in keys):
            return True
    return False


def rule_api_write_without_idempotency_guard(ctx):
    out = []
    events = [_norm_event(n) for n in (ctx.get("events") or [])]
    findings = [_norm_finding(f) for f in (ctx.get("findings") or [])]
    f_by_path = defaultdict(list)
    for f in findings:
        f_by_path[f["path"]].append(f)
    by_path = defaultdict(list)
    for e in events:
        by_path[e["path"]].append(e)
    for path, rows in by_path.items():
        api = [x for x in rows if x["event_kind"] == "api.route"]
        writes = [x for x in rows if x["event_kind"] in ("db.write", "queue.dispatch")]
        if not api or not writes:
            continue
        if _has_guard_signal(f_by_path.get(path) or []):
            continue
        fs = (f_by_path.get(path) or [])[:2]
        status = "suspected"
        out.append(
            _mk_pattern(
                "api_write_without_idempotency_guard",
                "Write API without idempotency guard",
                "medium",
                0.68,
                f"Write-like API path {path} has no explicit idempotency/guard signal.",
                fs,
                [api[0], writes[0]],
                status,
                "Add idempotency key or dedupe guard for write API endpoint.",
                {"path": path},
            )
        )
    return out


def rule_cross_language_api_unmatched(ctx):
    out = []
    summary = ctx.get("cross_language_summary") if isinstance(ctx.get("cross_language_summary"), dict) else {}
    links = ctx.get("cross_language_links") if isinstance(ctx.get("cross_language_links"), dict) else {}
    uc = int(summary.get("unmatched_callers") or 0)
    ue = int(summary.get("endpoints_without_callers") or summary.get("unmatched_endpoints") or 0)
    if uc <= 0 and ue <= 0:
        return out
    ev = []
    for x in (links.get("unmatched_callers") or [])[:3]:
        ev.append(
            {
                "source_type": "cross_language",
                "file": str(x.get("file") or ""),
                "start_line": int(x.get("line_start") or 0),
                "end_line": int(x.get("line_end") or 0),
                "rule_id": "cross_language.unmatched_caller",
            }
        )
    for x in (links.get("unmatched_endpoints") or [])[:3]:
        ev.append(
            {
                "source_type": "cross_language",
                "file": str(x.get("file") or ""),
                "start_line": int(x.get("line_start") or 0),
                "end_line": int(x.get("line_end") or 0),
                "rule_id": "cross_language.unmatched_endpoint",
            }
        )
    if not ev:
        ev.append({"source_type": "cross_language", "file": "cross_language_summary.json", "start_line": 1, "end_line": 1, "rule_id": "cross_language.unmatched"})
    out.append(
        normalize_pattern(
            {
                "pattern_type": "cross_language_api_unmatched",
                "title": "Cross-language API mismatch",
                "severity": "medium",
                "confidence": 0.86,
                "summary": f"Cross-language linking has unmatched callers={uc}, unmatched endpoints={ue}.",
                "supporting_findings": [],
                "supporting_events": [],
                "evidence_refs": ev,
                "files": sorted(set([str(x.get("file") or "") for x in ev if str(x.get("file") or "")])),
                "languages": ["typescript", "java"],
                "frameworks": [],
                "status": "confirmed",
                "explain_stub": "Align API caller paths/methods with backend endpoint contracts.",
                "metadata": {"unmatched_callers": uc, "unmatched_endpoints": ue},
            }
        )
    )
    return out


def rule_hot_write_path(ctx):
    out = []
    events = [_norm_event(n) for n in (ctx.get("events") or [])]
    findings = [_norm_finding(f) for f in (ctx.get("findings") or [])]
    by_path = defaultdict(list)
    for e in events:
        by_path[e["path"]].append(e)
    f_by_path = defaultdict(list)
    for f in findings:
        f_by_path[f["path"]].append(f)
    for path, rows in by_path.items():
        has_api = any(x["event_kind"] == "api.route" for x in rows)
        has_dbw = any(x["event_kind"] == "db.write" for x in rows)
        has_qd = any(x["event_kind"] == "queue.dispatch" for x in rows)
        has_cw = any(x["event_kind"] == "cache.write" for x in rows)
        hi_findings = [f for f in (f_by_path.get(path) or []) if f["concept"].lower() in ("transaction", "queue", "db", "cache")]
        if not has_api:
            continue
        if (has_dbw and has_qd and has_cw) or len(hi_findings) >= 2:
            status = "confirmed" if (has_dbw and has_qd and has_cw) else "suspected"
            confidence = 0.78 if status == "confirmed" else 0.64
            evs = [x for x in rows if x["event_kind"] in ("api.route", "db.write", "queue.dispatch", "cache.write")][:3]
            out.append(
                _mk_pattern(
                    "hot_write_path",
                    "Complex write path",
                    "medium",
                    confidence,
                    f"Path {path} combines multiple write-side signals and risk findings.",
                    hi_findings[:2],
                    evs,
                    status,
                    "Reduce write-path complexity by separating side effects and adding protective boundaries.",
                    {"path": path, "db_write": has_dbw, "queue_dispatch": has_qd, "cache_write": has_cw},
                )
            )
    return out


def run_all_rules(ctx):
    rules = [
        rule_transaction_missing,
        rule_db_write_outside_tx,
        rule_queue_without_consumer,
        rule_api_write_without_idempotency_guard,
        rule_cross_language_api_unmatched,
        rule_hot_write_path,
    ]
    out = []
    for fn in rules:
        out.extend(fn(ctx))
    return out
