import os


DEFAULT_THRESHOLDS = {
    "large_file_lines": 400,
    "giant_file_lines": 800,
}

RULES = {
    "CHD-001": {
        "title": "Large or giant file",
        "description": "Detects files that are large enough to create maintainability risk.",
        "confidence_policy": "conservative",
    },
    "CHD-002": {
        "title": "Debt comment",
        "description": "Detects TODO/FIXME/HACK/workaround style comments in code files.",
        "confidence_policy": "evidence-backed",
    },
    "CHD-003": {
        "title": "Type escape",
        "description": "Detects explicit static typing bypass signals.",
        "confidence_policy": "evidence-backed",
    },
    "CHD-004": {
        "title": "Swallowed error",
        "description": "Detects empty or value-returning catch/except blocks without log or rethrow.",
        "confidence_policy": "conservative",
    },
    "CHD-005": {
        "title": "High-risk backend file without adjacent test evidence",
        "description": "Detects backend side-effect files where adjacent test evidence is not observed by naming.",
        "confidence_policy": "suspected-only",
    },
}

SOURCE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".tmp_test_runs",
    ".reposense_ci",
    ".reposense_demo",
    ".reposense_release_demo",
    "coverage",
    "vendor",
}


def is_generated_or_config(rel_path):
    p = rel_path.replace("\\", "/").lower()
    base = os.path.basename(p)
    if base.endswith((".min.js", ".bundle.js", ".lock", ".map")):
        return True
    if base in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock"}:
        return True
    if "/dist/" in p or "/build/" in p:
        return True
    return False


def is_test_path(rel_path):
    p = rel_path.replace("\\", "/").lower()
    base = os.path.basename(p)
    return (
        "/test/" in p
        or "/tests/" in p
        or base.startswith("test_")
        or base.endswith(("_test.py", ".test.ts", ".spec.ts", "test.java", "tests.java"))
        or "/mock/" in p
        or "/mocks/" in p
    )


def is_core_path(rel_path):
    p = rel_path.replace("\\", "/").lower()
    return any(part in p for part in ["/src/", "/app/", "/service", "/controller", "/domain", "/api/"]) or p.startswith(("src/", "app/"))


def language_for_path(rel_path):
    ext = os.path.splitext(rel_path.lower())[1]
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
    }.get(ext, "unknown")
