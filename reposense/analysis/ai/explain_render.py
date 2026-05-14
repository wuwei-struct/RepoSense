def _format_refs(refs):
    rows = []
    for r in refs or []:
        rows.append(
            "{st} f={f} e={e} {file}:{s}-{t}".format(
                st=str(r.get("source_type") or "-"),
                f=str(r.get("finding_id") or "-"),
                e=str(r.get("event_id") or "-"),
                file=str(r.get("file") or "-"),
                s=int(r.get("start_line") or 0),
                t=int(r.get("end_line") or 0),
            )
        )
    return rows


def render_explain_markdown(result):
    r = result or {}
    lines = []
    lines.append("# RepoSense AI Explain")
    lines.append("")
    lines.append("## 请求目标")
    lines.append(f"- target_type: {r.get('target_type')}")
    lines.append(f"- target_id: {r.get('target_id')}")
    lines.append(f"- mode: {r.get('mode')}")
    lines.append("")
    lines.append("## 已证实")
    confirmed = r.get("confirmed") or []
    if not confirmed:
        lines.append("- none")
    for c in confirmed:
        lines.append(f"- claim: {c.get('claim')}")
        lines.append(f"  - because: {c.get('because')}")
        lines.append(f"  - confidence: {c.get('confidence')}")
        eref = _format_refs(c.get("evidence_refs") or [])
        lines.append(f"  - evidence_refs: {', '.join(eref) if eref else 'none'}")
    lines.append("")
    lines.append("## 合理推测")
    inferred = r.get("inferred") or []
    if not inferred:
        lines.append("- none")
    for c in inferred:
        lines.append(f"- claim: {c.get('claim')}")
        lines.append(f"  - signals: {', '.join(c.get('signals') or []) or 'none'}")
        lines.append(f"  - why_not_confirmed: {c.get('why_not_confirmed')}")
    lines.append("")
    lines.append("## 未知")
    unknown = r.get("unknown") or []
    if not unknown:
        lines.append("- none")
    for c in unknown:
        lines.append(f"- question: {c.get('question')}")
        lines.append(f"  - missing_evidence: {', '.join(c.get('missing_evidence') or []) or 'none'}")
        lines.append(f"  - suggested_next_step: {c.get('suggested_next_step')}")
    lines.append("")
    lines.append("## 证据索引")
    eref = _format_refs(r.get("evidence_index") or [])
    if not eref:
        lines.append("- none")
    else:
        for x in eref:
            lines.append(f"- {x}")
    lines.append("")
    lines.append("## 已知局限")
    for item in r.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
