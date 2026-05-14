import os, sys, shutil, hashlib, json, re, time, subprocess
def read_lines(p):
    with open(p, "r", encoding="utf-8") as f:
        return [x.strip() for x in f.read().splitlines() if x.strip()]
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(8192)
            if not b: break
            h.update(b)
    return h.hexdigest()
def copy_allowlist(src, dst, allow):
    for pat in allow:
        ap = os.path.join(src, pat.replace("/", os.sep))
        if os.path.isdir(ap):
            for root, dirs, files in os.walk(ap):
                for nm in files:
                    rel = os.path.relpath(os.path.join(root, nm), src)
                    outp = os.path.join(dst, rel)
                    os.makedirs(os.path.dirname(outp), exist_ok=True)
                    shutil.copy2(os.path.join(root, nm), outp)
        elif os.path.isfile(ap):
            rel = os.path.relpath(ap, src)
            outp = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(outp), exist_ok=True)
            shutil.copy2(ap, outp)
def run_denylist_scan(dst, path_entries, pattern_entries):
    import fnmatch
    glob_paths = [p for p in path_entries if ("*" in p or "?" in p)]
    dir_paths = [p for p in path_entries if not ("*" in p or "?" in p)]
    for pat in dir_paths:
        dp = os.path.join(dst, pat.replace("/", os.sep))
        if os.path.exists(dp):
            raise SystemExit(f"denylist path hit: {pat}")
    regs = [re.compile(p) for p in pattern_entries if p]
    for root, _, files in os.walk(dst):
        for nm in files:
            rp = os.path.relpath(os.path.join(root, nm), dst).replace("\\","/")
            for gp in glob_paths:
                if fnmatch.fnmatch(rp, gp):
                    raise SystemExit(f"denylist glob hit: {gp} at {rp}")
            p = os.path.join(root, nm)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read()
                for rg in regs:
                    if rg.search(data):
                        raise SystemExit(f"denylist content hit: {rg.pattern} in {rp}")
            except Exception:
                continue
def write_manifest(dst):
    m = {"generated_at": int(time.time()), "files": []}
    for root, _, files in os.walk(dst):
        for nm in files:
            p = os.path.join(root, nm)
            rel = os.path.relpath(p, dst).replace("\\","/")
            m["files"].append({"path": rel, "sha256": sha256_file(p)})
    with open(os.path.join(dst, "OSS_SNAPSHOT_MANIFEST.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(m))
def main():
    src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out = os.path.abspath(sys.argv[sys.argv.index("--out")+1]) if "--out" in sys.argv else os.path.join(src, "dist", "oss_snapshot")
    os.makedirs(out, exist_ok=True)
    allow = read_lines(os.path.join(os.path.dirname(__file__), "allowlist.txt"))
    deny = read_lines(os.path.join(os.path.dirname(__file__), "denylist.txt"))
    copy_allowlist(src, out, allow)
    path_entries = [d for d in deny if d.endswith("/") or d.endswith("\\") or ("*" in d) or ("?" in d)]
    pattern_entries = [d for d in deny if d not in path_entries]
    run_denylist_scan(out, path_entries, pattern_entries)
    write_manifest(out)
    smoke = "--smoke" in sys.argv
    smoke_cmd = None
    if "--smoke-cmd" in sys.argv:
        try:
            smoke_cmd = sys.argv[sys.argv.index("--smoke-cmd")+1]
        except Exception:
            smoke_cmd = None
    if smoke:
        try:
            if not smoke_cmd:
                subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=out, check=True)
                smoke_cmd = "bash scripts/demo_run.sh" if os.name != "nt" else "powershell -ExecutionPolicy Bypass -File scripts\\demo_run.ps1"
            res = subprocess.run(smoke_cmd, cwd=out, shell=True)
            if res.returncode != 0:
                print(json.dumps({"out": out, "smoke_failed": True, "returncode": res.returncode}))
                sys.exit(res.returncode)
            # artifact existence check
            def _find_run_dirs(root):
                base = os.path.join(root, "_demo_out")
                runs = []
                if os.path.isdir(base):
                    for d in os.listdir(base):
                        p = os.path.join(base, d)
                        if os.path.isdir(p) and d.startswith("run-"):
                            runs.append(p)
                return sorted(runs)
            runs = _find_run_dirs(out)
            if not runs:
                print(json.dumps({"out": out, "smoke_failed": True, "error": "no_run_dirs"}))
                sys.exit(2)
            rd = runs[-1]
            reqs = [
                os.path.join(rd, "report.html"),
                os.path.join(rd, "learn", "index.html"),
                os.path.join(rd, "exports", "report.sarif.json"),
                os.path.join(rd, "exports", "context_pack.zip"),
                os.path.join(rd, "quality_gate.json"),
                os.path.join(rd, "baseline_diff.md"),
            ]
            missing = [p for p in reqs if not os.path.isfile(p)]
            if missing:
                print(json.dumps({"out": out, "smoke_failed": True, "missing": [os.path.relpath(m, out) for m in missing]}))
                sys.exit(2)
        except subprocess.CalledProcessError as e:
            try:
                print(json.dumps({"out": out, "smoke_failed": True, "returncode": e.returncode}))
            except Exception:
                pass
            sys.exit(2)
    print(json.dumps({"out": out, "files": len(os.listdir(out)), "smoke": smoke}))
if __name__ == "__main__":
    main()
