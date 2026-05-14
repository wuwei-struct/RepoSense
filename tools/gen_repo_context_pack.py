#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RepoSense Repo Context Pack generator (repository-level snapshot).
Goal: produce a reproducible, diff-friendly, archive-friendly pack for repo handoff.

Usage:
  python tools/gen_repo_context_pack.py --out packs/repo_context_pack --zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_EXCLUDES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".DS_Store",
    ".reposense_studio",
    "analysis_runs",
    "outputs",
    "reports",
    "packs",
    "context_out",
    "learn_out",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".sqlite",
    ".db",
    ".log",
}

SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "id_ecdsa",
}

SENSITIVE_SUFFIXES = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}

TEXT_EXT_HINT = {
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".js",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".sh",
    ".bat",
    ".ps1",
}

ZIP_FIXED_DATETIME = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding=encoding, newline="\n") as f:
        f.write(text)
    tmp.replace(path)


def atomic_write_json(path: Path, obj, *, indent: int = 2) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=True)
    atomic_write_text(path, text + "\n")


def run_cmd(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 999, "", f"{type(e).__name__}: {e}"


def safe_relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_sensitive_file(path: Path) -> bool:
    name = path.name
    if name in SENSITIVE_FILE_NAMES:
        return True
    if name.startswith(".env"):
        return True
    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    return False


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(2048)
        if b"\x00" in chunk:
            return True
        if path.suffix.lower() in TEXT_EXT_HINT:
            return False
        try:
            chunk.decode("utf-8")
            return False
        except Exception:
            return True
    except Exception:
        return True


def iter_repo_files(root: Path, excludes: set) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(dirnames)
        filenames = sorted(filenames)
        rel_dir = Path(dirpath).resolve().relative_to(root.resolve()).as_posix()
        parts = [] if rel_dir == "." else rel_dir.split("/")
        if any(p in excludes for p in parts):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in excludes]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                rel = safe_relpath(p, root)
            except Exception:
                continue
            rel_parts = rel.split("/")
            if any(part in excludes for part in rel_parts):
                continue
            yield p


@dataclass(frozen=True)
class IndexedFile:
    path: str
    size: int
    sha256: Optional[str]
    is_binary: Optional[bool]
    lines: Optional[int]
    status: str
    reason: Optional[str]


def index_repository_files(
    root: Path, excludes: set, max_file_bytes: int
) -> Tuple[List[IndexedFile], List[Path], Dict[str, List[dict]], List[str]]:
    indexed: List[IndexedFile] = []
    included: List[Path] = []
    excluded_files: List[dict] = []
    sensitive_files: List[dict] = []
    warnings: List[str] = []

    for p in iter_repo_files(root, excludes):
        rel = safe_relpath(p, root)
        try:
            size = p.stat().st_size
        except Exception as e:
            indexed.append(
                IndexedFile(
                    path=rel,
                    size=-1,
                    sha256=None,
                    is_binary=None,
                    lines=None,
                    status="error",
                    reason=f"stat_failed:{type(e).__name__}",
                )
            )
            warnings.append(f"stat_failed:{rel}:{type(e).__name__}")
            continue

        if is_sensitive_file(p):
            indexed.append(
                IndexedFile(
                    path=rel,
                    size=size,
                    sha256=None,
                    is_binary=None,
                    lines=None,
                    status="excluded",
                    reason="sensitive",
                )
            )
            sensitive_files.append({"path": rel, "size": size, "reason": "sensitive"})
            warnings.append(f"sensitive_skipped:{rel}")
            continue

        suffix = p.suffix.lower()
        excluded_by_suffix = suffix in EXCLUDE_SUFFIXES

        file_is_binary = None
        try:
            file_is_binary = is_binary_file(p)
        except Exception:
            file_is_binary = None

        if size > max_file_bytes:
            indexed.append(
                IndexedFile(
                    path=rel,
                    size=size,
                    sha256=None,
                    is_binary=file_is_binary,
                    lines=None,
                    status="skipped",
                    reason="too_large",
                )
            )
            excluded_files.append({"path": rel, "size": size, "reason": "too_large"})
            warnings.append(f"skip_large_file:{rel}:size={size}")
            continue

        file_sha: Optional[str] = None
        try:
            file_sha = sha256_file(p)
        except Exception as e:
            warnings.append(f"sha256_failed:{rel}:{type(e).__name__}")

        file_lines: Optional[int] = None
        if file_is_binary is False:
            try:
                with p.open("r", encoding="utf-8", errors="replace") as f:
                    file_lines = sum(1 for _ in f)
            except Exception:
                file_lines = None

        if excluded_by_suffix:
            indexed.append(
                IndexedFile(
                    path=rel,
                    size=size,
                    sha256=file_sha,
                    is_binary=file_is_binary,
                    lines=file_lines,
                    status="excluded",
                    reason=f"suffix_excluded:{suffix}",
                )
            )
            excluded_files.append({"path": rel, "size": size, "reason": f"suffix_excluded:{suffix}"})
            continue

        indexed.append(
            IndexedFile(
                path=rel,
                size=size,
                sha256=file_sha,
                is_binary=file_is_binary,
                lines=file_lines,
                status="included",
                reason=None,
            )
        )
        included.append(p)

    indexed_sorted = sorted(indexed, key=lambda x: x.path)
    return (
        indexed_sorted,
        sorted(included, key=lambda x: safe_relpath(x, root)),
        {
            "excluded_files": sorted(excluded_files, key=lambda x: x["path"]),
            "sensitive_files": sorted(sensitive_files, key=lambda x: x["path"]),
        },
        sorted(set(warnings)),
    )


def build_tree(root: Path, excludes: set) -> str:
    lines: List[str] = []

    def walk(dir_path: Path, prefix: str = "") -> None:
        entries = []
        for child in dir_path.iterdir():
            try:
                rel = safe_relpath(child, root)
            except Exception:
                continue
            parts = rel.split("/")
            if any(p in excludes for p in parts):
                continue
            if child.is_dir():
                entries.append((child.name, True, child))
            else:
                if is_sensitive_file(child):
                    continue
                if child.suffix.lower() in EXCLUDE_SUFFIXES:
                    continue
                entries.append((child.name, False, child))

        entries.sort(key=lambda x: (not x[1], x[0]))
        for i, (name, is_dir, child) in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            if is_dir:
                lines.append(f"{prefix}{connector}{name}/")
                walk(child, prefix + ("    " if last else "│   "))
            else:
                try:
                    size = child.stat().st_size
                except Exception:
                    size = -1
                lines.append(f"{prefix}{connector}{name} ({size} bytes)")

    lines.append(f"{root.name}/")
    walk(root)
    return "\n".join(lines) + "\n"


def collect_repo_fingerprint(root: Path) -> Tuple[dict, List[str]]:
    warnings: List[str] = []
    fp: Dict[str, object] = {
        "generated_epoch": int(time.time()),
        "repo_root": str(root.resolve()),
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "git": {},
        "lockfiles": {},
    }

    code, out, err = run_cmd(["git", "rev-parse", "--show-toplevel"], root)
    if code != 0:
        warnings.append(f"git_unavailable:{err.strip() or 'rev-parse failed'}")
        fp["git"] = {"available": False}
    else:
        fp["git"] = {"available": True, "toplevel": out.strip()}

        def git_one(cmd: List[str], key: str) -> None:
            c, o, e = run_cmd(cmd, root)
            if c == 0:
                fp["git"][key] = o.strip()
            else:
                warnings.append(f"git_cmd_failed:{' '.join(cmd)}:{e.strip()}")

        git_one(["git", "rev-parse", "HEAD"], "head")
        git_one(["git", "rev-parse", "--abbrev-ref", "HEAD"], "branch")
        c, o, e = run_cmd(["git", "status", "--porcelain"], root)
        if c == 0:
            dirty_lines = [x for x in o.splitlines() if x.strip()]
            fp["git"]["dirty"] = bool(dirty_lines)
            fp["git"]["dirty_count"] = len(dirty_lines)
        else:
            warnings.append(f"git_status_failed:{e.strip()}")

    candidates = [
        "pyproject.toml",
        "poetry.lock",
        "pdm.lock",
        "requirements.txt",
        "requirements-dev.txt",
        "uv.lock",
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
    ]
    for rel in candidates:
        p = root / rel
        if p.exists() and p.is_file():
            try:
                fp["lockfiles"][rel] = {"sha256": sha256_file(p), "size": p.stat().st_size}
            except Exception as e:
                warnings.append(f"lockfile_hash_failed:{rel}:{type(e).__name__}")

    return fp, warnings


def capture_cli_help(root: Path, out_dir: Path, warnings: List[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    cmds = [
        ([sys.executable, "-m", "reposense", "--help"], "reposense_help.txt"),
        ([sys.executable, "-m", "reposense", "learn", "--help"], "reposense_learn_help.txt"),
        ([sys.executable, "-m", "reposense", "context", "--help"], "reposense_context_help.txt"),
        ([sys.executable, "-m", "reposense", "arch", "--help"], "reposense_arch_help.txt"),
        ([sys.executable, "-m", "reposense", "specs", "--help"], "reposense_specs_help.txt"),
        ([sys.executable, "-m", "reposense", "cases", "--help"], "reposense_cases_help.txt"),
        ([sys.executable, "-m", "reposense", "rules", "--help"], "reposense_rules_help.txt"),
        ([sys.executable, "-m", "reposense", "studio", "--help"], "reposense_studio_help.txt"),
    ]

    for cmd, fname in cmds:
        code, stdout, stderr = run_cmd(cmd, root)
        payload: List[str] = []
        payload.append(f"$ python -m {' '.join(cmd[3:])}".rstrip())
        payload.append(f"exit_code={code}")
        if stderr.strip():
            payload.append("\n[stderr]\n" + stderr.strip())
        if stdout.strip():
            payload.append("\n[stdout]\n" + stdout.strip())
        atomic_write_text(out_dir / fname, "\n".join(payload) + "\n")
        if code != 0:
            warnings.append(f"cli_help_failed:{' '.join(cmd)}")


def extract_api_routes(root: Path, excludes: set) -> List[str]:
    routes = set()
    pat = re.compile(r"""["'](/api/[A-Za-z0-9_\-\/\{\}\:\.]+)["']""")

    for p in sorted(iter_repo_files(root, excludes), key=lambda x: safe_relpath(x, root)):
        if p.suffix.lower() != ".py":
            continue
        if is_sensitive_file(p):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in pat.finditer(text):
            routes.add(m.group(1))

    return sorted(routes)


def copy_repo_files(files: List[Path], root: Path, pack_repo_dir: Path) -> None:
    for p in files:
        rel = safe_relpath(p, root)
        dst = pack_repo_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def build_pack_readme() -> str:
    return (
        "# Repo Context Pack (Repository Snapshot)\n\n"
        "This pack is a repository-level snapshot for handoff / AI session migration.\n\n"
        "## Contents\n"
        "- repo_fingerprint.json: reproducibility fingerprint (git/head/dirty, lockfile hashes)\n"
        "- tree.txt: deterministic repository tree (excluding build outputs & dependencies)\n"
        "- files_index.json: file list with sha256/size/lines\n"
        "- cli_help/: captured CLI help outputs\n"
        "- api_routes.json: lightweight /api route strings extracted from source\n"
        "- assets_index.json: key entrypoints and asset directories\n"
        "- repo/: copied source files (excluding build outputs & dependency dirs)\n"
        "- checksums.json: sha256 for every file in this pack (stable order)\n"
        "- warnings.json: downgrade info / missing tools / skipped files\n\n"
        "## How to regenerate\n"
        "Run from repo root:\n"
        "  python tools/gen_repo_context_pack.py --out <out_dir> --zip\n"
    )


def freeze_argv(argv: List[str]) -> List[str]:
    out: List[str] = []
    redact_next = False
    for a in argv:
        if redact_next:
            out.append("<redacted>")
            redact_next = False
            continue
        if a in {"--out", "--sample-path"}:
            out.append(a)
            redact_next = True
            continue
        if a.startswith("--out="):
            out.append("--out=<redacted>")
            continue
        if a.startswith("--sample-path="):
            out.append("--sample-path=<redacted>")
            continue
        out.append(a)
    return out


def build_start_here(fp: dict, assets_index: dict, routes: List[str], manifest: dict) -> str:
    git = fp.get("git", {}) if isinstance(fp.get("git", {}), dict) else {}
    head = git.get("head", "")
    branch = git.get("branch", "")
    dirty = git.get("dirty", "")
    repo_root = manifest.get("repo_root", ".")

    entrypoints = assets_index.get("entrypoints", [])
    key_paths = assets_index.get("key_paths", [])

    lines: List[str] = []
    lines.append("# START_HERE｜Repo Context Pack 导览\n")
    lines.append("本包是 RepoSense 仓库级快照，用于交接、审计与离线阅读。\n")
    lines.append("## 快速入口\n")
    lines.append("- HOTSPOTS：HOTSPOTS.md\n")
    lines.append("- 合同层：docs/contracts/\n")
    lines.append("- 文件树：tree.txt\n")
    lines.append("- 文件索引：files_index.json\n")
    lines.append("- 路由索引：api_routes.json\n")
    lines.append("- 生成器元信息：pack_meta.json\n")
    lines.append("- 内容稳定 ID：content_id.json\n")
    lines.append("\n## 当前仓库信息\n")
    lines.append(f"- repo_root：{repo_root}\n")
    if head:
        lines.append(f"- git.head：{head}\n")
    if branch:
        lines.append(f"- git.branch：{branch}\n")
    if dirty != "":
        lines.append(f"- git.dirty：{dirty}\n")
    lines.append("\n## 关键路径（建议从这里读起）\n")
    for p in entrypoints:
        lines.append(f"- {p}\n")
    if not entrypoints:
        for p in key_paths:
            lines.append(f"- {p}/\n")
    lines.append("\n## DEMO（可选示例产物）\n")
    lines.append(
        "- 如果本包生成时带了 --sample-path，则 examples/demo_run/ 里会包含一个示例 run 产物副本（不重新扫描）。\n"
    )
    lines.append("\n## 本包不包含什么\n")
    lines.append("- 不默认包含 .sqlite/.db/.log 等运行产物与大文件（即使 sample 也会过滤）。\n")
    lines.append("\n## Studio API 速览\n")
    if routes:
        for r in routes[:20]:
            lines.append(f"- {r}\n")
        if len(routes) > 20:
            lines.append(f"- ...（共 {len(routes)} 个）\n")
    else:
        lines.append("- 未发现 /api 路由（api_routes.json 为空）。\n")
    return "".join(lines)


def build_hotspots(assets_index: dict) -> str:
    entrypoints = assets_index.get("entrypoints", [])
    key_paths = assets_index.get("key_paths", [])
    rulesets = assets_index.get("rulesets", [])

    lines: List[str] = []
    lines.append("# HOTSPOTS｜热点入口（建议阅读顺序）\n\n")
    lines.append("## 入口脚本\n")
    for p in entrypoints:
        lines.append(f"- {p}\n")
    if not entrypoints:
        lines.append("- （未发现 entrypoints）\n")

    lines.append("\n## 核心目录\n")
    for p in key_paths:
        lines.append(f"- {p}/\n")

    lines.append("\n## Rulesets\n")
    for r in rulesets:
        lines.append(f"- rulesets/{r}/\n")
    if not rulesets:
        lines.append("- （未发现 rulesets）\n")

    lines.append("\n## 建议读法\n")
    lines.append("- 先看 docs/contracts/ 了解稳定契约，再看 reposense/cli.py 了解命令编排。\n")
    lines.append("- 如果你关注 Studio：先看 reposense/studio/server.py 与 webui/studio/index.html。\n")
    return "".join(lines)


def build_contract_run_dir() -> str:
    return (
        "# RUN_DIR｜运行目录契约（Contract）\n\n"
        "本文件描述 RepoSense 的 run_dir 产物结构与稳定字段，便于下游工具消费与回放。\n\n"
        "## 目录结构（典型）\n"
        "- report.json：结构化 findings（含 schema_version/engine_version/ruleset_version/budget_profile）\n"
        "- report.html：离线报告页面\n"
        "- evidence/：Evidence JSON（E*.json），可追溯到原始片段\n"
        "- detections.sqlite：冻结的检测数据库（表结构由 sql/schema_v1.sql 约束）\n"
        "- indices.sqlite：索引数据库\n"
        "- event_graph.json：事件图（nodes/edges）\n"
        "- meta/：config.json / tool_version / ruleset_version 等元信息\n"
        "- exports/：导出产物（例如 SARIF）\n\n"
        "## 稳定性要点\n"
        "- 下游应优先使用 evidence 引用（可审计），而非仅依赖 HTML。\n"
        "- SQLite 表结构与 user_version 是契约的一部分：见 repo/sql/schema_v1.sql。\n"
    )


def build_contract_studio_api(routes: List[str]) -> str:
    known: List[Tuple[str, str, str]] = []
    for r in routes:
        if r == "/api/projects/import-zip":
            known.append((r, "POST", "multipart/form-data；字段 file 为 ZIP"))
        elif r == "/api/runs":
            known.append((r, "GET/POST", "GET 列表；POST 创建运行（JSON body）"))
        elif r.startswith("/api/runs/"):
            known.append((r, "GET", "查询单个 run 状态"))
        else:
            known.append((r, "GET/POST", "未分类（来自源码字符串提取）"))

    lines: List[str] = []
    lines.append("# STUDIO_API｜本地 Studio API 契约（Contract）\n\n")
    lines.append("本文件基于 api_routes.json 中提取到的 /api 路由生成，用于离线对接与回归测试。\n\n")
    if not known:
        lines.append("未提取到任何 /api 路由。\n")
        return "".join(lines)

    lines.append("## 端点列表\n")
    for path, method, note in known:
        lines.append(f"- {method} {path}：{note}\n")
    lines.append("\n## 通用约定\n")
    lines.append("- 基础地址通常为 http://127.0.0.1:<port>\n")
    lines.append("- 响应 JSON 使用 UTF-8；错误返回为 HTTP 4xx/5xx。\n")
    return "".join(lines)


def build_contract_sites() -> str:
    return (
        "# SITES｜本地站点/静态资源契约（Contract）\n\n"
        "本文件描述 Studio/WebUI 与运行产物的常见访问路径，便于离线浏览与集成。\n\n"
        "## Studio WebUI\n"
        "- / 或 /studio/：Studio 首页\n"
        "- /static/<name>：静态资源（CSS/JS 等）\n\n"
        "## Run 产物浏览（典型）\n"
        "- /runs/<run_id>/report/：重定向到 report.html\n"
        "- /runs/<run_id>/report/<file>：从 run_dir 根目录读取对应文件\n"
        "- /runs/<run_id>/learn/：重定向到 learn 站点 index.html\n"
        "- /runs/<run_id>/learn/<file>：从 learn_site/ 读取对应文件\n"
    )


def build_coverage(indexed: List[IndexedFile], warnings_obj: dict, files_copied: int) -> dict:
    by_status: Dict[str, int] = {"included": 0, "excluded": 0, "skipped": 0, "error": 0}
    by_reason: Dict[str, int] = {}

    for f in indexed:
        by_status[f.status] = by_status.get(f.status, 0) + 1
        if f.reason:
            by_reason[f.reason] = by_reason.get(f.reason, 0) + 1

    sensitive_count = by_reason.get("sensitive", 0)
    excluded_count = by_status.get("excluded", 0)
    skipped_count = by_status.get("skipped", 0)

    warnings_list = warnings_obj.get("warnings", [])
    warnings_count = len(warnings_list) if isinstance(warnings_list, list) else 0

    return {
        "totals": {
            "files_in_index": len(indexed),
            "files_copied": files_copied,
            "warnings_count": warnings_count,
            "sensitive_count": sensitive_count,
            "excluded_count": excluded_count,
            "skipped_count": skipped_count,
        },
        "by_status": dict(sorted(by_status.items(), key=lambda x: x[0])),
        "by_reason": dict(sorted(by_reason.items(), key=lambda x: x[0])),
    }


def build_content_id(indexed: List[IndexedFile]) -> Tuple[str, int, List[dict]]:
    included_entries: List[dict] = []
    for f in indexed:
        if f.status != "included":
            continue
        included_entries.append({"path": f.path, "sha256": f.sha256 or "", "size": f.size})
    included_entries.sort(key=lambda x: x["path"])
    payload = json.dumps(included_entries, ensure_ascii=False, sort_keys=True)
    content_id = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return content_id, len(included_entries), included_entries


def _copy_file_filtered(src: Path, dst: Path, warnings: List[str], max_file_bytes: int) -> bool:
    try:
        if is_sensitive_file(src):
            warnings.append(f"sample_skip_sensitive:{src.name}")
            return False
        if src.suffix.lower() in EXCLUDE_SUFFIXES:
            warnings.append(f"sample_skip_suffix:{src.name}:{src.suffix.lower()}")
            return False
        size = src.stat().st_size
        if size > max_file_bytes:
            warnings.append(f"sample_skip_large:{src.name}:size={size}")
            return False
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        warnings.append(f"sample_copy_failed:{src.name}:{type(e).__name__}")
        return False


def _copy_tree_filtered(src_dir: Path, dst_dir: Path, warnings: List[str], max_file_bytes: int, excludes: set) -> int:
    copied = 0
    for p in sorted([x for x in src_dir.rglob("*") if x.is_file()], key=lambda x: x.as_posix()):
        rel = p.relative_to(src_dir).as_posix()
        if any(part in excludes for part in rel.split("/")):
            continue
        if is_sensitive_file(p):
            continue
        if p.suffix.lower() in EXCLUDE_SUFFIXES:
            continue
        try:
            if p.stat().st_size > max_file_bytes:
                warnings.append(f"sample_skip_large:{src_dir.name}/{rel}")
                continue
        except Exception:
            continue
        dst = dst_dir / rel
        if _copy_file_filtered(p, dst, warnings, max_file_bytes):
            copied += 1
    return copied


def copy_sample_run(sample_path: Path, pack_dir: Path, warnings: List[str], max_file_bytes: int, excludes: set) -> None:
    if not sample_path.exists():
        warnings.append(f"sample_path_missing:{sample_path}")
        return
    if not sample_path.is_dir():
        warnings.append(f"sample_path_not_dir:{sample_path}")
        return

    dst_root = pack_dir / "examples" / "demo_run"
    dst_root.mkdir(parents=True, exist_ok=True)

    file_candidates = [
        "report.html",
        "report.json",
        "event_graph.json",
        "verify.json",
        "verify_output.json",
    ]
    dir_candidates = [
        "arch_views",
        "meta",
        "report_site",
        "learn_site",
        "learn_out",
        "sarif",
    ]

    for fn in file_candidates:
        src = sample_path / fn
        if src.exists() and src.is_file():
            _copy_file_filtered(src, dst_root / fn, warnings, max_file_bytes)

    for dn in dir_candidates:
        srcd = sample_path / dn
        if srcd.exists() and srcd.is_dir():
            _copy_tree_filtered(srcd, dst_root / dn, warnings, max_file_bytes, excludes)

    for p in sorted(sample_path.iterdir(), key=lambda x: x.name):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf == ".sarif" or p.name.lower().endswith(".sarif.json"):
            _copy_file_filtered(p, dst_root / p.name, warnings, max_file_bytes)


def list_all_files_under(dir_path: Path) -> List[Path]:
    return sorted([p for p in dir_path.rglob("*") if p.is_file()], key=lambda x: x.as_posix())


def compute_pack_checksums(pack_root: Path) -> List[dict]:
    items: List[dict] = []
    for p in list_all_files_under(pack_root):
        rel = p.relative_to(pack_root).as_posix()
        items.append({"path": rel, "sha256": sha256_file(p)})
    items.sort(key=lambda x: x["path"])
    return items


def zip_pack(pack_root: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in list_all_files_under(pack_root):
            rel = p.relative_to(pack_root).as_posix()
            info = zipfile.ZipInfo(rel)
            info.date_time = ZIP_FIXED_DATETIME
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16) | 0
            zf.writestr(info, p.read_bytes())


def build_assets_index(repo_root: Path) -> dict:
    keys = [
        "reposense",
        "reposense/studio",
        "webui",
        "webui/studio",
        "specs",
        "rulesets",
        "tests",
        "sql",
        "presets",
        ".github/workflows",
    ]
    existing_paths = [k for k in keys if (repo_root / k).exists()]

    entrypoints = [
        "reposense/__main__.py",
        "reposense/cli.py",
        "reposense/studio/server.py",
        "webui/studio/index.html",
    ]
    existing_entrypoints = [p for p in entrypoints if (repo_root / p).exists()]

    rulesets = []
    rulesets_dir = repo_root / "rulesets"
    if rulesets_dir.exists() and rulesets_dir.is_dir():
        for p in sorted(rulesets_dir.iterdir(), key=lambda x: x.name):
            if p.is_dir():
                rulesets.append(p.name)

    return {
        "key_paths": existing_paths,
        "entrypoints": existing_entrypoints,
        "rulesets": rulesets,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory path (pack dir).")
    ap.add_argument("--zip", action="store_true", help="Also produce a deterministic zip next to out dir.")
    ap.add_argument("--max-file-bytes", type=int, default=1_000_000, help="Max single file size to include (bytes).")
    ap.add_argument("--exclude", action="append", default=[], help="Additional exclude dir/file names.")
    ap.add_argument(
        "--freeze-meta",
        action="store_true",
        help="Freeze epoch timestamps and absolute paths for diff-friendly packs.",
    )
    ap.add_argument(
        "--sample-path",
        default=None,
        help="Optional: copy a sample run_dir or studio run output into examples/demo_run/ for readers.",
    )
    args = ap.parse_args()

    repo_root = Path.cwd().resolve()
    excludes = set(DEFAULT_EXCLUDES)
    excludes.update(args.exclude)

    pack_dir = Path(args.out).resolve()
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)

    warnings: List[str] = []
    fp, fp_warn = collect_repo_fingerprint(repo_root)
    warnings.extend(fp_warn)
    if args.freeze_meta:
        fp["generated_epoch"] = 0
        fp["repo_root"] = "."
        py = fp.get("python", {})
        if isinstance(py, dict):
            py["executable"] = "<redacted>"
        git = fp.get("git", {})
        if isinstance(git, dict) and "toplevel" in git:
            git["toplevel"] = "."

    indexed, included, excluded_detail, file_warn = index_repository_files(repo_root, excludes, args.max_file_bytes)
    warnings.extend(file_warn)

    atomic_write_text(pack_dir / "README.md", build_pack_readme())
    atomic_write_json(pack_dir / "repo_fingerprint.json", fp)
    atomic_write_text(pack_dir / "tree.txt", build_tree(repo_root, excludes))

    files_index = {
        "max_file_bytes": args.max_file_bytes,
        "files": [f.__dict__ for f in indexed],
    }
    atomic_write_json(pack_dir / "files_index.json", files_index)

    capture_cli_help(repo_root, pack_dir / "cli_help", warnings)

    routes = extract_api_routes(repo_root, excludes)
    atomic_write_json(pack_dir / "api_routes.json", {"routes": routes})

    assets_index = build_assets_index(repo_root)
    atomic_write_json(pack_dir / "assets_index.json", assets_index)

    pack_repo_dir = pack_dir / "repo"
    copy_repo_files(included, repo_root, pack_repo_dir)

    manifest = {
        "created_epoch": int(time.time()),
        "repo_root": str(repo_root),
        "pack_format": "repo_context_pack_v1",
        "excluded_names": sorted(excludes),
        "max_file_bytes": args.max_file_bytes,
        "counts": {"files_in_index": len(indexed), "files_copied": len(included), "api_routes": len(routes)},
    }
    if args.freeze_meta:
        manifest["created_epoch"] = 0
        manifest["repo_root"] = "."
    atomic_write_json(pack_dir / "repo_context_manifest.json", manifest)

    atomic_write_text(pack_dir / "START_HERE.md", build_start_here(fp, assets_index, routes, manifest))
    atomic_write_text(pack_dir / "HOTSPOTS.md", build_hotspots(assets_index))
    atomic_write_text(pack_dir / "docs" / "contracts" / "RUN_DIR.md", build_contract_run_dir())
    atomic_write_text(pack_dir / "docs" / "contracts" / "STUDIO_API.md", build_contract_studio_api(routes))
    atomic_write_text(pack_dir / "docs" / "contracts" / "SITES.md", build_contract_sites())

    warnings_obj = {
        "warnings": sorted(set(warnings)),
        "excluded_files": excluded_detail["excluded_files"],
        "sensitive_files": excluded_detail["sensitive_files"],
    }
    atomic_write_json(pack_dir / "warnings.json", warnings_obj)

    if args.sample_path:
        copy_sample_run(Path(args.sample_path), pack_dir, warnings, args.max_file_bytes, excludes)
        warnings_obj = {
            "warnings": sorted(set(warnings)),
            "excluded_files": excluded_detail["excluded_files"],
            "sensitive_files": excluded_detail["sensitive_files"],
        }
        atomic_write_json(pack_dir / "warnings.json", warnings_obj)

    coverage = build_coverage(indexed, warnings_obj, len(included))
    atomic_write_json(pack_dir / "coverage.json", coverage)

    content_id, included_files_n, _included_entries = build_content_id(indexed)
    atomic_write_json(
        pack_dir / "content_id.json",
        {"content_id": content_id, "algo": "sha1(paths+sha256+size)", "included_files": included_files_n},
    )

    checksums = compute_pack_checksums(pack_dir)
    atomic_write_json(pack_dir / "checksums.json", checksums)

    pack_id = hashlib.sha1(json.dumps(checksums, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    atomic_write_json(pack_dir / "pack_id.json", {"pack_id": pack_id})

    gen_argv = freeze_argv(sys.argv) if args.freeze_meta else list(sys.argv)
    pack_meta = {
        "pack_format": "repo_context_pack_v2",
        "pack_id": pack_id,
        "content_id": content_id,
        "generated_epoch": 0 if args.freeze_meta else int(time.time()),
        "git": {
            "head": (fp.get("git", {}) or {}).get("head") if isinstance(fp.get("git", {}), dict) else None,
            "branch": (fp.get("git", {}) or {}).get("branch") if isinstance(fp.get("git", {}), dict) else None,
            "dirty": (fp.get("git", {}) or {}).get("dirty") if isinstance(fp.get("git", {}), dict) else None,
            "dirty_count": (fp.get("git", {}) or {}).get("dirty_count") if isinstance(fp.get("git", {}), dict) else None,
        },
        "excludes": sorted(excludes),
        "max_file_bytes": args.max_file_bytes,
        "generator": {"script": "tools/gen_repo_context_pack.py", "argv": gen_argv},
        "counts": {
            "files_in_index": len(indexed),
            "files_copied": len(included),
            "api_routes": len(routes),
            "warnings_count": coverage.get("totals", {}).get("warnings_count", 0),
            "sensitive_count": coverage.get("totals", {}).get("sensitive_count", 0),
            "excluded_count": coverage.get("totals", {}).get("excluded_count", 0),
            "skipped_count": coverage.get("totals", {}).get("skipped_count", 0),
        },
    }
    atomic_write_json(pack_dir / "pack_meta.json", pack_meta)

    if args.zip:
        zip_path = pack_dir.with_suffix(".zip")
        zip_pack(pack_dir, zip_path)

    print(f"[OK] repo context pack written to: {pack_dir}")
    if args.zip:
        print(f"[OK] repo context zip written to: {pack_dir.with_suffix('.zip')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
