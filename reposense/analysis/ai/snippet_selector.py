from collections import defaultdict


def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return int(default)


def _norm_ref(ref, target_type, target_id):
    r = ref if isinstance(ref, dict) else {}
    path = str(r.get("file") or r.get("path") or "")
    start = _safe_int(r.get("start_line") or r.get("line_start") or 0, 0)
    end = _safe_int(r.get("end_line") or r.get("line_end") or start, start)
    if end < start:
        start, end = end, start
    if start <= 0:
        start = 1
    if end <= 0:
        end = start
    return {
        "file": path,
        "start_line": start,
        "end_line": end,
        "source_type": str(r.get("source_type") or ""),
        "rule_id": str(r.get("rule_id") or ""),
        "why_selected": "evidence_ref",
        "source_ref": {
            "pattern_id": target_id if target_type == "pattern" else "",
            "finding_id": target_id if target_type == "finding" else str(r.get("finding_id") or ""),
            "event_id": target_id if target_type == "event" else str(r.get("event_id") or ""),
            "source_type": str(r.get("source_type") or ""),
            "rule_id": str(r.get("rule_id") or ""),
        },
        "confidence": float(r.get("confidence") or 0.75),
    }


def _collect_for_pattern(pattern, findings_by_id, events_by_id):
    refs = []
    for r in pattern.get("evidence_refs") or []:
        refs.append(_norm_ref(r, "pattern", str(pattern.get("pattern_id") or "")))
    for fid in pattern.get("supporting_findings") or []:
        f = findings_by_id.get(str(fid))
        if not f:
            continue
        refs.append(
            _norm_ref(
                {
                    "file": f.get("path"),
                    "start_line": f.get("start_line"),
                    "end_line": f.get("end_line"),
                    "source_type": "finding",
                    "rule_id": f.get("rule_id"),
                    "finding_id": f.get("fid"),
                    "confidence": f.get("confidence"),
                },
                "pattern",
                str(pattern.get("pattern_id") or ""),
            )
        )
    for eid in pattern.get("supporting_events") or []:
        e = events_by_id.get(str(eid))
        if not e:
            continue
        meta = e.get("meta") or {}
        refs.append(
            _norm_ref(
                {
                    "file": meta.get("path"),
                    "start_line": meta.get("start_line"),
                    "end_line": meta.get("end_line"),
                    "source_type": "event",
                    "event_id": e.get("event_id"),
                    "confidence": e.get("confidence"),
                },
                "pattern",
                str(pattern.get("pattern_id") or ""),
            )
        )
    return refs


def _collect_refs(facts, target_type, target_id):
    findings = facts.get("findings") or []
    events = facts.get("events") or []
    patterns = facts.get("patterns") or []
    findings_by_id = {str(x.get("fid") or ""): x for x in findings}
    events_by_id = {str(x.get("event_id") or ""): x for x in events}
    if target_type == "pattern":
        p = next((x for x in patterns if str(x.get("pattern_id") or "") == target_id), None)
        return _collect_for_pattern(p or {}, findings_by_id, events_by_id) if p else []
    if target_type == "finding":
        f = findings_by_id.get(target_id)
        if not f:
            return []
        return [
            _norm_ref(
                {
                    "file": f.get("path"),
                    "start_line": f.get("start_line"),
                    "end_line": f.get("end_line"),
                    "source_type": "finding",
                    "rule_id": f.get("rule_id"),
                    "finding_id": f.get("fid"),
                    "confidence": f.get("confidence"),
                },
                target_type,
                target_id,
            )
        ]
    e = events_by_id.get(target_id)
    if not e:
        return []
    meta = e.get("meta") or {}
    return [
        _norm_ref(
            {
                "file": meta.get("path"),
                "start_line": meta.get("start_line"),
                "end_line": meta.get("end_line"),
                "source_type": "event",
                "event_id": e.get("event_id"),
                "confidence": e.get("confidence"),
            },
            target_type,
            target_id,
        )
    ]


def _expand_window(ref, context_lines):
    start = max(1, _safe_int(ref.get("start_line"), 1) - context_lines)
    end = max(start, _safe_int(ref.get("end_line"), start) + context_lines)
    out = dict(ref)
    out["line_start"] = start
    out["line_end"] = end
    out["context_before"] = context_lines
    out["context_after"] = context_lines
    return out


def _merge_ranges(rows, max_lines_per_snippet):
    if not rows:
        return []
    rows = sorted(rows, key=lambda x: (x["line_start"], x["line_end"]))
    merged = []
    cur = dict(rows[0])
    cur["source_refs"] = [cur.pop("source_ref")]
    for r in rows[1:]:
        near = r["line_start"] <= (cur["line_end"] + 5)
        if near:
            cur["line_end"] = max(cur["line_end"], r["line_end"])
            cur["source_refs"].append(r["source_ref"])
            cur["confidence"] = max(float(cur.get("confidence") or 0.0), float(r.get("confidence") or 0.0))
            continue
        merged.append(cur)
        cur = dict(r)
        cur["source_refs"] = [cur.pop("source_ref")]
    merged.append(cur)
    out = []
    for x in merged:
        start = x["line_start"]
        end = x["line_end"]
        if end - start + 1 > max_lines_per_snippet:
            end = start + max_lines_per_snippet - 1
        x["line_start"] = start
        x["line_end"] = end
        x["why_selected"] = "evidence_ref_window"
        out.append(x)
    return out


def select_candidates(facts, request):
    budget = request.get("budget") or {}
    context_lines = _safe_int(budget.get("context_lines"), 25)
    max_files = _safe_int(budget.get("max_files"), 5)
    max_snippets = _safe_int(budget.get("max_snippets"), 8)
    max_lines = _safe_int(budget.get("max_lines_per_snippet"), 80)

    refs = _collect_refs(
        facts,
        str(request.get("target_type") or ""),
        str(request.get("target_id") or ""),
    )
    refs = [x for x in refs if str(x.get("file") or "")]
    expanded = [_expand_window(r, context_lines) for r in refs]
    by_file = defaultdict(list)
    for r in expanded:
        by_file[str(r["file"])].append(r)
    file_rows = []
    for fpath, rows in by_file.items():
        file_rows.append((fpath, _merge_ranges(rows, max_lines)))
    file_rows.sort(key=lambda x: (-len(x[1]), x[0]))
    file_rows = file_rows[:max_files]
    candidates = []
    for fpath, rows in file_rows:
        for row in sorted(rows, key=lambda x: (x["line_start"], x["line_end"])):
            row["file"] = fpath
            candidates.append(row)
    candidates.sort(key=lambda x: (str(x.get("file") or ""), int(x.get("line_start") or 0), int(x.get("line_end") or 0)))
    candidates = candidates[:max_snippets]
    trace = {
        "candidate_refs": len(refs),
        "expanded_ranges": len(expanded),
        "selected_files": len(file_rows),
        "selected_snippets": len(candidates),
        "strategy": ["evidence_first", "window_expand", "same_file_merge", "budget_clip"],
    }
    return {"candidates": candidates, "selection_trace": trace}
