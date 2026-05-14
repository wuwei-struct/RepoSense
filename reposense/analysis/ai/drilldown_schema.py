import hashlib


DEFAULT_BUDGET = {
    "max_files": 5,
    "max_snippets": 8,
    "max_lines_per_snippet": 80,
    "context_lines": 25,
    "max_total_chars": 12000,
}


def _safe_int(value, default):
    try:
        return int(value)
    except Exception:
        return int(default)


def normalize_budget(budget=None):
    src = budget if isinstance(budget, dict) else {}
    out = {}
    for key, default in DEFAULT_BUDGET.items():
        v = _safe_int(src.get(key, default), default)
        out[key] = max(1, v)
    return out


def build_request(target_type, target_id, budget=None):
    tt = str(target_type or "").strip().lower()
    tid = str(target_id or "").strip()
    if tt not in ("pattern", "finding", "event"):
        raise ValueError("target_type must be pattern|finding|event")
    if not tid:
        raise ValueError("target_id is required")
    b = normalize_budget(budget)
    key = (
        f"{tt}|{tid}|{b['max_files']}|{b['max_snippets']}|"
        f"{b['max_lines_per_snippet']}|{b['context_lines']}|{b['max_total_chars']}"
    )
    req_id = "dd-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return {
        "request_id": req_id,
        "target_type": tt,
        "target_id": tid,
        "source_mode": "facts_first_drilldown",
        "budget": b,
    }


def normalize_source_ref(ref):
    r = ref if isinstance(ref, dict) else {}
    return {
        "pattern_id": str(r.get("pattern_id") or ""),
        "finding_id": str(r.get("finding_id") or ""),
        "event_id": str(r.get("event_id") or ""),
        "evidence_ref": {
            "source_type": str((r.get("evidence_ref") or {}).get("source_type") or r.get("source_type") or ""),
            "rule_id": str((r.get("evidence_ref") or {}).get("rule_id") or r.get("rule_id") or ""),
        },
    }


def normalize_snippet(item):
    src_refs = item.get("source_refs") if isinstance(item.get("source_refs"), list) else []
    refs = [normalize_source_ref(r) for r in src_refs]
    return {
        "snippet_id": str(item.get("snippet_id") or ""),
        "file": str(item.get("file") or ""),
        "line_start": _safe_int(item.get("line_start"), 0),
        "line_end": _safe_int(item.get("line_end"), 0),
        "context_before": _safe_int(item.get("context_before"), 0),
        "context_after": _safe_int(item.get("context_after"), 0),
        "snippet": str(item.get("snippet") or ""),
        "language": str(item.get("language") or "unknown"),
        "why_selected": str(item.get("why_selected") or ""),
        "source_refs": refs,
        "confidence": float(item.get("confidence") or 0.0),
    }


def normalize_snippet_pack(pack):
    p = pack if isinstance(pack, dict) else {}
    budget = normalize_budget(p.get("budget"))
    snippets = p.get("selected_snippets") if isinstance(p.get("selected_snippets"), list) else []
    normalized_snippets = [normalize_snippet(x) for x in snippets]
    files = sorted(
        set(
            [
                str(x.get("file") or "")
                for x in normalized_snippets
                if str(x.get("file") or "")
            ]
        )
    )
    return {
        "request_id": str(p.get("request_id") or ""),
        "run_dir": str(p.get("run_dir") or ""),
        "source_mode": "facts_first_drilldown",
        "target_type": str(p.get("target_type") or ""),
        "target_id": str(p.get("target_id") or ""),
        "selected_files": files,
        "selected_snippets": normalized_snippets,
        "budget": {
            **budget,
            "total_chars": _safe_int((p.get("budget") or {}).get("total_chars"), 0),
        },
        "selection_trace": p.get("selection_trace") if isinstance(p.get("selection_trace"), dict) else {},
        "limitations": p.get("limitations") if isinstance(p.get("limitations"), list) else [],
    }
