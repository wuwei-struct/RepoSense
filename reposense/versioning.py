import os
import hashlib
def normalize_text(path):
    try:
        with open(path, "rb") as f:
            raw = f.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    for ln in lines:
        s = ln.rstrip()
        if not s:
            continue
        if s.lstrip().startswith("#"):
            continue
        out.append(s)
    return "\n".join(out)
def ruleset_fingerprint(ruleset_dir):
    main = None
    for nm in ("rules.yaml", "rules.yml"):
        p = os.path.join(ruleset_dir, nm)
        if os.path.isfile(p):
            main = p
            break
    txt = ""
    if main:
        txt = normalize_text(main)
    else:
        parts = []
        for root, _, files in os.walk(ruleset_dir):
            for f in sorted(files):
                if f.endswith((".yaml",".yml",".json")):
                    parts.append(normalize_text(os.path.join(root, f)))
        txt = "\n".join(parts)
    h = hashlib.sha256()
    h.update(txt.encode("utf-8"))
    return h.hexdigest()[:16]
def generated_by(reposense_version, ruleset_id, ruleset_fp, schema_version):
    return {
        "tool": "reposense",
        "reposense_version": str(reposense_version),
        "ruleset_id": str(ruleset_id),
        "ruleset_fingerprint": str(ruleset_fp),
        "schema_version": int(schema_version),
    }
