def render_code_health_markdown(findings, summary):
    lines = [
        "# Code Health Radar",
        "",
        f"- Total findings: {int(summary.get('total_findings') or 0)}",
        f"- Health score: {int((summary.get('health_score') or {}).get('score') or 0)} (experimental)",
        "",
        "## Findings",
    ]
    for f in findings[:50]:
        lines.append(f"- [{f.get('severity')}] {f.get('rule_id')} {f.get('file')}:{f.get('line_start')} - {f.get('title')}")
    lines += ["", "## Limitations"]
    for item in summary.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)

