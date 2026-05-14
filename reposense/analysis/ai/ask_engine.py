import json
import os

from .ask_classifier import classify_question
from .ask_schema import build_ask_request, normalize_answer
from .explain_export import export_ai_explain


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _mk_claim(claim, because="", evidence=None):
    return {
        "claim": str(claim or ""),
        "because": str(because or ""),
        "evidence_refs": evidence if isinstance(evidence, list) else [],
        "snippet_refs": [],
    }


def _summarize_supported():
    return [
        "这个系统主要做什么？（summary）",
        "这个系统最值得优先修复的风险是什么？（risk）",
        "为什么你说这里有风险，证据是什么？（evidence）",
        "订单路径里有没有 queue 和 db 写入？（flow）",
    ]


def _answer_summary(run_dir):
    s = _read_json(os.path.join(run_dir, "ai_summary.json"), {})
    ov = s.get("project_overview") if isinstance(s.get("project_overview"), dict) else {}
    st = s.get("stack_summary") if isinstance(s.get("stack_summary"), dict) else {}
    confirmed = [
        _mk_claim(
            "项目概览已可用。",
            f"languages={','.join(ov.get('languages') or []) or 'none'}, frameworks={','.join(ov.get('frameworks') or []) or 'none'}",
            [],
        ),
        _mk_claim(
            "结构面计数已可用。",
            "来自 ai_summary 的 surface/flow 聚合。",
            [],
        ),
    ]
    inferred = [
        {
            "claim": "当前架构以后端 API + DB/Queue 事件为主。",
            "signals": [",".join(st.get("db_hints") or []), ",".join(st.get("queue_hints") or [])],
            "why_not_confirmed": "仅基于静态 facts 聚合，不代表完整运行时覆盖。",
            "evidence_refs": [],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "是否覆盖了所有运行时路径？",
            "missing_evidence": ["runtime trace", "跨服务观测"],
            "suggested_next_step": "结合更多 run 或生产观测补齐。",
        }
    ]
    return confirmed, inferred, unknown, []


def _answer_risk(run_dir):
    r = _read_json(os.path.join(run_dir, "ai_risks", "risks.json"), {})
    items = r.get("risk_items") if isinstance(r.get("risk_items"), list) else []
    top = items[:3]
    confirmed = [
        _mk_claim(
            f"已识别风险 {len(items)} 条。",
            "来自 ai_risks 聚合排序结果。",
            [],
        )
    ]
    for x in top:
        confirmed.append(
            _mk_claim(
                f"优先风险：{str(x.get('title') or '')} ({str(x.get('severity') or '')}/{str(x.get('status') or '')})",
                str(x.get("recommended_action") or ""),
                x.get("evidence_refs") or [],
            )
        )
    inferred = [
        {
            "claim": "中高优先级项应先处理一致性/闭环风险。",
            "signals": [str(x.get("pattern_type") or "") for x in top],
            "why_not_confirmed": "处置顺序仍需结合业务上下文。",
            "evidence_refs": [],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "哪个风险对业务影响最大？",
            "missing_evidence": ["业务影响权重", "流量/事故数据"],
            "suggested_next_step": "引入业务优先级与生产指标联合排序。",
        }
    ]
    ev = []
    for x in top:
        ev.extend(x.get("evidence_refs") or [])
    return confirmed, inferred, unknown, ev[:20]


def _answer_evidence(run_dir, with_drilldown=False, no_drilldown=False):
    patterns_obj = _read_json(os.path.join(run_dir, "patterns.json"), {"patterns": []})
    patterns = patterns_obj.get("patterns") if isinstance(patterns_obj, dict) else []
    target = next((p for p in patterns if str(p.get("status") or "") == "suspected"), None) or (patterns[0] if patterns else {})
    pid = str(target.get("pattern_id") or "")
    ex = {}
    mode = "facts_only"
    if pid:
        need_dd = (with_drilldown and not no_drilldown) or (str(target.get("status") or "") == "suspected" and not no_drilldown)
        if need_dd:
            exr = export_ai_explain(run_dir, "pattern", pid, with_drilldown=True, no_drilldown=False)
            ex = exr.get("result") or {}
            mode = "facts_plus_drilldown"
        else:
            exr = export_ai_explain(run_dir, "pattern", pid, with_drilldown=False, no_drilldown=True)
            ex = exr.get("result") or {}
    confirmed = []
    if ex:
        confirmed.append(
            _mk_claim(
                f"证据目标：pattern {pid}",
                "来自 explain 产物。",
                ex.get("evidence_index") or [],
            )
        )
    inferred = [
        {
            "claim": "部分结论依赖上下文窗口而非完整仓库语义。",
            "signals": [mode],
            "why_not_confirmed": "受限于 evidence-first 下钻策略。",
            "evidence_refs": ex.get("evidence_index") or [],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "是否存在未覆盖的跨文件实现分支？",
            "missing_evidence": ["跨文件控制流", "运行时分支命中"],
            "suggested_next_step": "对目标路径追加 explain/drilldown 并人工复核。",
        }
    ]
    return confirmed, inferred, unknown, ex.get("evidence_index") or [], mode


def _answer_flow(run_dir, with_drilldown=False, no_drilldown=False):
    graph = _read_json(os.path.join(run_dir, "event_graph.json"), {"nodes": [], "edges": []})
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    kinds = []
    for n in nodes:
        t = str(n.get("type") or "").lower()
        if "queue" in t:
            kinds.append("queue")
        if "db" in t:
            kinds.append("db")
        if "api" in t:
            kinds.append("api")
    kinds = sorted(set(kinds))
    confirmed = [
        _mk_claim(
            f"当前可见流程信号：{', '.join(kinds) if kinds else 'none'}",
            "基于 event_graph 节点类型聚合。",
            [],
        )
    ]
    mode = "facts_only"
    inferred = [
        {
            "claim": "流程链路可能包含更多跨文件步骤。",
            "signals": kinds,
            "why_not_confirmed": "flow v1 仅做轻量事件族聚合。",
            "evidence_refs": [],
            "snippet_refs": [],
        }
    ]
    unknown = [
        {
            "question": "完整调用顺序是否闭环？",
            "missing_evidence": ["更细粒度依赖边", "跨服务调用事实"],
            "suggested_next_step": "针对目标 event 运行 explain 或 drilldown。",
        }
    ]
    if with_drilldown and not no_drilldown and nodes:
        eid = str(nodes[0].get("event_id") or "")
        if eid:
            export_ai_explain(run_dir, "event", eid, with_drilldown=True, no_drilldown=False)
            mode = "facts_plus_drilldown"
    return confirmed, inferred, unknown, [], mode


def generate_ask_answer(run_dir, question, with_drilldown=False, no_drilldown=False):
    req = build_ask_request(run_dir, question, with_drilldown=with_drilldown, no_drilldown=no_drilldown)
    qtype = classify_question(req["question"])
    mode = "facts_only"
    evidence = []
    if qtype == "summary":
        confirmed, inferred, unknown, evidence = _answer_summary(run_dir)
    elif qtype == "risk":
        confirmed, inferred, unknown, evidence = _answer_risk(run_dir)
    elif qtype == "evidence":
        confirmed, inferred, unknown, evidence, mode = _answer_evidence(
            run_dir, with_drilldown=with_drilldown, no_drilldown=no_drilldown
        )
    elif qtype == "flow":
        confirmed, inferred, unknown, evidence, mode = _answer_flow(
            run_dir, with_drilldown=with_drilldown, no_drilldown=no_drilldown
        )
    else:
        confirmed = [
            _mk_claim("当前问题类型不在受支持范围。", "仅支持 summary/risk/evidence/flow 四类。", []),
        ]
        inferred = []
        unknown = [
            {
                "question": "你可以换一种问法吗？",
                "missing_evidence": _summarize_supported(),
                "suggested_next_step": "请按示例问题提问。",
            }
        ]
    ans = normalize_answer(
        {
            "request_id": req["request_id"],
            "run_dir": run_dir,
            "question": req["question"],
            "question_type": qtype,
            "mode": mode,
            "confirmed": confirmed,
            "inferred": inferred,
            "unknown": unknown,
            "evidence_index": evidence[:30],
            "limitations": [
                "This ask endpoint is restricted to summary/risk/evidence/flow.",
                "Default mode is facts-only.",
                "No unrestricted full-repository source reading is performed.",
            ],
            "metadata": {
                "with_drilldown": bool(with_drilldown),
                "no_drilldown": bool(no_drilldown),
            },
        }
    )
    return ans
