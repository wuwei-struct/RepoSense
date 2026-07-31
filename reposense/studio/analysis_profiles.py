"""Stable Studio analysis profiles with public and internal views."""

from __future__ import annotations

from copy import deepcopy

from ..runtime_resources import get_presets_dir, get_rulesets_dir, get_specs_dir


DEFAULT_ANALYSIS_PROFILE = "full_review"

_PROFILES = {
    "full_review": {
        "profile_id": "full_review",
        "display_name": "Full Repository Review",
        "description": "Build the complete evidence-backed repository review workspace.",
        "recommended": True,
        "capabilities": {
            "permission_review": True,
            "code_health": True,
            "context_pack": True,
            "strict_verify": True,
        },
        "generated_outputs": [
            "Repository Review",
            "Human Review Required",
            "Code Health",
            "Permission and AuthZ",
            "Context Pack REVIEW",
            "Validation outputs",
        ],
        "ruleset": "specs_v2",
        "budget": "prod_lite.json",
        "gate": "prod_lite.json",
    },
    "quick_scan": {
        "profile_id": "quick_scan",
        "display_name": "Quick Scan",
        "description": "Build core facts, API and event graph outputs with a smaller review surface.",
        "recommended": False,
        "capabilities": {
            "permission_review": False,
            "code_health": False,
            "context_pack": True,
            "strict_verify": True,
        },
        "generated_outputs": [
            "Main HTML Report",
            "API and event graph facts",
            "Context Pack",
            "Validation outputs",
        ],
        "ruleset": "specs_v2",
        "budget": "prod_lite.json",
        "gate": "prod_lite.json",
    },
}


def _profile_or_raise(profile_id: str | None) -> dict:
    normalized = str(profile_id or DEFAULT_ANALYSIS_PROFILE).strip().lower()
    profile = _PROFILES.get(normalized)
    if profile is None:
        raise ValueError("unknown_analysis_profile")
    return profile


def get_analysis_profile(profile_id: str | None = None) -> dict:
    """Return the internal profile, including resolved runtime resource paths."""
    profile = deepcopy(_profile_or_raise(profile_id))
    profile["ruleset_path"] = str(get_rulesets_dir() / profile.pop("ruleset"))
    profile["budget_path"] = str(get_presets_dir() / profile.pop("budget"))
    profile["gate_path"] = str(get_presets_dir() / "gates" / profile.pop("gate"))
    profile["specs_path"] = str(get_specs_dir())
    return profile


def public_analysis_profile(profile_id: str | None = None) -> dict:
    """Return browser-safe profile metadata without local resource paths."""
    profile = deepcopy(_profile_or_raise(profile_id))
    for field in ("ruleset", "budget", "gate"):
        profile.pop(field, None)
    return profile


def list_public_analysis_profiles() -> list[dict]:
    return [public_analysis_profile(profile_id) for profile_id in ("full_review", "quick_scan")]
