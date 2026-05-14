def _line_list(rows, prefix="- "):
    return "\n".join([f"{prefix}{x}" for x in rows]) if rows else f"{prefix}none"


def render_summary_markdown(summary):
    s = summary or {}
    ov = s.get("project_overview") or {}
    st = s.get("stack_summary") or {}
    su = s.get("surface_summary") or {}
    fl = s.get("flow_summary") or {}
    rs = s.get("risk_summary") or {}
    acts = s.get("priority_actions") or []
    lines = []
    lines.append("# RepoSense AI Summary")
    lines.append("")
    lines.append("## 1. 项目概览")
    lines.append(f"- mode: {s.get('mode')}")
    lines.append(f"- gate status: {ov.get('gate_status')}")
    lines.append(
        f"- scanned files/findings/events/edges: {ov.get('scanned_files',0)}/{ov.get('findings',0)}/{ov.get('events',0)}/{ov.get('graph_edges',0)}"
    )
    lines.append(f"- languages: {', '.join(ov.get('languages') or []) or 'none'}")
    lines.append(f"- frameworks: {', '.join(ov.get('frameworks') or []) or 'none'}")
    lines.append("")
    lines.append("## 2. 技术栈与语言分布")
    lines.append(f"- languages: {', '.join(st.get('languages') or []) or 'none'}")
    lines.append(f"- frameworks: {', '.join(st.get('frameworks') or []) or 'none'}")
    lines.append(f"- queue hints: {', '.join(st.get('queue_hints') or []) or 'none'}")
    lines.append(f"- cache hints: {', '.join(st.get('cache_hints') or []) or 'none'}")
    lines.append(f"- db hints: {', '.join(st.get('db_hints') or []) or 'none'}")
    lines.append(f"- openapi present: {bool(st.get('openapi_present'))}")
    lines.append(f"- cross-language present: {bool(st.get('cross_language_present'))}")
    lines.append("")
    lines.append("## 3. 核心结构摘要")
    lines.append(
        f"- API count / write-like API count: {su.get('api_count',0)} / {su.get('write_like_api_count',0)}"
    )
    lines.append(
        f"- Queue dispatch/consume: {su.get('queue_dispatch_count',0)} / {su.get('queue_consume_count',0)}"
    )
    lines.append(
        f"- Cache read/write/invalidate: {su.get('cache_read_count',0)} / {su.get('cache_write_count',0)} / {su.get('cache_invalidate_count',0)}"
    )
    lines.append(
        f"- DB read/write/tx: {su.get('db_read_count',0)} / {su.get('db_write_count',0)} / {su.get('db_tx_count',0)}"
    )
    cl = fl.get("cross_language") or {}
    lines.append(
        f"- Cross-language matched/unmatched callers/unmatched endpoints: {cl.get('matched_links',0)} / {cl.get('unmatched_callers',0)} / {cl.get('unmatched_endpoints',0)}"
    )
    lines.append("")
    lines.append("## 4. 核心事件流摘要")
    fam_rows = [f"{x.get('family')}:{x.get('count')}" for x in (fl.get("top_event_families") or [])]
    lines.append("- Top event families:")
    lines.append(_line_list(fam_rows))
    path_rows = [f"{x.get('path')} ({','.join(x.get('event_kinds') or [])})" for x in (fl.get("representative_paths") or [])]
    lines.append("- Representative paths:")
    lines.append(_line_list(path_rows))
    lines.append("")
    lines.append("## 5. 风险模式摘要")
    lines.append(f"- total patterns: {rs.get('total_patterns',0)}")
    cbs = rs.get("counts_by_severity") or {}
    cbt = rs.get("counts_by_type") or {}
    lines.append(f"- counts by severity: {', '.join([f'{k}:{v}' for k,v in sorted(cbs.items())]) or 'none'}")
    lines.append(f"- top pattern types: {', '.join([f'{k}:{v}' for k,v in sorted(cbt.items())]) or 'none'}")
    lines.append("- confirmed top:")
    lines.append(_line_list([f"{x.get('pattern_type')} [{x.get('severity')}]" for x in (rs.get("confirmed_top") or [])]))
    lines.append("- suspected top:")
    lines.append(_line_list([f"{x.get('pattern_type')} [{x.get('severity')}]" for x in (rs.get("suspected_top") or [])]))
    lines.append("")
    lines.append("## 6. 建议优先关注点")
    if acts:
        for a in acts:
            lines.append(f"- {a.get('title')}: {a.get('reason')}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## 已知局限")
    lines.append("- 本摘要为 facts-only（仅基于 run artifacts + patterns）。")
    lines.append("- 未进行源码下钻。")
    lines.append("- suspected 项可能需要二次复核。")
    lines.append("")
    return "\n".join(lines)

