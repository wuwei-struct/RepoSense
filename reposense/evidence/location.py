import os
import re
from pathlib import Path


_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def is_absolute_path(value):
    raw = str(value or "").strip()
    return bool(raw) and (os.path.isabs(raw) or bool(_WINDOWS_ABSOLUTE.match(raw)))


def _line_value(ref, primary, alternate):
    value = ref.get(primary)
    if value is None:
        value = ref.get(alternate)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _relative_path(value, repo_root, allow_repo_absolute):
    raw = str(value or "").strip()
    if not raw:
        return None
    normalized = raw.replace("\\", "/")
    for token in ("<REPO_ROOT>", "${REPO_ROOT}"):
        if normalized.startswith(token + "/"):
            return normalized[len(token) + 1 :]
    if is_absolute_path(raw):
        if not allow_repo_absolute or not repo_root:
            return None
        try:
            return Path(raw).resolve().relative_to(Path(repo_root).resolve()).as_posix()
        except (OSError, ValueError):
            return None
    path = Path(normalized)
    if any(part == ".." for part in path.parts):
        return None
    relative = path.as_posix()
    return relative[2:] if relative.startswith("./") else relative


def canonicalize_evidence_ref(ref, repo_root=None, allow_repo_absolute=False):
    """Return a canonical relative code evidence ref, or None when location is unknown."""
    if not isinstance(ref, dict):
        return None
    file_value = ref.get("file") or ref.get("path") or ref.get("repo_path")
    file_path = _relative_path(file_value, repo_root, allow_repo_absolute)
    start = _line_value(ref, "start_line", "line_start")
    end = _line_value(ref, "end_line", "line_end")
    if not file_path or start is None or start < 1:
        return None
    if end is None:
        end = start
    if end < start:
        return None
    out = dict(ref)
    out.pop("path", None)
    out.pop("repo_path", None)
    out.pop("absolute_path", None)
    out.pop("line_start", None)
    out.pop("line_end", None)
    out["file"] = file_path
    out["start_line"] = start
    out["end_line"] = end
    return out


def evidence_ref_key(ref):
    canonical = canonicalize_evidence_ref(ref)
    if canonical is None:
        return None
    return (
        str(canonical.get("source_type") or ""),
        str(canonical.get("finding_id") or ""),
        str(canonical.get("event_id") or ""),
        canonical["file"],
        canonical["start_line"],
        canonical["end_line"],
        str(canonical.get("rule_id") or ""),
    )


def filter_valid_evidence_refs(refs):
    """Structurally filter and deduplicate serialized evidence refs without inventing locations."""
    valid = []
    invalid_count = 0
    seen = set()
    for ref in refs if isinstance(refs, list) else []:
        canonical = canonicalize_evidence_ref(ref)
        if canonical is None:
            invalid_count += 1
            continue
        key = evidence_ref_key(canonical)
        if key in seen:
            continue
        seen.add(key)
        valid.append(canonical)
    return valid, invalid_count
