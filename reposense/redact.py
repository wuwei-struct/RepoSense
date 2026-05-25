import os
import re
import json
import zipfile
def _home_patterns():
    return [re.compile(r"[A-Za-z]:\\Users\\[^\\]+", re.IGNORECASE), re.compile(r"/home/[^/]+", re.IGNORECASE)]
def _drive_pattern():
    return re.compile(r"[A-Za-z]:\\[^\\\n]+", re.IGNORECASE)
def _tmp_abs_pattern():
    # CI/Linux temp roots such as /tmp/repo_ctx_xxx or /var/tmp/...
    return re.compile(r"/(?:tmp|var/tmp)/[^\s\"'<>]+", re.IGNORECASE)
def build_ctx(run_dir, repo_root):
    plat = "win" if os.name == "nt" else "posix"
    return {"repo_root_abs": os.path.abspath(repo_root), "repo_root_token": "<REPO_ROOT>", "home_tokens": {"home": "<HOME>", "abs": "<ABS_PATH>"}, "platform": plat, "run_dir": os.path.abspath(run_dir)}
def redact_text(text, ctx):
    counts = {"repo_root": 0, "home": 0, "abs": 0}
    rr = re.escape(ctx["repo_root_abs"]).replace("\\/", "/")
    text = re.sub(rr + r"([^\s]*)", lambda m: (counts.__setitem__("repo_root", counts["repo_root"]+1)) or (ctx["repo_root_token"] + (m.group(1) or "")), text)
    for hp in _home_patterns():
        text = hp.sub(lambda m: (counts.__setitem__("home", counts["home"]+1)) or (ctx["home_tokens"]["home"]), text)
    text = _drive_pattern().sub(lambda m: (counts.__setitem__("abs", counts["abs"]+1)) or (ctx["home_tokens"]["abs"]), text)
    text = _tmp_abs_pattern().sub(lambda m: (counts.__setitem__("abs", counts["abs"]+1)) or (ctx["home_tokens"]["abs"]), text)
    return text, counts
def _redact_json_obj(obj, ctx, acc):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str):
                nv, c = redact_text(v, ctx)
                out[k] = nv
                for kk in c:
                    acc[kk] = acc.get(kk, 0) + c[kk]
            else:
                out[k] = _redact_json_obj(v, ctx, acc)
        return out
    if isinstance(obj, list):
        return [_redact_json_obj(x, ctx, acc) for x in obj]
    return obj
def redact_json(obj, ctx):
    acc = {"repo_root": 0, "home": 0, "abs": 0}
    out = _redact_json_obj(obj, ctx, acc)
    return out, acc
def scrub_file(path, kind, ctx):
    try:
        if kind == "json":
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            red, c = redact_json(obj, ctx)
            with open(path, "w", encoding="utf-8") as f2:
                json.dump(red, f2, ensure_ascii=False)
            return c
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            red, c = redact_text(txt, ctx)
            with open(path, "w", encoding="utf-8") as f2:
                f2.write(red)
            return c
    except Exception:
        return {"repo_root": 0, "home": 0, "abs": 0}
def scrub_context_pack_zip(zip_path, ctx):
    try:
        tmp = zip_path + ".tmp"
        with zipfile.ZipFile(zip_path, "r") as zin, zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                kind = "text"
                if info.filename.endswith(".json"):
                    try:
                        obj = json.loads(data.decode("utf-8"))
                        red, _ = redact_json(obj, ctx)
                        data = json.dumps(red, ensure_ascii=False).encode("utf-8")
                        kind = "json"
                    except Exception:
                        red, _ = redact_text(data.decode("utf-8", errors="ignore"), ctx)
                        data = red.encode("utf-8")
                else:
                    red, _ = redact_text(data.decode("utf-8", errors="ignore"), ctx)
                    data = red.encode("utf-8")
                zout.writestr(info, data)
        try:
            os.replace(tmp, zip_path)
        except Exception:
            pass
    except Exception:
        pass
def scrub_outputs(run_dir, repo_root, enabled=True):
    rep = {"enabled": bool(enabled), "counts": {"repo_root": 0, "home": 0, "abs": 0}, "files": []}
    if not enabled:
        with open(os.path.join(run_dir, "redaction_report.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False)
        return 0
    ctx = build_ctx(run_dir, repo_root)
    targets = [
        ("report.html", "text"),
        ("ci_summary.json", "json"),
        (os.path.join("meta","config.json"), "json"),
        ("quality_gate.json", "json"),
        ("baseline_diff.json", "json"),
        ("baseline_diff.md", "text"),
        ("run_manifest.json", "json"),
        (os.path.join("exports","report.sarif.json"), "json"),
    ]
    for rel, kind in targets:
        p = os.path.join(run_dir, rel)
        if os.path.isfile(p):
            c = scrub_file(p, kind, ctx)
            rep["files"].append({"path": rel, "counts": c})
            for kk in c:
                rep["counts"][kk] = rep["counts"].get(kk, 0) + c[kk]
    learn_dir = os.path.join(run_dir, "learn")
    if os.path.isdir(learn_dir):
        for root, _, fs in os.walk(learn_dir):
            for nm in fs:
                p = os.path.join(root, nm)
                kind = "json" if nm.endswith(".json") else "text"
                c = scrub_file(p, kind, ctx)
                rep["files"].append({"path": os.path.relpath(p, run_dir).replace("\\","/"), "counts": c})
                for kk in c:
                    rep["counts"][kk] = rep["counts"].get(kk, 0) + c[kk]
    zip_p = os.path.join(run_dir, "exports", "context_pack.zip")
    if os.path.isfile(zip_p):
        scrub_context_pack_zip(zip_p, ctx)
        rep["files"].append({"path": "exports/context_pack.zip", "counts": {}})
    with open(os.path.join(run_dir, "redaction_report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False)
    return 0
