import json
import os

from .explain_engine import generate_explain_result
from .explain_render import render_explain_markdown


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def export_ai_explain(run_dir, target_type, target_id, with_drilldown=False, no_drilldown=False):
    result = generate_explain_result(
        run_dir,
        target_type=target_type,
        target_id=target_id,
        with_drilldown=with_drilldown,
        no_drilldown=no_drilldown,
    )
    req_id = str(result.get("request_id") or "request")
    out_dir = os.path.join(run_dir, "ai_explain", req_id)
    json_path = os.path.join(out_dir, "explain.json")
    md_path = os.path.join(out_dir, "explain.md")
    markdown = render_explain_markdown(result)
    _write_json(json_path, result)
    _write_text(md_path, markdown)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "request_id": req_id,
        "result": result,
        "markdown": markdown,
        "json_path": json_path,
        "markdown_path": md_path,
    }
