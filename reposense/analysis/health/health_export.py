import json
import os

from .health_render import render_code_health_markdown
from .health_scanner import scan_code_health
from .health_summary import LIMITATIONS, maintainability_risks_from_findings, summarize_code_health


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _repo_from_run(run_dir):
    for rel in ["run_manifest.json", "coverage.json", "report.json"]:
        obj = _read_json(os.path.join(run_dir, rel), {})
        candidates = [
            obj.get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("meta") or {}).get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("run_summary") or {}).get("repo_path") if isinstance(obj, dict) else None,
            (obj.get("stats") or {}).get("repo_path") if isinstance(obj, dict) else None,
        ]
        for c in candidates:
            if c and os.path.isdir(str(c)):
                return str(c)
    return None


def export_code_health(run_dir, repo_path=None, write_markdown=False, thresholds=None):
    repo = repo_path or _repo_from_run(run_dir)
    if not repo:
        raise ValueError("repo_path is required when run artifacts do not record a readable repository path")
    if not os.path.isdir(repo):
        raise ValueError("repo_path must be an existing directory")
    findings = scan_code_health(run_dir, repo, thresholds=thresholds)
    summary = summarize_code_health(findings)
    risks = maintainability_risks_from_findings(findings)
    payload = {
        "version": "code_health_v1",
        "generated_from": run_dir,
        "repo_path": os.path.abspath(repo),
        "findings": findings,
        "limitations": LIMITATIONS[:],
    }
    paths = {
        "code_health_path": os.path.join(run_dir, "code_health.json"),
        "summary_path": os.path.join(run_dir, "code_health_summary.json"),
        "risks_path": os.path.join(run_dir, "maintainability_risks.json"),
    }
    _write_json(paths["code_health_path"], payload)
    _write_json(paths["summary_path"], summary)
    _write_json(paths["risks_path"], risks)
    markdown = ""
    if write_markdown:
        markdown = render_code_health_markdown(findings, summary)
        paths["markdown_path"] = os.path.join(run_dir, "code_health.md")
        _write_text(paths["markdown_path"], markdown)
    try:
        from ...run_manifest import build_run_manifest

        build_run_manifest(run_dir, write=True)
    except Exception:
        pass
    return {
        "code_health": payload,
        "summary": summary,
        "maintainability_risks": risks,
        "markdown": markdown,
        **paths,
    }

