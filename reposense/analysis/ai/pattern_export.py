import json
import os
import shutil

from .pattern_engine import generate_patterns


def _read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def _upsert_context_pack(run_dir, patterns_path, summary_path):
    cp = os.path.join(run_dir, "context_pack")
    if not os.path.isdir(cp):
        return
    art = os.path.join(cp, "ARTIFACTS")
    os.makedirs(art, exist_ok=True)
    shutil.copyfile(patterns_path, os.path.join(art, "patterns.json"))
    shutil.copyfile(summary_path, os.path.join(art, "pattern_summary.json"))
    idx_path = os.path.join(cp, "MAP", "index.json")
    idx = _read_json(idx_path, {})
    outs = idx.get("outputs") if isinstance(idx.get("outputs"), dict) else {}
    outs["patterns"] = "patterns.json"
    outs["pattern_summary"] = "pattern_summary.json"
    idx["outputs"] = outs
    _write_json(idx_path, idx)
    rd_path = os.path.join(cp, "README.md")
    try:
        txt = ""
        if os.path.isfile(rd_path):
            with open(rd_path, "r", encoding="utf-8") as f:
                txt = f.read()
        marker = "## Patterns Summary"
        if marker in txt:
            txt = txt.split(marker)[0].rstrip() + "\n\n"
        sm = _read_json(summary_path, {})
        rows = [
            marker,
            f"- total patterns: {int(sm.get('total_patterns') or 0)}",
            f"- top pattern types: {', '.join([f'{k}:{v}' for k, v in (sm.get('counts_by_type') or {}).items()]) or 'none'}",
            f"- counts by severity: {', '.join([f'{k}:{v}' for k, v in (sm.get('counts_by_severity') or {}).items()]) or 'none'}",
        ]
        with open(rd_path, "w", encoding="utf-8") as f:
            f.write((txt + "\n".join(rows) + "\n").strip() + "\n")
    except Exception:
        pass


def export_patterns(run_dir, out_dir=None):
    pats, summary = generate_patterns(run_dir)
    target = os.path.abspath(out_dir or run_dir)
    os.makedirs(target, exist_ok=True)
    patterns_path = os.path.join(target, "patterns.json")
    summary_path = os.path.join(target, "pattern_summary.json")
    _write_json(patterns_path, {"patterns": pats})
    _write_json(summary_path, summary)
    if os.path.abspath(target) == os.path.abspath(run_dir):
        _upsert_context_pack(run_dir, patterns_path, summary_path)
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
    return {"patterns_path": patterns_path, "summary_path": summary_path, "summary": summary}
