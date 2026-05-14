import json
import os

from .risks_engine import generate_risks_report
from .risks_render import render_risks_markdown


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def export_ai_risks(
    run_dir,
    with_drilldown=False,
    no_drilldown=False,
    max_auto_drilldowns=5,
    severity_threshold="medium",
):
    report = generate_risks_report(
        run_dir,
        with_drilldown=with_drilldown,
        no_drilldown=no_drilldown,
        max_auto_drilldowns=max_auto_drilldowns,
        severity_threshold=severity_threshold,
    )
    out_dir = os.path.join(run_dir, "ai_risks")
    json_path = os.path.join(out_dir, "risks.json")
    md_path = os.path.join(out_dir, "risks.md")
    markdown = render_risks_markdown(report)
    _write_json(json_path, report)
    _write_text(md_path, markdown)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "report": report,
        "markdown": markdown,
        "json_path": json_path,
        "markdown_path": md_path,
    }
