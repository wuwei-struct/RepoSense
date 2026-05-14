import os
import re
import json
import hashlib
from .utils import write_json


def _sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _mk_id(kind, path, cmd):
    return _sha("|".join([kind or "", path or "", cmd or ""]))


def _detect_package_json(repo_root):
    p = os.path.join(repo_root, "package.json")
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return []
    res = []
    scripts = obj.get("scripts") or {}
    for name, cmd in scripts.items():
        k = "cli"
        if name.lower() == "test":
            k = "tests"
        title = f"npm run {name}"
        cmdline = f"npm run {name}"
        res.append({
            "id": _mk_id(k, p, cmdline),
            "kind": k,
            "language": "node",
            "title": title,
            "command": cmdline,
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.8,
            "evidence_ref": None,
        })
    main = obj.get("main")
    if isinstance(main, str) and main:
        title = f"node {main}"
        cmdline = f"node {main}"
        res.append({
            "id": _mk_id("cli", p, cmdline),
            "kind": "cli",
            "language": "node",
            "title": title,
            "command": cmdline,
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.7,
            "evidence_ref": None,
        })
    binf = obj.get("bin")
    if isinstance(binf, str) and binf:
        title = f"npx {binf}"
        cmdline = f"npx {binf}"
        res.append({
            "id": _mk_id("cli", p, cmdline),
            "kind": "cli",
            "language": "node",
            "title": title,
            "command": cmdline,
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.7,
            "evidence_ref": None,
        })
    if isinstance(binf, dict) and binf:
        for name, pathv in binf.items():
            title = f"npx {name}"
            cmdline = f"npx {name}"
            res.append({
                "id": _mk_id("cli", p, cmdline),
                "kind": "cli",
                "language": "node",
                "title": title,
                "command": cmdline,
                "source": {"path": p, "start_line": None, "end_line": None},
                "confidence": 0.7,
                "evidence_ref": None,
            })
    return res


def _detect_manage_py(repo_root):
    p = os.path.join(repo_root, "manage.py")
    if not os.path.isfile(p):
        return []
    return [
        {
            "id": _mk_id("web", p, "python manage.py runserver"),
            "kind": "web",
            "language": "python",
            "title": "Django runserver",
            "command": "python manage.py runserver",
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.85,
            "evidence_ref": None,
        },
        {
            "id": _mk_id("migration", p, "python manage.py migrate"),
            "kind": "migration",
            "language": "python",
            "title": "Django migrate",
            "command": "python manage.py migrate",
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.75,
            "evidence_ref": None,
        },
    ]


def _detect_console_scripts(repo_root):
    out = []
    pyproject = os.path.join(repo_root, "pyproject.toml")
    setup_cfg = os.path.join(repo_root, "setup.cfg")
    setup_py = os.path.join(repo_root, "setup.py")
    if os.path.isfile(pyproject):
        try:
            with open(pyproject, "r", encoding="utf-8") as f:
                txt = f.read()
            for m in re.finditer(r"^\s*\[project\.scripts\]\s*$", txt, re.MULTILINE):
                rest = txt[m.end():]
                for mm in re.finditer(r"^\s*([\w\-\._]+)\s*=\s*['\"][^'\"]+['\"]\s*$", rest, re.MULTILINE):
                    name = mm.group(1)
                    cmdline = f"{name}"
                    out.append({
                        "id": _mk_id("cli", pyproject, cmdline),
                        "kind": "cli",
                        "language": "python",
                        "title": f"console script {name}",
                        "command": cmdline,
                        "source": {"path": pyproject, "start_line": None, "end_line": None},
                        "confidence": 0.7,
                        "evidence_ref": None,
                    })
        except Exception:
            pass
    if os.path.isfile(setup_cfg):
        try:
            with open(setup_cfg, "r", encoding="utf-8") as f:
                txt = f.read()
            sec = re.search(r"^\s*\[options\.entry_points\]\s*$", txt, re.MULTILINE)
            if sec:
                rest = txt[sec.end():]
                cs = re.search(r"^\s*console_scripts\s*=\s*$", rest, re.MULTILINE)
                if cs:
                    after = rest[cs.end():]
                    for mm in re.finditer(r"^\s*[\-\s]*\s*([\w\-\._]+)\s*=\s*[^=\n]+$", after, re.MULTILINE):
                        name = mm.group(1)
                        cmdline = f"{name}"
                        out.append({
                            "id": _mk_id("cli", setup_cfg, cmdline),
                            "kind": "cli",
                            "language": "python",
                            "title": f"console script {name}",
                            "command": cmdline,
                            "source": {"path": setup_cfg, "start_line": None, "end_line": None},
                            "confidence": 0.7,
                            "evidence_ref": None,
                        })
        except Exception:
            pass
    if os.path.isfile(setup_py):
        try:
            with open(setup_py, "r", encoding="utf-8") as f:
                txt = f.read()
            for mm in re.finditer(r"console_scripts\s*=\s*\[([^\]]+)\]", txt, re.MULTILINE | re.DOTALL):
                body = mm.group(1)
                for m2 in re.finditer(r"['\"]([\w\-\._]+)=['\"][^'\"]+['\"]", body):
                    name = m2.group(1)
                    cmdline = f"{name}"
                    out.append({
                        "id": _mk_id("cli", setup_py, cmdline),
                        "kind": "cli",
                        "language": "python",
                        "title": f"console script {name}",
                        "command": cmdline,
                        "source": {"path": setup_py, "start_line": None, "end_line": None},
                        "confidence": 0.7,
                        "evidence_ref": None,
                    })
        except Exception:
            pass
    return out


def _detect_compose(repo_root):
    paths = []
    for nm in ["docker-compose.yml", "compose.yaml", "docker-compose.yaml"]:
        p = os.path.join(repo_root, nm)
        if os.path.isfile(p):
            paths.append(p)
    out = []
    for p in paths:
        title = "Compose up"
        try:
            with open(p, "r", encoding="utf-8") as f:
                txt = f.read()
            svcs = []
            ms = re.search(r"^\s*services\s*:\s*$", txt, re.MULTILINE)
            if ms:
                after = txt[ms.end():]
                for m in re.finditer(r"^\s{2,}([a-zA-Z0-9\-_]+)\s*:\s*$", after, re.MULTILINE):
                    svcs.append(m.group(1))
            if svcs:
                title = f"Compose up ({', '.join(svcs[:3])}{'...' if len(svcs)>3 else ''})"
        except Exception:
            pass
        out.append({
            "id": _mk_id("docker", p, "docker compose up"),
            "kind": "docker",
            "language": "shell",
            "title": title,
            "command": "docker compose up",
            "source": {"path": p, "start_line": None, "end_line": None},
            "confidence": 0.8,
            "evidence_ref": None,
        })
    return out


def _detect_ci(repo_root):
    base = os.path.join(repo_root, ".github", "workflows")
    if not os.path.isdir(base):
        return []
    out = []
    for nm in os.listdir(base):
        if nm.endswith(".yml") or nm.endswith(".yaml"):
            p = os.path.join(base, nm)
            title = os.path.splitext(nm)[0]
            try:
                with open(p, "r", encoding="utf-8") as f:
                    txt = f.read()
                m = re.search(r"^\s*name\s*:\s*(.+)$", txt, re.MULTILINE)
                if m:
                    title = m.group(1).strip()
            except Exception:
                pass
            out.append({
                "id": _mk_id("ci", p, "see workflow file"),
                "kind": "ci",
                "language": "unknown",
                "title": title,
                "command": "see workflow file",
                "source": {"path": p, "start_line": None, "end_line": None},
                "confidence": 0.6,
                "evidence_ref": None,
            })
    return out


def _detect_readme(repo_root):
    p = os.path.join(repo_root, "README.md")
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except Exception:
        return []
    out = []
    patterns = [
        ("cli", "npm run start", "node", "npm run start"),
        ("docker", "docker compose up", "shell", "docker compose up"),
        ("cli", "python -m", "python", "python -m ..."),
    ]
    for kind, needle, lang, cmdline in patterns:
        if any(needle in ln for ln in lines):
            out.append({
                "id": _mk_id(kind, p, cmdline),
                "kind": kind,
                "language": lang,
                "title": f"{needle} (README)",
                "command": cmdline,
                "source": {"path": p, "start_line": None, "end_line": None},
                "confidence": 0.4,
                "evidence_ref": None,
            })
    return out


def build_entrypoints(repo_root, run_dir):
    eps = []
    eps.extend(_detect_package_json(repo_root))
    eps.extend(_detect_manage_py(repo_root))
    eps.extend(_detect_console_scripts(repo_root))
    eps.extend(_detect_compose(repo_root))
    eps.extend(_detect_ci(repo_root))
    eps.extend(_detect_readme(repo_root))
    eps_sorted = sorted(eps, key=lambda x: (-float(x.get("confidence") or 0.0), x.get("kind") or "", x.get("title") or "", (x.get("source") or {}).get("path") or ""))
    stats = {
        "by_kind": {},
        "total": len(eps_sorted),
        "confidence_breakdown": {"high": len([e for e in eps_sorted if (e.get("confidence") or 0) >= 0.8]), "mid": len([e for e in eps_sorted if 0.5 <= (e.get("confidence") or 0) < 0.8]), "low": len([e for e in eps_sorted if (e.get("confidence") or 0) < 0.5])},
    }
    for e in eps_sorted:
        k = e.get("kind") or ""
        stats["by_kind"][k] = stats["by_kind"].get(k, 0) + 1
    try:
        with open(os.path.join(run_dir, "meta", "config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        rsdir = cfg.get("ruleset_dir") or ""
        from .versioning import ruleset_fingerprint, generated_by
        rid = os.path.basename(rsdir) if rsdir else ""
        rfp = ruleset_fingerprint(rsdir) if rsdir and os.path.isdir(rsdir) else ""
        gb = generated_by("0.1.0", rid, rfp, 1)
    except Exception:
        gb = {"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"","ruleset_fingerprint":"","schema_version":1}
    data = {"schema_version": 1, "entrypoints": eps_sorted, "stats": stats, "generated_by": gb}
    write_json(os.path.join(run_dir, "entrypoints.json"), data)
    return data
