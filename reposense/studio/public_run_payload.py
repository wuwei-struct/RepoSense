import copy
import re
from typing import Any, Dict, List


_WINDOWS_ABSOLUTE = re.compile(r"(?i)(?<![A-Za-z0-9])(?:[A-Z]:[\\/])")
_UNC_PATH = re.compile(r"(?<![A-Za-z0-9])(?:\\\\|//)[^/\\\s]+[\\/][^/\\\s]+")
_FILE_URI = re.compile(r"(?i)\bfile://")
_COMMON_POSIX_ROOT = re.compile(
    r"(?<![A-Za-z0-9:])/(?:home|Users|tmp|private|var|opt|root|mnt|srv|workspace)(?:/|\b)"
)
_PATH_FIELD_HINT = re.compile(
    r"(?i)(?:^|_)(?:path|dir|directory|workspace|repo|source|output|log)(?:$|_)"
)
_SAFE_HTTP_PATH_PREFIXES = (
    "/api/",
    "/runs/",
    "/studio/",
    "/artifact-cards.",
)
_PUBLIC_SECTIONS = (
    "summary",
    "artifact_groups",
    "recommended_artifacts",
    "missing_capabilities",
    "review",
)


def _string_path_reason(value: str, field_path: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    stripped = text.strip()
    if re.match(r"(?i)^https?://", stripped):
        return ""
    lowered = text.lower()
    if _FILE_URI.search(text):
        return "file_uri"
    if ".reposense_studio" in lowered:
        return "studio_workspace_path"
    if _WINDOWS_ABSOLUTE.search(text):
        return "windows_absolute_path"
    if _UNC_PATH.search(text):
        return "unc_path"
    if _COMMON_POSIX_ROOT.search(text):
        return "posix_absolute_path"

    if stripped.startswith("/") and not stripped.startswith(_SAFE_HTTP_PATH_PREFIXES):
        field_name = field_path.rsplit(".", 1)[-1].split("[", 1)[0]
        if _PATH_FIELD_HINT.search(field_name):
            return "posix_absolute_path"
    return ""


def find_local_path_leaks(payload: Any) -> List[Dict[str, str]]:
    """Return path locations and reasons without copying private values."""
    leaks = []

    def visit(value: Any, field_path: str) -> None:
        if isinstance(value, dict):
            for key in sorted(value, key=lambda item: str(item)):
                visit(value[key], f"{field_path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, f"{field_path}[{index}]")
        elif isinstance(value, str):
            reason = _string_path_reason(value, field_path)
            if reason:
                leaks.append({"field": field_path, "reason": reason})

    visit(payload, "$")
    return leaks


def _safe_text(value: Any, fallback: str, warnings: List[str], field: str) -> str:
    text = str(value or "")
    if not find_local_path_leaks({field: text}):
        return text
    warnings.append(f"{field}_omitted_local_path")
    return fallback


def _safe_logs(value: Any, warnings: List[str]) -> List[str]:
    if not isinstance(value, (list, tuple)):
        return []
    safe = []
    omitted = False
    for item in value:
        text = str(item)
        if find_local_path_leaks({"log_line": text}):
            omitted = True
            continue
        safe.append(text)
    if omitted:
        warnings.append("logs_tail_omitted_local_path")
    return safe


def _safe_timestamp(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return value


def _copy_safe_section(
    output: dict,
    source: dict,
    field: str,
    default: Any,
    warnings: List[str],
) -> None:
    value = source.get(field, default)
    if find_local_path_leaks({field: value}):
        warnings.append(f"{field}_omitted_local_path")
        output[field] = copy.deepcopy(default)
        return
    output[field] = copy.deepcopy(value)


def build_public_run_payload(run_state: Any) -> dict:
    """Build the allowlisted public run-detail DTO from internal state."""
    if not isinstance(run_state, dict):
        return {
            "run_id": "",
            "status": "",
            "phase": "",
            "logs_tail": [],
            "error_message": "",
            "warnings": ["invalid_internal_run_state"],
        }

    warnings = []
    output = {
        "run_id": _safe_text(run_state.get("run_id"), "", warnings, "run_id"),
        "status": _safe_text(run_state.get("status"), "", warnings, "status"),
        "phase": _safe_text(run_state.get("phase"), "", warnings, "phase"),
        "logs_tail": _safe_logs(
            run_state.get("logs_tail", run_state.get("logs", [])), warnings
        ),
        "error_message": _safe_text(
            run_state.get("error_message", run_state.get("error", "")),
            "Run failed; local details are available in Studio logs.",
            warnings,
            "error_message",
        ),
        "updated_at": _safe_timestamp(run_state.get("updated_at", 0)),
    }
    if "start_time" in run_state or "created_at" in run_state:
        output["start_time"] = _safe_timestamp(
            run_state.get("start_time", run_state.get("created_at", 0))
        )

    for field in _PUBLIC_SECTIONS:
        default = [] if field in {
            "artifact_groups",
            "recommended_artifacts",
            "missing_capabilities",
        } else {}
        _copy_safe_section(output, run_state, field, default, warnings)

    inherited = run_state.get("warnings")
    if isinstance(inherited, list) and not find_local_path_leaks({"warnings": inherited}):
        warnings.extend(str(item) for item in inherited)
    output["warnings"] = sorted(set(warnings))
    return output


def build_public_run_list_item(run_state: Any) -> dict:
    """Build the public list DTO using the same privacy contract as details."""
    payload = build_public_run_payload(run_state)
    payload.pop("logs_tail", None)
    payload.pop("error_message", None)
    return payload
