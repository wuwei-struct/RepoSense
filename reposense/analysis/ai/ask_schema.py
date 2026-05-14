import hashlib


def build_ask_request(run_dir, question, with_drilldown=False, no_drilldown=False):
    q = str(question or "").strip()
    if not q:
        raise ValueError("question is required")
    key = f"{str(run_dir or '')}|{q}|{bool(with_drilldown)}|{bool(no_drilldown)}"
    req_id = "ask-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return {
        "request_id": req_id,
        "run_dir": str(run_dir or ""),
        "question": q,
        "with_drilldown": bool(with_drilldown),
        "no_drilldown": bool(no_drilldown),
    }


def normalize_answer(obj):
    o = obj if isinstance(obj, dict) else {}
    return {
        "request_id": str(o.get("request_id") or ""),
        "run_dir": str(o.get("run_dir") or ""),
        "question": str(o.get("question") or ""),
        "question_type": str(o.get("question_type") or "unsupported"),
        "mode": str(o.get("mode") or "facts_only"),
        "confirmed": o.get("confirmed") if isinstance(o.get("confirmed"), list) else [],
        "inferred": o.get("inferred") if isinstance(o.get("inferred"), list) else [],
        "unknown": o.get("unknown") if isinstance(o.get("unknown"), list) else [],
        "evidence_index": o.get("evidence_index") if isinstance(o.get("evidence_index"), list) else [],
        "limitations": o.get("limitations") if isinstance(o.get("limitations"), list) else [],
        "metadata": o.get("metadata") if isinstance(o.get("metadata"), dict) else {},
    }
