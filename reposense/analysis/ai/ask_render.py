def render_ask_markdown(answer):
    a = answer or {}
    lines = []
    lines.append("# RepoSense AI Ask")
    lines.append("")
    lines.append("## 用户问题")
    lines.append(f"- {a.get('question')}")
    lines.append("")
    lines.append("## 问题分类")
    lines.append(f"- type: {a.get('question_type')}")
    lines.append(f"- mode: {a.get('mode')}")
    lines.append("")
    lines.append("## 已证实")
    if not (a.get("confirmed") or []):
        lines.append("- none")
    for c in a.get("confirmed") or []:
        lines.append(f"- {c.get('claim')}")
        if c.get("because"):
            lines.append(f"  - because: {c.get('because')}")
    lines.append("")
    lines.append("## 合理推测")
    if not (a.get("inferred") or []):
        lines.append("- none")
    for c in a.get("inferred") or []:
        lines.append(f"- {c.get('claim')}")
        lines.append(f"  - why_not_confirmed: {c.get('why_not_confirmed')}")
    lines.append("")
    lines.append("## 未知")
    if not (a.get("unknown") or []):
        lines.append("- none")
    for c in a.get("unknown") or []:
        lines.append(f"- {c.get('question')}")
        lines.append(f"  - suggested_next_step: {c.get('suggested_next_step')}")
    lines.append("")
    lines.append("## 证据索引")
    for e in (a.get("evidence_index") or []):
        lines.append(
            f"- {str(e.get('source_type') or '-')}: {str(e.get('file') or '-')}:"
            f"{int(e.get('start_line') or 0)}-{int(e.get('end_line') or 0)}"
        )
    if not (a.get("evidence_index") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## 已知局限")
    for x in a.get("limitations") or []:
        lines.append(f"- {x}")
    lines.append("")
    return "\n".join(lines)
