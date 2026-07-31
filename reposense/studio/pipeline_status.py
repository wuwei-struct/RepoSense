"""Structured, browser-safe Studio pipeline progress."""

from __future__ import annotations

import re
import time
from copy import deepcopy


PIPELINE_STATUSES = {"pending", "running", "passed", "warned", "failed", "skipped"}

PIPELINE_STEPS = (
    ("preparing", "Preparing repository"),
    ("scanning_facts", "Scanning facts"),
    ("building_event_graph", "Building event graph"),
    ("detecting_patterns", "Detecting patterns"),
    ("analyzing_code_health", "Analyzing code health"),
    ("reviewing_permissions", "Reviewing permissions"),
    ("correlating_transactions", "Correlating transactions"),
    ("reviewing_queue_reliability", "Reviewing queue reliability"),
    ("building_repository_review", "Building repository review"),
    ("building_context_pack", "Building Context Pack"),
    ("strict_verification", "Strict verification"),
    ("quality_gate", "Quality gate"),
    ("finalizing", "Finalizing run"),
)

_PRIVATE_PATH = re.compile(
    r"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+[\\/][^\\\s]+|file://|/(?:home|users|tmp|private|root|mnt|workspace)/)"
)


def build_pipeline_steps() -> list[dict]:
    return [
        {
            "step_id": step_id,
            "label": label,
            "status": "pending",
            "started_at": 0,
            "finished_at": 0,
            "message": "",
            "artifact_ids": [],
            "warning": False,
        }
        for step_id, label in PIPELINE_STEPS
    ]


def safe_pipeline_message(value, fallback="Stage details are available in local logs.") -> str:
    text = " ".join(str(value or "").split())[:240]
    return fallback if _PRIVATE_PATH.search(text) else text


def transition_pipeline_step(
    steps: list[dict],
    step_id: str,
    status: str,
    message: str = "",
    artifact_ids=None,
    warning: bool = False,
    now: int | None = None,
) -> list[dict]:
    if status not in PIPELINE_STATUSES:
        raise ValueError("invalid_pipeline_status")
    timestamp = int(time.time()) if now is None else int(now)
    updated = deepcopy(steps)
    for step in updated:
        if step.get("step_id") != step_id:
            continue
        if status == "running" and not step.get("started_at"):
            step["started_at"] = timestamp
        if status in {"passed", "warned", "failed", "skipped"}:
            step["finished_at"] = timestamp
            if not step.get("started_at") and status != "skipped":
                step["started_at"] = timestamp
        step["status"] = status
        step["message"] = safe_pipeline_message(message, "")
        step["artifact_ids"] = sorted({str(item) for item in (artifact_ids or []) if item})
        step["warning"] = bool(warning or status in {"warned", "failed"})
        return updated
    raise ValueError("unknown_pipeline_step")


def build_public_pipeline(profile: dict, steps, current_step="") -> dict:
    safe_steps = []
    if isinstance(steps, list):
        for source in steps:
            if not isinstance(source, dict):
                continue
            status = str(source.get("status") or "pending")
            if status not in PIPELINE_STATUSES:
                status = "pending"
            safe_steps.append(
                {
                    "step_id": str(source.get("step_id") or ""),
                    "label": str(source.get("label") or ""),
                    "status": status,
                    "started_at": int(source.get("started_at") or 0),
                    "finished_at": int(source.get("finished_at") or 0),
                    "message": safe_pipeline_message(source.get("message"), ""),
                    "artifact_ids": sorted(
                        {str(item) for item in (source.get("artifact_ids") or []) if item}
                    ),
                    "warning": bool(source.get("warning")),
                }
            )
    completed = sum(1 for step in safe_steps if step["status"] in {"passed", "warned", "skipped"})
    return {
        "profile_id": str((profile or {}).get("profile_id") or ""),
        "current_step": str(current_step or ""),
        "completed_steps": completed,
        "total_steps": len(safe_steps),
        "steps": safe_steps,
    }
