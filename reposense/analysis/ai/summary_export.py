import json
import os
import shutil

from .summary_engine import generate_facts_only_summary
from .summary_render import render_summary_markdown


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _upsert_context_pack(run_dir, summary_json_path, summary_md_path):
    cp = os.path.join(run_dir, "context_pack")
    if not os.path.isdir(cp):
        return
    art = os.path.join(cp, "ARTIFACTS")
    os.makedirs(art, exist_ok=True)
    shutil.copyfile(summary_json_path, os.path.join(art, "ai_summary.json"))
    shutil.copyfile(summary_md_path, os.path.join(art, "ai_summary.md"))
    idx_path = os.path.join(cp, "MAP", "index.json")
    idx = _read_json(idx_path, {})
    outs = idx.get("outputs") if isinstance(idx.get("outputs"), dict) else {}
    outs["ai_summary_json"] = "ai_summary.json"
    outs["ai_summary_md"] = "ai_summary.md"
    idx["outputs"] = outs
    _write_json(idx_path, idx)
    rd_path = os.path.join(cp, "README.md")
    try:
        txt = ""
        if os.path.isfile(rd_path):
            with open(rd_path, "r", encoding="utf-8") as f:
                txt = f.read()
        marker = "## AI Summary"
        if marker in txt:
            txt = txt.split(marker)[0].rstrip() + "\n\n"
        sm = _read_json(summary_json_path, {})
        risk = sm.get("risk_summary") or {}
        lines = [
            marker,
            f"- total patterns: {int(risk.get('total_patterns') or 0)}",
            f"- gate status: {str((sm.get('project_overview') or {}).get('gate_status') or 'n/a')}",
            "- file: ARTIFACTS/ai_summary.md",
        ]
        _write_text(rd_path, (txt + "\n".join(lines) + "\n").strip() + "\n")
    except Exception:
        pass


def export_ai_summary(
    run_dir,
    out_dir=None,
    write_json_file=False,
    write_markdown_file=False,
):
    summary = generate_facts_only_summary(run_dir)
    markdown = render_summary_markdown(summary)
    target = os.path.abspath(out_dir or run_dir)
    json_path = os.path.join(target, "ai_summary.json")
    md_path = os.path.join(target, "ai_summary.md")
    if write_json_file:
        _write_json(json_path, summary)
    if write_markdown_file:
        _write_text(md_path, markdown)
    if os.path.abspath(target) == os.path.abspath(run_dir) and (write_json_file or write_markdown_file):
        if write_json_file and write_markdown_file:
            _upsert_context_pack(run_dir, json_path, md_path)
        try:
            from ...run_manifest import build_run_manifest

            build_run_manifest(run_dir, write=True)
        except Exception:
            pass
        try:
            from ...context_pack import zip_context_pack

            if os.path.isdir(os.path.join(run_dir, "context_pack")):
                zip_context_pack(run_dir)
        except Exception:
            pass
    return {
        "summary": summary,
        "markdown": markdown,
        "json_path": json_path,
        "markdown_path": md_path,
    }

