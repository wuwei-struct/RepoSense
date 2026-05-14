import os
import json
from .utils import write_json
from .versioning import generated_by, ruleset_fingerprint


def load_gate_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"gate_id": "unknown", "version": "0", "rules": []}


def _read(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def collect_metrics(run_dir):
    rep = _read(os.path.join(run_dir, "report.json"), {})
    run_summary = rep.get("run_summary") or {}
    cov = _read(os.path.join(run_dir, "coverage.json"), {})
    api = _read(os.path.join(run_dir, "api_surface.json"), {"mismatches": {}})
    graph = _read(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    # artifacts_missing_count
    artifacts_missing = run_summary.get("artifacts_missing") or []
    amc = len(artifacts_missing)
    trunc = run_summary.get("truncation") or {}
    budget_cut = bool(trunc.get("budget_cut"))
    findings_trunc = bool(trunc.get("findings_truncated"))
    events_trunc = bool(trunc.get("events_truncated"))
    walk = cov.get("walk") or {}
    skipped = walk.get("skipped") or {}
    skipped_files = sum(v for v in skipped.values()) if isinstance(skipped, dict) else 0
    scanned_files = int(run_summary.get("scanned_files") or walk.get("included_files") or 0)
    denom = scanned_files + skipped_files
    skipped_ratio = (float(skipped_files) / float(denom)) if denom > 0 else 0.0
    skipped_top = []
    try:
        # run_summary provides list of [reason, count]
        rs = run_summary.get("skipped_files_by_reason") or []
        rs = sorted(rs, key=lambda x: x[1], reverse=True)
        skipped_top = rs[:3]
    except Exception:
        skipped_top = []
    warnings_count = len(cov.get("warnings") or [])
    api_missing_in_spec = len(((api.get("mismatches") or {}).get("missing_in_spec") or []))
    api_missing_in_code = len(((api.get("mismatches") or {}).get("missing_in_code") or []))
    events_count = int(run_summary.get("events_count") or len(graph.get("nodes") or []))
    graph_edges = int(run_summary.get("graph_edges") or len(graph.get("edges") or []))
    cid = cov.get("content_id") or (cov.get("stats") or {}).get("content_id")
    pid = cov.get("pack_id") or (cov.get("stats") or {}).get("pack_id")
    return {
        "artifacts_missing_count": amc,
        "budget_cut": budget_cut,
        "findings_truncated": findings_trunc,
        "events_truncated": events_trunc,
        "skipped_ratio": skipped_ratio,
        "scanned_files_count": scanned_files,
        "skipped_files_count": skipped_files,
        "skipped_files_by_reason_top": skipped_top,
        "warnings_count": warnings_count,
        "api.missing_in_spec_count": api_missing_in_spec,
        "api.missing_in_code_count": api_missing_in_code,
        "events_count": events_count,
        "graph_edges": graph_edges,
        "content_id": cid,
        "pack_id": pid,
    }


def _compare(actual, op, expected):
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    try:
        a = float(actual)
        b = float(expected)
    except Exception:
        a = actual
        b = expected
    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    return False


def _hint_for(metric):
    m = metric
    if m == "artifacts_missing_count":
        return "重新执行扫描并检查 run_dir 是否完整生成"
    if m == "budget_cut":
        return "调整预算文件：增大 max_files/max_total_bytes 等限额"
    if m in ("findings_truncated", "events_truncated"):
        return "增大预算中的 max_findings/max_events"
    if m == "skipped_ratio":
        return "减少忽略或增大预算，降低跳过比例"
    if m == "warnings_count":
        return "查看 coverage.json 的 warnings 并逐项修正"
    if m == "api.missing_in_spec_count":
        return "补充 OpenAPI 契约，覆盖代码中的接口"
    if m == "api.missing_in_code_count":
        return "实现契约中的接口或更新规范"
    if m == "graph_edges":
        return "检查 event_graph 是否生成边，并确认事件链接规则"
    return "请查看质量门禁规则，逐项修正"


def evaluate(metrics, gate_config, baseline_diff=None, baseline_paths=None):
    rules = gate_config.get("rules") or []
    violations = []
    for r in rules:
        metric = r.get("metric")
        op = r.get("op")
        expected = r.get("value")
        level = r.get("level", "warn")
        actual = metrics.get(metric)
        ok = _compare(actual, op, expected)
        if ok:
            violations.append({
                "level": level,
                "metric": metric,
                "actual": actual,
                "expected": expected,
                "op": op,
                "message": r.get("message") or "",
                "hint": _hint_for(metric),
            })
    violations.sort(key=lambda v: (0 if v["level"] == "fail" else 1, v["metric"]))
    status = "pass"
    if any(v["level"] == "fail" for v in violations):
        status = "fail"
    elif violations:
        status = "warn"
    out = {
        "status": status,
        "gate_id": gate_config.get("gate_id"),
        "gate_version": gate_config.get("version"),
        "metrics": {k: metrics[k] for k in ["artifacts_missing_count","budget_cut","findings_truncated","events_truncated","skipped_ratio","scanned_files_count","skipped_files_count","skipped_files_by_reason_top","warnings_count","api.missing_in_spec_count","api.missing_in_code_count","events_count","graph_edges","content_id","pack_id"] if k in metrics},
        "violations": violations,
        "hints": [v["hint"] for v in violations]
    }
    if baseline_diff:
        stats = baseline_diff.get("stats") or {}
        out["baseline_used"] = True
        out["baseline_compatible"] = bool(baseline_diff.get("compatible"))
        out["regressions"] = {"added_error": stats.get("added_error",0), "added_warning": stats.get("added_warning",0), "severity_upgrades": stats.get("severity_upgrades",0), "total": (stats.get("added_error",0)+stats.get("added_warning",0)+stats.get("severity_upgrades",0))}
        out["regression_samples_top"] = (baseline_diff.get("added") or [])[:5]
        if out["baseline_compatible"]:
            if out["status"] != "fail":
                if (stats.get("added_error",0) > 0) or (stats.get("severity_upgrades",0) > 0):
                    out["status"] = "fail"
                elif (stats.get("added_warning",0) > 0):
                    out["status"] = "warn"
        else:
            violations.append({
                "level": "warn",
                "metric": "baseline_incompatible",
                "actual": None,
                "expected": None,
                "op": "",
                "message": "Baseline incompatible; please refresh baseline on main",
                "hint": "Run baseline refresh workflow to update baselines"
            })
        if baseline_paths:
            out["baseline_paths"] = baseline_paths
    return out


def write_quality_gate(run_dir, obj):
    try:
        cfg = {}
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        rsdir = cfg.get("ruleset_dir") or ""
        rid = os.path.basename(rsdir) if rsdir else ""
        rfp = ruleset_fingerprint(rsdir) if rsdir and os.path.isdir(rsdir) else ""
        obj.setdefault("generated_by", generated_by("0.1.0", rid, rfp, 1))
    except Exception:
        obj.setdefault("generated_by", generated_by("0.1.0", "", "", 1))
    write_json(os.path.join(run_dir, "quality_gate.json"), obj)
    return os.path.join(run_dir, "quality_gate.json")
