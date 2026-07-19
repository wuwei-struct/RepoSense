from collections import defaultdict
from .pattern_schema import normalize_pattern
from ...events.taxonomy import normalize_event_kind
from ...evidence.location import canonicalize_evidence_ref, filter_valid_evidence_refs


def _norm_event(node, evidence_by_id=None):
    meta = node.get("meta") or {}
    kind = normalize_event_kind(node.get("type"), meta=meta)
    canonical = None
    evidence_by_id = evidence_by_id if isinstance(evidence_by_id, dict) else {}
    for evidence_id in node.get("evidence") or []:
        canonical = canonicalize_evidence_ref(evidence_by_id.get(str(evidence_id)))
        if canonical is not None:
            break
    scope = meta.get("scope") if isinstance(meta.get("scope"), dict) else {}
    path = str((canonical or {}).get("file") or meta.get("path") or "")
    start = int((canonical or {}).get("start_line") or meta.get("start_line") or scope.get("start_line") or 0)
    end = int((canonical or {}).get("end_line") or meta.get("end_line") or scope.get("end_line") or 0)
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
    return canonicalize_evidence_ref({
        "source_type": "event",
        "event_id": e["event_id"],
        "file": e["path"],
        "start_line": e["start_line"],
        "end_line": e["end_line"],
        "rule_id": "",
    })


def _finding_ref(f):
    return canonicalize_evidence_ref({
        "source_type": "finding",
        "finding_id": f["fid"],
        "file": f["path"],
        "start_line": f["start_line"],
        "end_line": f["end_line"],
        "rule_id": f["rule_id"],
    })


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
    extra_evidence_refs=None,
):
    refs = []
    for f in findings:
        ref = _finding_ref(f)
        if ref is not None:
            refs.append(ref)
    for e in events:
        ref = _event_ref(e)
        if ref is not None:
            refs.append(ref)
    refs.extend(extra_evidence_refs if isinstance(extra_evidence_refs, list) else [])
    refs, invalid_ref_count = filter_valid_evidence_refs(refs)
    metadata = dict(metadata or {})
    if invalid_ref_count or not refs:
        limitations = metadata.get("limitations") if isinstance(metadata.get("limitations"), list) else []
        metadata["limitations"] = sorted(set([str(x) for x in limitations] + ["source_location_unavailable"]))
        status = "suspected"
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
            "metadata": metadata,
        }
    )


def rule_transaction_missing(ctx):
    out = []
    events = [_norm_event(n, ctx.get("evidence_by_id")) for n in (ctx.get("events") or [])]
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
    events = [_norm_event(n, ctx.get("evidence_by_id")) for n in (ctx.get("events") or [])]
    correlation_artifact = ctx.get("transaction_correlations") if isinstance(ctx.get("transaction_correlations"), dict) else {}
    correlation_rows = correlation_artifact.get("correlations") if isinstance(correlation_artifact.get("correlations"), list) else []
    correlation_by_event = {
        str(row.get("db_event_id") or ""): row
        for row in correlation_rows
        if isinstance(row, dict) and str(row.get("db_event_id") or "")
    }
    correlation_enabled = bool(correlation_artifact.get("version"))
    by_path = defaultdict(list)
    for e in events:
        by_path[e["path"]].append(e)
    for path, rows in by_path.items():
        dbw = [x for x in rows if x["event_kind"] == "db.write"]
        tx = [x for x in rows if x["event_kind"] == "db.transaction"]
        if dbw and not tx:
            correlations = [correlation_by_event.get(event["event_id"]) for event in dbw]
            correlations = [row for row in correlations if isinstance(row, dict)]
            statuses = [str(row.get("coverage_status") or "unknown") for row in correlations]
            if correlation_enabled and len(correlations) == len(dbw) and statuses and set(statuses) == {"covered_explicit"}:
                continue

            status = "confirmed"
            confidence = 0.9
            limitations = []
            summary = f"DB write is observed at {path} without nearby transaction event."
            extra_refs = []
            if correlation_enabled and correlations:
                correlation_ids = [str(row.get("correlation_id") or "") for row in correlations]
                for row in correlations:
                    extra_refs.extend(row.get("callsite_evidence_refs") or [])
                    extra_refs.extend(row.get("db_write_evidence_refs") or [])
                    limitations.extend(row.get("limitations") or [])
                status_set = set(statuses)
                if status_set == {"uncovered"} and len(correlations) == len(dbw):
                    summary = f"DB write at {path} has a resolved direct caller without explicit transaction coverage."
                else:
                    status = "suspected"
                    confidence = 0.68
                    if "partially_covered" in status_set or len(status_set) > 1:
                        limitations.append("partial_transaction_coverage")
                    elif "read_only_transaction" in status_set:
                        limitations.append("write_call_inside_read_only_transaction")
                    else:
                        limitations.append("transaction_coverage_unresolved")
                    summary = f"DB write at {path} has incomplete or unresolved explicit transaction coverage."
            elif correlation_enabled:
                status = "suspected"
                confidence = 0.62
                limitations.append("transaction_coverage_unresolved")
                summary = f"DB write at {path} has no resolvable cross-layer transaction correlation."
                correlation_ids = []
            else:
                correlation_ids = []
            typeorm_writes = [
                event
                for event in dbw
                if str(event.get("framework") or "").lower() == "typeorm"
            ]
            explicit_typeorm_writes = [
                event
                for event in typeorm_writes
                if str((event.get("meta") or {}).get("transaction_context") or "")
                in {"explicit_callback", "query_runner_explicit"}
            ]
            if typeorm_writes and len(explicit_typeorm_writes) == len(dbw):
                continue
            if typeorm_writes:
                status = "suspected"
                confidence = min(confidence, 0.66)
                typeorm_statuses = {
                    str(row.get("coverage_status") or "unknown")
                    for row in correlations
                    if str(row.get("language") or "") == "typescript"
                }
                if not typeorm_statuses or typeorm_statuses == {"unknown"}:
                    limitations.append(
                        "typescript_transaction_coverage_unresolved"
                    )
                    summary = (
                        f"TypeORM DB write is observed at {path}, but static "
                        "analysis cannot resolve complete TypeScript transaction "
                        "coverage."
                    )
            out.append(
                _mk_pattern(
                    "db_write_outside_tx",
                    "DB write outside transaction",
                    "high",
                    confidence,
                    summary,
                    [],
                    [dbw[0]],
                    status,
                    "Wrap DB write path with transaction guard or explicit begin/commit boundary.",
                    {
                        "path": path,
                        "transaction_correlation_ids": correlation_ids,
                        "transaction_coverage_statuses": statuses,
                        "limitations": sorted(set(str(x) for x in limitations if str(x))),
                    },
                    extra_evidence_refs=extra_refs,
                )
            )
    return out


def rule_queue_without_consumer(ctx):
    out = []
    events = [_norm_event(n, ctx.get("evidence_by_id")) for n in (ctx.get("events") or [])]
    dispatch = [x for x in events if x["event_kind"] == "queue.dispatch"]
    consume = [x for x in events if x["event_kind"] == "queue.consume"]

    def identity(event):
        meta = event.get("meta") or {}
        name = str(
            meta.get("queue_name") or meta.get("topic_name") or ""
        ).strip()
        if meta.get("queue_name_resolved") is False or not name:
            return None
        return (str(event.get("framework") or "unknown"), name)

    consume_keys = {
        identity(event)
        for event in consume
        if identity(event) is not None
    }
    for d in dispatch:
        key = identity(d)
        if key is not None and key in consume_keys:
            continue
        has_resolved_queue_name = key is not None
        status = "confirmed" if has_resolved_queue_name else "suspected"
        confidence = 0.8 if has_resolved_queue_name else 0.58
        limitations = (
            [] if has_resolved_queue_name else ["queue_name_unresolved"]
        )
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
                {
                    "queue_name": key[1] if key is not None else "",
                    "framework": d.get("framework") or "unknown",
                    "limitations": limitations,
                },
            )
        )
    return out


def rule_queue_reliability(ctx):
    payload = ctx.get("queue_reliability_risks")
    risks = payload.get("risks") if isinstance(payload, dict) else []
    out = []
    for risk in risks if isinstance(risks, list) else []:
        pattern_type = str(risk.get("pattern_type") or "")
        if pattern_type not in {
            "queue_retry_without_idempotency_guard",
            "queue_consumer_side_effect_without_idempotency_evidence",
        }:
            continue
        pattern = _mk_pattern(
            pattern_type,
            str(risk.get("title") or pattern_type),
            "medium",
            min(float(risk.get("confidence") or 0.0), 0.82),
            str(risk.get("reason") or ""),
            [],
            [],
            "suspected",
            (
                "Review duplicate-delivery behavior and confirm a persistent "
                "or atomic consumer idempotency guard."
            ),
            {
                "correlation_id": str(risk.get("correlation_id") or ""),
                "queue_or_topic": str(risk.get("queue_or_topic") or ""),
                "framework": str(risk.get("framework") or "unknown"),
                "limitations": list(risk.get("limitations") or []),
            },
            extra_evidence_refs=risk.get("evidence_refs"),
        )
        pattern["frameworks"] = [
            str(risk.get("framework") or "unknown")
        ]
        pattern["languages"] = [
            (
                "java"
                if str(risk.get("framework") or "").startswith("spring_")
                else "typescript"
            )
        ]
        out.append(normalize_pattern(pattern))
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
    events = [_norm_event(n, ctx.get("evidence_by_id")) for n in (ctx.get("events") or [])]
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
    ev, invalid_ref_count = filter_valid_evidence_refs(ev)
    metadata = {"unmatched_callers": uc, "unmatched_endpoints": ue}
    status = "confirmed"
    if invalid_ref_count or not ev:
        metadata["limitations"] = ["source_location_unavailable"]
        status = "suspected"
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
                "status": status,
                "explain_stub": "Align API caller paths/methods with backend endpoint contracts.",
                "metadata": metadata,
            }
        )
    )
    return out


def rule_hot_write_path(ctx):
    out = []
    events = [_norm_event(n, ctx.get("evidence_by_id")) for n in (ctx.get("events") or [])]
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
        rule_queue_reliability,
        rule_api_write_without_idempotency_guard,
        rule_cross_language_api_unmatched,
        rule_hot_write_path,
    ]
    out = []
    for fn in rules:
        out.extend(fn(ctx))
    return out
