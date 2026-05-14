import json
import os

from .source_drilldown import generate_snippet_pack


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def render_snippet_pack_markdown(pack):
    p = pack or {}
    b = p.get("budget") or {}
    lines = []
    lines.append("# RepoSense AI Drill-down")
    lines.append("")
    lines.append("## 1. Request Target")
    lines.append(f"- target_type: {p.get('target_type')}")
    lines.append(f"- target_id: {p.get('target_id')}")
    lines.append(f"- source_mode: {p.get('source_mode')}")
    lines.append(
        "- budget: "
        f"max_files={b.get('max_files')} "
        f"max_snippets={b.get('max_snippets')} "
        f"max_lines_per_snippet={b.get('max_lines_per_snippet')} "
        f"context_lines={b.get('context_lines')} "
        f"max_total_chars={b.get('max_total_chars')} "
        f"total_chars={b.get('total_chars')}"
    )
    lines.append("")
    lines.append("## 2. Selection Summary")
    lines.append(f"- selected files: {len(p.get('selected_files') or [])}")
    lines.append(f"- selected snippets: {len(p.get('selected_snippets') or [])}")
    lines.append("- strategy: evidence-first with local window expansion and merge")
    lines.append("")
    lines.append("## 3. Snippet List")
    for s in p.get("selected_snippets") or []:
        lines.append(f"### {s.get('file')}:{s.get('line_start')}-{s.get('line_end')}")
        lines.append(f"- why_selected: {s.get('why_selected')}")
        src = s.get("source_refs") or []
        refs = []
        for r in src:
            refs.append(
                "pattern={p} finding={f} event={e} source={st}".format(
                    p=r.get("pattern_id") or "-",
                    f=r.get("finding_id") or "-",
                    e=r.get("event_id") or "-",
                    st=(r.get("evidence_ref") or {}).get("source_type") or "-",
                )
            )
        lines.append(f"- source_refs: {', '.join(refs) if refs else 'none'}")
        lines.append("")
        lines.append("```text")
        lines.append(str(s.get("snippet") or ""))
        lines.append("```")
        lines.append("")
    lines.append("## 4. Known Limitations")
    for item in p.get("limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def export_drilldown(run_dir, target_type, target_id, budget=None):
    pack = generate_snippet_pack(run_dir, target_type, target_id, budget=budget)
    out_dir = os.path.join(run_dir, "ai_drilldown", str(pack.get("request_id") or "request"))
    json_path = os.path.join(out_dir, "snippet_pack.json")
    md_path = os.path.join(out_dir, "snippet_pack.md")
    markdown = render_snippet_pack_markdown(pack)
    _write_json(json_path, pack)
    _write_text(md_path, markdown)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "request_id": pack.get("request_id"),
        "pack": pack,
        "markdown": markdown,
        "json_path": json_path,
        "markdown_path": md_path,
    }
