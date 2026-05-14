def _bucket(items):
    immediate = []
    review = []
    watch = []
    for x in items or []:
        sev = str(x.get("severity") or "medium")
        st = str(x.get("status") or "suspected")
        if sev == "high" or (sev == "medium" and st == "confirmed"):
            immediate.append(x)
        elif sev == "medium":
            review.append(x)
        else:
            watch.append(x)
    return immediate, review, watch


def _render_item(x):
    lines = []
    lines.append(f"### {str(x.get('title') or '')}")
    lines.append(
        f"- severity/status/priority: {str(x.get('severity') or '')} / "
        f"{str(x.get('status') or '')} / {float(x.get('priority_score') or 0.0):.1f}"
    )
    lines.append(f"- why_it_matters: {str(x.get('why_it_matters') or '')}")
    lines.append(f"- 已证实: {len(x.get('confirmed') or [])} 条")
    lines.append(f"- 待复核: {len(x.get('suspected') or [])} 条")
    lines.append(f"- 未知: {len(x.get('unknown') or [])} 条")
    lines.append(f"- evidence_refs: {len(x.get('evidence_refs') or [])} 条")
    lines.append(f"- recommended_action: {str(x.get('recommended_action') or '')}")
    return lines


def render_risks_markdown(report):
    r = report or {}
    items = r.get("risk_items") or []
    immediate, review, watch = _bucket(items)
    s = r.get("summary") or {}
    lines = []
    lines.append("# RepoSense AI Risks")
    lines.append("")
    lines.append("## 风险概览")
    lines.append(f"- mode: {str(r.get('mode') or '')}")
    lines.append(f"- total_risks: {int(s.get('total_risks') or 0)}")
    lines.append(f"- gate_status: {str(s.get('gate_status') or 'n/a')}")
    lines.append("")
    lines.append("## Immediate attention")
    if not immediate:
        lines.append("- none")
    for x in immediate[:5]:
        lines.extend(_render_item(x))
    lines.append("")
    lines.append("## Needs review")
    if not review:
        lines.append("- none")
    for x in review[:5]:
        lines.extend(_render_item(x))
    lines.append("")
    lines.append("## Contextual watchlist")
    if not watch:
        lines.append("- none")
    for x in watch[:5]:
        lines.extend(_render_item(x))
    lines.append("")
    lines.append("## 建议优先处置顺序")
    for a in r.get("priority_actions") or []:
        lines.append(f"- {str(a.get('title') or '')}: {str(a.get('reason') or '')}")
    lines.append("")
    lines.append("## 证据索引")
    for e in (r.get("evidence_index") or [])[:20]:
        lines.append(
            "- {st} f={f} e={ev} {file}:{s}-{t}".format(
                st=str(e.get("source_type") or "-"),
                f=str(e.get("finding_id") or "-"),
                ev=str(e.get("event_id") or "-"),
                file=str(e.get("file") or "-"),
                s=int(e.get("start_line") or 0),
                t=int(e.get("end_line") or 0),
            )
        )
    lines.append("")
    lines.append("## 已知局限")
    for item in r.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
