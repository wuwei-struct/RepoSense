import os
from .utils import skip_reason, detect_language, sha256_file, filesize, mtime, read_text, read_text_limited
def _bump(stats, key, path=None):
    if stats is None:
        return
    stats.setdefault("skipped", {})
    stats["skipped"][key] = stats["skipped"].get(key, 0) + 1
    if path:
        stats.setdefault("samples", {})
        stats["samples"].setdefault(key, [])
        if len(stats["samples"][key]) < 20:
            stats["samples"][key].append(path.replace("\\", "/"))
def walk_files_with_stats(root, budget):
    stats = {
        "included_files": 0,
        "included_bytes": 0,
        "skipped": {},
        "samples": {},
        "budget": {
            "max_files": budget.get("max_files", 50000),
            "max_total_bytes": budget.get("max_total_bytes", 1024 * 1024 * 1024),
            "max_file_bytes": budget.get("max_file_bytes"),
            "max_lines_per_file": budget.get("max_lines_per_file"),
        },
    }
    files = []
    count = 0
    total = 0
    max_files = int(budget.get("max_files", 50000))
    max_total = int(budget.get("max_total_bytes", 1024 * 1024 * 1024))
    for base, dirs, fs in os.walk(root):
        kept_dirs = []
        for d in dirs:
            p = os.path.join(base, d)
            r = skip_reason(p, budget)
            if r:
                _bump(stats, r, p)
                continue
            kept_dirs.append(d)
        dirs[:] = kept_dirs
        for f in fs:
            p = os.path.join(base, f)
            r = skip_reason(p, budget)
            if r:
                _bump(stats, r, p)
                continue
            try:
                sz = filesize(p)
            except Exception:
                _bump(stats, "stat_failed", p)
                continue
            if sz > int(budget.get("max_file_bytes", sz + 1)):
                _bump(stats, "too_large", p)
                continue
            count += 1
            total += sz
            if count > max_files:
                stats["skipped"]["budget_cut_files"] = stats["skipped"].get("budget_cut_files", 0) + 1
                stats["budget_cut_reached"] = True
                break
            if total > max_total:
                stats["skipped"]["budget_cut_bytes"] = stats["skipped"].get("budget_cut_bytes", 0) + 1
                stats["budget_cut_reached"] = True
                break
            files.append(p)
            stats["included_files"] += 1
            stats["included_bytes"] += sz
    return files, stats
def walk_files(root, budget):
    files, _ = walk_files_with_stats(root, budget)
    return files
def collect_file_info(path):
    return {
        "path": os.path.abspath(path),
        "lang": detect_language(path),
        "size": filesize(path),
        "sha256": sha256_file(path),
        "mtime": mtime(path)
    }
def read_lines(path):
    s = read_text(path)
    lines = s.splitlines()
    return lines
def read_lines_limited(path, budget):
    res = read_text_limited(path, max_bytes=(budget or {}).get("max_file_bytes"), max_lines=(budget or {}).get("max_lines_per_file"))
    return res

