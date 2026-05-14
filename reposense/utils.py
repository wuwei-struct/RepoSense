import os
import hashlib
import time
import json
import re
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    return h.hexdigest()
def read_text(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        s = data.decode("utf-8", errors="replace")
    except:
        s = data.decode("latin-1", errors="replace")
    return s
def is_binary_bytes(data):
    if not data:
        return False
    if b"\x00" in data:
        return True
    sample = data[:8192]
    printable = 0
    for b in sample:
        if b in (9, 10, 13):
            printable += 1
        elif 32 <= b <= 126:
            printable += 1
    ratio = printable / max(1, len(sample))
    return ratio < 0.7
def read_text_limited(path, max_bytes=None, max_lines=None):
    encoding = "utf-8"
    with open(path, "rb") as f:
        data = f.read(max_bytes if max_bytes is not None else -1)
    truncated_bytes = False
    if max_bytes is not None:
        try:
            full_sz = os.path.getsize(path)
            if full_sz > max_bytes:
                truncated_bytes = True
        except Exception:
            pass
    if is_binary_bytes(data):
        return {"text": "", "lines": [], "encoding": None, "binary": True, "truncated": truncated_bytes}
    try:
        s = data.decode("utf-8", errors="replace")
        encoding = "utf-8"
    except Exception:
        s = data.decode("latin-1", errors="replace")
        encoding = "latin-1"
    lines = s.splitlines()
    truncated_lines = False
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated_lines = True
    return {"text": "\n".join(lines), "lines": lines, "encoding": encoding, "binary": False, "truncated": (truncated_bytes or truncated_lines)}
def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
def now_millis():
    return int(time.time() * 1000)
def safe_join(base, *paths):
    p = os.path.abspath(os.path.join(base, *paths))
    if os.path.commonpath([p, os.path.abspath(base)]) != os.path.abspath(base):
        raise ValueError("path traversal")
    return p
def normalize_manifest(obj):
    r = dict(obj)
    r.pop("timestamp", None)
    return r
def snippet_with_context(lines, start, end, ctx):
    s = max(1, start - ctx)
    e = min(len(lines), end + ctx)
    return "\n".join(lines[s - 1:e])
def clamp_text_bytes(s, max_bytes):
    if max_bytes is None:
        return s
    if not isinstance(s, str):
        return s
    b = s.encode("utf-8", errors="replace")
    if len(b) <= max_bytes:
        return s
    b = b[:max_bytes]
    return b.decode("utf-8", errors="ignore")
def clamp_lines(s, max_lines):
    if max_lines is None:
        return s
    if not isinstance(s, str):
        return s
    lines = s.splitlines()
    if len(lines) <= max_lines:
        return s
    return "\n".join(lines[:max_lines])
def detect_language(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".py"]:
        return "python"
    if ext in [".js", ".jsx", ".ts", ".tsx"]:
        return "javascript"
    if ext in [".go"]:
        return "go"
    if ext in [".java"]:
        return "java"
    if ext in [".c", ".h", ".cpp", ".cc"]:
        return "cxx"
    if ext in [".yaml", ".yml"]:
        return "yaml"
    if ext in [".json"]:
        return "json"
    return "text"
def default_ignores():
    return [
        ".git", "node_modules", "dist", "build", "out", ".next", "coverage",
        ".reposense_studio", "parse_cache", "learn_site", "context-pack", "packs",
        "outputs", "reports", "assets", "public", "static", "vendor", ".venv",
        "__pycache__"
    ]
_EXT_IGNORE = {
    ".csv", ".tsv", ".jsonl", ".ndjson",
    ".sqlite", ".db",
    ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".zip", ".7z", ".tar", ".gz",
    ".mp3", ".mp4", ".wav",
    ".woff", ".woff2", ".ttf",
}
def is_ignored(path):
    p_norm = path.replace("\\", "/")
    parts = p_norm.split("/")
    for ig in default_ignores():
        if ig in parts:
            return True
    # dict sources and common large data dumps
    if "dict_source" in parts:
        return True
    base = os.path.basename(p_norm).lower()
    if "cedict" in base:
        return True
    ext = os.path.splitext(base)[1].lower()
    if ext in _EXT_IGNORE:
        return True
    return False
def skip_reason(path, budget):
    p_norm = path.replace("\\", "/")
    parts = p_norm.split("/")
    ignore_dirs = set(default_ignores()) | set((budget or {}).get("ignore_dirs") or [])
    for ig in ignore_dirs:
        if ig in parts:
            return "ignored_dir"
    base = os.path.basename(p_norm).lower()
    if "cedict" in base:
        return "ignored_ext"
    ext = os.path.splitext(base)[1].lower()
    ignore_exts = set(_EXT_IGNORE) | set((budget or {}).get("ignore_exts") or [])
    if ext in ignore_exts:
        return "ignored_ext"
    max_file_bytes = (budget or {}).get("max_file_bytes")
    if max_file_bytes:
        try:
            if os.path.getsize(path) > int(max_file_bytes):
                return "too_large"
        except Exception:
            pass
    try:
        with open(path, "rb") as f:
            sample = f.read(8192)
        if is_binary_bytes(sample):
            return "binary"
    except Exception:
        pass
    return None
def filesize(path):
    return os.path.getsize(path)
def mtime(path):
    return int(os.path.getmtime(path))

