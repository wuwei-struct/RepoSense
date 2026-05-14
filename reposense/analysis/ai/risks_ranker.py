def _sev_score(sev):
    return {"high": 30, "medium": 20, "low": 10}.get(str(sev or "medium"), 20)


def _status_score(st):
    return {"confirmed": 20, "suspected": 10, "unknown": 5}.get(str(st or "suspected"), 10)


def _family_weight(ptype):
    boosts = {
        "transaction_missing": 12,
        "db_write_outside_tx": 12,
        "cross_language_api_unmatched": 9,
        "queue_without_consumer": 9,
        "api_write_without_idempotency_guard": 8,
        "hot_write_path": 7,
    }
    return boosts.get(str(ptype or ""), 4)


def score_risk_item(item, gate_obj=None):
    gate = gate_obj if isinstance(gate_obj, dict) else {}
    base = _sev_score(item.get("severity")) + _status_score(item.get("status")) + _family_weight(item.get("pattern_type"))
    ev_count = len(item.get("evidence_refs") or [])
    base += min(10, ev_count * 2)
    conf = float(item.get("confidence") or 0.0)
    base += int(conf * 10)
    g_status = str(gate.get("status") or "").lower()
    if g_status in ("warn", "fail"):
        base += 5
    return float(base)


def rank_risk_items(items, gate_obj=None):
    rows = []
    seen = set()
    for x in items or []:
        rid = str(x.get("risk_id") or "")
        if rid in seen:
            continue
        seen.add(rid)
        row = dict(x)
        row["priority_score"] = score_risk_item(row, gate_obj=gate_obj)
        rows.append(row)
    rows.sort(
        key=lambda x: (
            -float(x.get("priority_score") or 0.0),
            str(x.get("severity") or ""),
            str(x.get("status") or ""),
            str(x.get("risk_id") or ""),
        )
    )
    return rows
