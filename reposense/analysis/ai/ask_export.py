import json
import os

from .ask_engine import generate_ask_answer
from .ask_render import render_ask_markdown


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def export_ai_ask(run_dir, question, with_drilldown=False, no_drilldown=False):
    answer = generate_ask_answer(
        run_dir,
        question=question,
        with_drilldown=with_drilldown,
        no_drilldown=no_drilldown,
    )
    req_id = str(answer.get("request_id") or "request")
    out_dir = os.path.join(run_dir, "ai_ask", req_id)
    json_path = os.path.join(out_dir, "answer.json")
    md_path = os.path.join(out_dir, "answer.md")
    markdown = render_ask_markdown(answer)
    _write_json(json_path, answer)
    _write_text(md_path, markdown)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "answer": answer,
        "markdown": markdown,
        "json_path": json_path,
        "markdown_path": md_path,
    }
