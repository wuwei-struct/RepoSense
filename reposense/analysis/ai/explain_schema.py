import hashlib


def _safe_int(v, d=0):
    try:
        return int(v)
    except Exception:
        return int(d)


def build_explain_request(target_type, target_id, with_drilldown=False, no_drilldown=False):
    tt = str(target_type or "").strip().lower()
    tid = str(target_id or "").strip()
    if tt not in ("pattern", "finding", "event"):
        raise ValueError("target_type must be pattern|finding|event")
    if not tid:
        raise ValueError("target_id is required")
    key = f"{tt}|{tid}|{bool(with_drilldown)}|{bool(no_drilldown)}"
    req_id = "ex-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return {
        "request_id": req_id,
        "target_type": tt,
        "target_id": tid,
        "with_drilldown": bool(with_drilldown),
        "no_drilldown": bool(no_drilldown),
    }


def normalize_claim(item, claim_type):
    x = item if isinstance(item, dict) else {}
    base = {
        "claim": str(x.get("claim") or ""),
        "evidence_refs": x.get("evidence_refs") if isinstance(x.get("evidence_refs"), list) else [],
        "snippet_refs": x.get("snippet_refs") if isinstance(x.get("snippet_refs"), list) else [],
    }
    if claim_type == "confirmed":
        base["because"] = str(x.get("because") or "")
        base["confidence"] = float(x.get("confidence") or 0.0)
    elif claim_type == "inferred":
        base["signals"] = x.get("signals") if isinstance(x.get("signals"), list) else []
        base["why_not_confirmed"] = str(x.get("why_not_confirmed") or "")
    else:
        base = {
            "question": str(x.get("question") or ""),
            "missing_evidence": x.get("missing_evidence") if isinstance(x.get("missing_evidence"), list) else [],
            "suggested_next_step": str(x.get("suggested_next_step") or ""),
        }
    return base


def normalize_explain_result(obj):
    o = obj if isinstance(obj, dict) else {}
    confirmed = [normalize_claim(x, "confirmed") for x in (o.get("confirmed") or [])]
    inferred = [normalize_claim(x, "inferred") for x in (o.get("inferred") or [])]
    unknown = [normalize_claim(x, "unknown") for x in (o.get("unknown") or [])]
    out = {
        "request_id": str(o.get("request_id") or ""),
        "run_dir": str(o.get("run_dir") or ""),
        "target_type": str(o.get("target_type") or ""),
        "target_id": str(o.get("target_id") or ""),
        "mode": str(o.get("mode") or "facts_only"),
        "confirmed": confirmed,
        "inferred": inferred,
        "unknown": unknown,
        "evidence_index": o.get("evidence_index") if isinstance(o.get("evidence_index"), list) else [],
        "snippet_pack_ref": o.get("snippet_pack_ref") if isinstance(o.get("snippet_pack_ref"), dict) else {},
        "limitations": o.get("limitations") if isinstance(o.get("limitations"), list) else [],
        "metadata": o.get("metadata") if isinstance(o.get("metadata"), dict) else {},
    }
    out["metadata"]["confirmed_count"] = _safe_int(len(confirmed))
    out["metadata"]["inferred_count"] = _safe_int(len(inferred))
    out["metadata"]["unknown_count"] = _safe_int(len(unknown))
    return out
