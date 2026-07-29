"""Stable Studio metadata for known run artifacts.

The catalog describes product-facing artifact metadata only. Availability is
resolved separately for each run so a missing artifact never receives a URL.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Callable


CATEGORY_GROUPS = (
    {
        "group_id": "review",
        "display_name": "Review",
        "categories": ("review",),
        "default_expanded": True,
    },
    {
        "group_id": "backend",
        "display_name": "Backend & Side Effects",
        "categories": ("backend",),
        "default_expanded": False,
    },
    {
        "group_id": "transactions_database",
        "display_name": "Transactions & Database",
        "categories": ("transaction", "database"),
        "default_expanded": False,
    },
    {
        "group_id": "messaging",
        "display_name": "Queue & Messaging Reliability",
        "categories": ("messaging",),
        "default_expanded": False,
    },
    {
        "group_id": "code_health",
        "display_name": "Code Health",
        "categories": ("code_health",),
        "default_expanded": False,
    },
    {
        "group_id": "permission",
        "display_name": "Permission & AuthZ",
        "categories": ("permission",),
        "default_expanded": False,
    },
    {
        "group_id": "validation",
        "display_name": "Validation & Evidence",
        "categories": ("validation",),
        "default_expanded": True,
    },
    {
        "group_id": "context",
        "display_name": "Context Pack & AI Handoff",
        "categories": ("context",),
        "default_expanded": False,
    },
    {
        "group_id": "learn",
        "display_name": "Learn",
        "categories": ("learn",),
        "default_expanded": False,
    },
    {
        "group_id": "advanced_raw",
        "display_name": "Advanced / Raw Artifacts",
        "categories": ("overview", "raw"),
        "default_expanded": False,
    },
)


# Keep artifact names and categories in one server-side source of truth. The
# browser receives this metadata from the run API instead of maintaining a copy.
ARTIFACT_CATALOG = (
    {
        "artifact_id": "repository_review_report",
        "relative_path": "repository_review_report.md",
        "display_name": "Repository Review Report",
        "description": "Start here for the evidence-guided review decision and risk summary.",
        "category": "review",
        "format": "markdown",
        "priority": "primary",
        "audience": "human",
        "recommended_action": "Read the review decision, limitations, and top risks first.",
        "generated_when": "Repository Review is generated",
        "kind": "repository_review",
        "is_primary": True,
        "sort_order": 10,
        "review_legacy_key": "repository_review_report",
    },
    {
        "artifact_id": "human_review_required",
        "relative_path": "human_review_required.md",
        "display_name": "Human Review Required",
        "description": "Focused decisions that need source and business-context review.",
        "category": "review",
        "format": "markdown",
        "priority": "primary",
        "audience": "human",
        "recommended_action": "Assign each item to the relevant owner and confirm the evidence.",
        "generated_when": "Repository Review is generated",
        "kind": "repository_review",
        "is_primary": True,
        "sort_order": 20,
        "review_legacy_key": "human_review_required",
    },
    {
        "artifact_id": "main_html_report",
        "relative_path": "report.html",
        "display_name": "Main HTML Report",
        "description": "Interactive overview of analysis facts, findings, and evidence links.",
        "category": "overview",
        "format": "html",
        "priority": "primary",
        "audience": "mixed",
        "recommended_action": "Use this for a broad visual overview before opening raw artifacts.",
        "generated_when": "A CI run completes",
        "kind": "report",
        "is_primary": True,
        "sort_order": 30,
    },
    {
        "artifact_id": "context_pack_review_readme",
        "relative_path": "context_pack/REVIEW/README.md",
        "display_name": "Context Pack REVIEW",
        "description": "Reading order and available review handoff artifacts for humans and AI tools.",
        "category": "context",
        "format": "markdown",
        "priority": "primary",
        "audience": "mixed",
        "recommended_action": "Use this as the entry point for a constrained review handoff.",
        "generated_when": "Context Pack REVIEW is generated",
        "kind": "context_pack",
        "is_primary": True,
        "sort_order": 40,
        "review_legacy_key": "review_context",
    },
    {
        "artifact_id": "backend_verifier_report",
        "relative_path": "backend_verifier_report.md",
        "display_name": "Backend Verifier Report",
        "description": "Backend side effects, transactions, queue, cache, and API signals.",
        "category": "backend",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review side-effect and coverage limitations before changing backend code.",
        "generated_when": "Backend verifier report is generated",
        "kind": "backend_verifier_report",
        "is_primary": False,
        "sort_order": 50,
        "review_legacy_key": "backend_verifier_report",
    },
    {
        "artifact_id": "code_health_summary",
        "relative_path": "code_health_summary.json",
        "display_name": "Code Health Summary",
        "description": "Counts, severity, top files, and experimental health-score context.",
        "category": "code_health",
        "format": "json",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review actionable findings before using the raw finding list.",
        "generated_when": "Code Health scan is generated",
        "kind": "code_health",
        "is_primary": False,
        "sort_order": 60,
        "review_legacy_key": "code_health_summary",
    },
    {
        "artifact_id": "maintainability_risks",
        "relative_path": "maintainability_risks.json",
        "display_name": "Maintainability Risks",
        "description": "Actionable Code Health risks retained for primary review.",
        "category": "code_health",
        "format": "json",
        "priority": "advanced",
        "audience": "human",
        "recommended_action": "Open when you need the individual Code Health risk records.",
        "generated_when": "Code Health scan is generated",
        "kind": "code_health",
        "is_primary": False,
        "sort_order": 70,
        "review_legacy_key": "maintainability_risks",
    },
    {
        "artifact_id": "permission_risk_report",
        "relative_path": "permission_risk_report.md",
        "display_name": "Permission Risk Report",
        "description": "Permission findings, effective guard context, and review limitations.",
        "category": "permission",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review before relying on route-level authorization assumptions.",
        "generated_when": "Permission Auditor is generated",
        "kind": "permission_audit",
        "is_primary": False,
        "sort_order": 80,
        "review_legacy_key": "permission_risk_report",
    },
    {
        "artifact_id": "human_permission_review_required",
        "relative_path": "human_permission_review_required.md",
        "display_name": "Human Permission Review Required",
        "description": "Permission-specific decisions that static analysis cannot confirm.",
        "category": "permission",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Confirm protection requirements with the backend or security owner.",
        "generated_when": "Permission Auditor is generated",
        "kind": "permission_audit",
        "is_primary": False,
        "sort_order": 90,
        "review_legacy_key": "human_permission_review_required",
    },
    {
        "artifact_id": "authz_matrix_report",
        "relative_path": "authz_matrix_report.md",
        "display_name": "AuthZ Matrix Report",
        "description": "Observed and contract-backed authorization matrix comparison.",
        "category": "permission",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Confirm inferred observations against the project authorization contract.",
        "generated_when": "AuthZ Matrix is generated",
        "kind": "authz_matrix",
        "is_primary": False,
        "sort_order": 100,
        "review_legacy_key": "authz_matrix_report",
    },
    {
        "artifact_id": "authz_negative_test_plan",
        "relative_path": "authz_negative_test_plan.md",
        "display_name": "AuthZ Negative Test Plan",
        "description": "Suggested negative authorization tests derived from observed evidence.",
        "category": "permission",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Use as a test-planning aid, not as proof that tests exist.",
        "generated_when": "AuthZ Matrix is generated",
        "kind": "authz_matrix",
        "is_primary": False,
        "sort_order": 110,
        "review_legacy_key": "authz_negative_test_plan",
    },
    {
        "artifact_id": "transaction_correlation_summary",
        "relative_path": "transaction_correlation_summary.json",
        "display_name": "Transaction Correlation Summary",
        "description": "Explicit, partial, uncovered, and unresolved transaction coverage evidence.",
        "category": "transaction",
        "format": "json",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review correlation limitations before classifying a write as transactional.",
        "generated_when": "Transaction correlation is generated",
        "kind": "transaction_correlation",
        "is_primary": False,
        "sort_order": 120,
    },
    {
        "artifact_id": "typeorm_db_summary",
        "relative_path": "typeorm_db_summary.json",
        "display_name": "TypeORM DB Summary",
        "description": "TypeORM reads, writes, transactions, receiver kinds, and unresolved SQL.",
        "category": "database",
        "format": "json",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Use for TypeORM coverage context; it is not a data-consistency proof.",
        "generated_when": "TypeORM DB analysis is generated",
        "kind": "typeorm_db_operation",
        "is_primary": False,
        "sort_order": 130,
    },
    {
        "artifact_id": "queue_cache_validation",
        "relative_path": "queue_cache_validation.md",
        "display_name": "Queue & Cache Validation",
        "description": "Queue producer-consumer and cache observation validation for a smoke case.",
        "category": "messaging",
        "format": "markdown",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review unmatched channels and evidence limitations before calibration.",
        "generated_when": "Queue and cache validation is generated",
        "kind": "queue_cache_validation",
        "is_primary": False,
        "sort_order": 140,
    },
    {
        "artifact_id": "queue_reliability_summary",
        "relative_path": "queue_reliability_summary.json",
        "display_name": "Queue Reliability Summary",
        "description": "Matched channels, retry observations, side effects, and idempotency evidence.",
        "category": "messaging",
        "format": "json",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Review retry and consumer-guard evidence before relying on message handling assumptions.",
        "generated_when": "Queue reliability correlation is generated",
        "kind": "queue_reliability",
        "is_primary": False,
        "sort_order": 150,
    },
    {
        "artifact_id": "queue_reliability_risks",
        "relative_path": "queue_reliability_risks.json",
        "display_name": "Queue Reliability Risks",
        "description": "Suspected retry and consumer-side-effect risks requiring confirmation.",
        "category": "messaging",
        "format": "json",
        "priority": "advanced",
        "audience": "human",
        "recommended_action": "Confirm consumer behavior and idempotency controls in source and runtime configuration.",
        "generated_when": "Queue reliability correlation is generated",
        "kind": "queue_reliability",
        "is_primary": False,
        "sort_order": 160,
    },
    {
        "artifact_id": "route_guard_summary",
        "relative_path": "route_guard_summary.json",
        "display_name": "Route Guard Correlation Summary",
        "description": "Method, controller, and global guard observations correlated with routes.",
        "category": "permission",
        "format": "json",
        "priority": "advanced",
        "audience": "human",
        "recommended_action": "Use as observed guard evidence, not as a complete authorization proof.",
        "generated_when": "Route Guard Correlation is generated",
        "kind": "route_guard_correlation",
        "is_primary": False,
        "sort_order": 170,
    },
    {
        "artifact_id": "review_context_summary",
        "relative_path": "review_context_summary.json",
        "display_name": "Review Context Summary",
        "description": "Route intent and non-production file calibration context.",
        "category": "review",
        "format": "json",
        "priority": "advanced",
        "audience": "human",
        "recommended_action": "Check context classifications before interpreting calibrated findings.",
        "generated_when": "Review context calibration is generated",
        "kind": "review_context",
        "is_primary": False,
        "sort_order": 180,
    },
    {
        "artifact_id": "quality_gate",
        "relative_path": "quality_gate.json",
        "display_name": "Quality Gate",
        "description": "Gate status, violations, baseline compatibility, and remediation hints.",
        "category": "validation",
        "format": "json",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Address failed or warned gate signals before relying on downstream outputs.",
        "generated_when": "Quality gate is generated",
        "kind": "quality_gate",
        "is_primary": False,
        "sort_order": 190,
    },
    {
        "artifact_id": "run_manifest",
        "relative_path": "run_manifest.json",
        "display_name": "Run Manifest",
        "description": "Run-relative inventory of generated artifacts and their metadata.",
        "category": "validation",
        "format": "json",
        "priority": "advanced",
        "audience": "tooling",
        "recommended_action": "Use to confirm which artifacts were actually generated for this run.",
        "generated_when": "Run manifest is generated",
        "kind": "run_manifest",
        "is_primary": False,
        "sort_order": 200,
    },
    {
        "artifact_id": "sarif_report",
        "relative_path": "exports/report.sarif.json",
        "display_name": "SARIF Report",
        "description": "Machine-readable static-analysis findings for compatible tooling.",
        "category": "raw",
        "format": "sarif",
        "priority": "advanced",
        "audience": "tooling",
        "recommended_action": "Import into SARIF-compatible tooling when machine-readable findings are needed.",
        "generated_when": "Patch exports are generated",
        "kind": "sarif",
        "is_primary": False,
        "sort_order": 210,
    },
    {
        "artifact_id": "context_pack_zip",
        "relative_path": "exports/context_pack.zip",
        "display_name": "Context Pack ZIP",
        "description": "Portable Context Pack archive for offline handoff.",
        "category": "context",
        "format": "zip",
        "priority": "secondary",
        "audience": "mixed",
        "recommended_action": "Use for a portable handoff; inspect its manifest before broad changes.",
        "generated_when": "Context Pack export is generated",
        "kind": "context_pack",
        "is_primary": False,
        "sort_order": 220,
    },
    {
        "artifact_id": "ai_maintenance_constraints",
        "relative_path": "context_pack/REVIEW/ai_maintenance_constraints.md",
        "display_name": "AI Maintenance Constraints",
        "description": "Evidence-first maintenance constraints for a scoped AI-assisted handoff.",
        "category": "context",
        "format": "markdown",
        "priority": "secondary",
        "audience": "ai",
        "recommended_action": "Read before asking an AI assistant to make maintenance changes.",
        "generated_when": "Context Pack REVIEW is generated",
        "kind": "context_pack",
        "is_primary": False,
        "sort_order": 230,
        "review_legacy_key": "ai_maintenance_constraints",
    },
    {
        "artifact_id": "learn_index",
        "relative_path": "learn_site/index.html",
        "url_path": "learn/index.html",
        "display_name": "Learn",
        "description": "Local learning view generated from available run facts.",
        "category": "learn",
        "format": "html",
        "priority": "secondary",
        "audience": "human",
        "recommended_action": "Open for the local learning-oriented presentation of generated outputs.",
        "generated_when": "Learn site is generated",
        "kind": "learn",
        "is_primary": False,
        "sort_order": 240,
    },
    {
        "artifact_id": "review_risk_matrix",
        "relative_path": "review_risk_matrix.json",
        "display_name": "Review Risk Matrix",
        "description": "Structured review decision, risk counts, and top-risk metadata.",
        "category": "raw",
        "format": "json",
        "priority": "advanced",
        "audience": "tooling",
        "recommended_action": "Open when structured review-decision data is required.",
        "generated_when": "Repository Review is generated",
        "kind": "repository_review",
        "is_primary": False,
        "sort_order": 250,
        "review_legacy_key": "review_risk_matrix",
    },
)


def _is_valid_relative_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def validate_catalog() -> list[str]:
    """Return deterministic catalog-contract errors for unit tests and startup callers."""
    errors = []
    ids = set()
    group_categories = {
        category for group in CATEGORY_GROUPS for category in group["categories"]
    }
    for entry in ARTIFACT_CATALOG:
        artifact_id = entry.get("artifact_id")
        if not artifact_id or artifact_id in ids:
            errors.append(f"duplicate_or_missing_artifact_id:{artifact_id}")
        ids.add(artifact_id)
        if not _is_valid_relative_path(str(entry.get("relative_path") or "")):
            errors.append(f"invalid_relative_path:{artifact_id}")
        if not _is_valid_relative_path(str(entry.get("url_path") or entry.get("relative_path") or "")):
            errors.append(f"invalid_url_path:{artifact_id}")
        if entry.get("category") not in group_categories:
            errors.append(f"unknown_category:{artifact_id}")
        if entry.get("format") not in {"html", "markdown", "json", "yaml", "sarif", "zip", "other"}:
            errors.append(f"invalid_format:{artifact_id}")
        if entry.get("priority") not in {"primary", "secondary", "advanced"}:
            errors.append(f"invalid_priority:{artifact_id}")
        if entry.get("audience") not in {"human", "ai", "tooling", "mixed"}:
            errors.append(f"invalid_audience:{artifact_id}")
    return sorted(errors)


def review_artifact_specs() -> tuple[dict, ...]:
    """Return catalog entries used by the legacy review metadata response."""
    return tuple(entry for entry in ARTIFACT_CATALOG if entry.get("review_legacy_key"))


def build_artifact_presentation(
    run_id: str,
    run_dir: str,
    url_builder: Callable[[str, str], str],
) -> dict:
    """Return available groups and meaningful missing capabilities for one run."""
    from pathlib import Path

    run_root = Path(run_dir)
    available_by_category: dict[str, list[dict]] = {}
    missing_by_category: dict[str, list[dict]] = {}
    for entry in ARTIFACT_CATALOG:
        item = {
            key: entry[key]
            for key in (
                "artifact_id",
                "relative_path",
                "display_name",
                "description",
                "category",
                "format",
                "priority",
                "audience",
                "recommended_action",
                "generated_when",
                "kind",
                "is_primary",
                "sort_order",
            )
        }
        path = run_root.joinpath(*PurePosixPath(entry["relative_path"]).parts)
        item["available"] = path.is_file()
        if item["available"]:
            item["url"] = url_builder(run_id, entry.get("url_path") or entry["relative_path"])
            available_by_category.setdefault(item["category"], []).append(item)
        else:
            missing_by_category.setdefault(item["category"], []).append(item)

    groups = []
    for group in CATEGORY_GROUPS:
        items = [
            item
            for category in group["categories"]
            for item in available_by_category.get(category, [])
        ]
        if not items:
            continue
        groups.append(
            {
                "group_id": group["group_id"],
                "display_name": group["display_name"],
                "default_expanded": bool(group["default_expanded"]),
                "artifacts": sorted(items, key=lambda item: (item["sort_order"], item["artifact_id"])),
            }
        )

    missing_capabilities = []
    for group in CATEGORY_GROUPS:
        if group["group_id"] in {"advanced_raw", "learn"}:
            continue
        if any(available_by_category.get(category) for category in group["categories"]):
            continue
        missing = [
            item
            for category in group["categories"]
            for item in missing_by_category.get(category, [])
        ]
        if missing:
            missing_capabilities.append(
                {
                    "group_id": group["group_id"],
                    "display_name": group["display_name"],
                    "message": f"{group['display_name']} not generated for this run.",
                    "generated_when": sorted(
                        {item["generated_when"] for item in missing}
                    ),
                }
            )

    primary = sorted(
        [
            artifact
            for group in groups
            for artifact in group["artifacts"]
            if artifact["is_primary"]
        ],
        key=lambda item: (item["sort_order"], item["artifact_id"]),
    )[:4]
    return {
        "artifact_groups": groups,
        "recommended_artifacts": primary,
        "missing_capabilities": missing_capabilities,
    }
