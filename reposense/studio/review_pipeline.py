"""Controlled Studio review pipeline built from existing RepoSense entrypoints."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class PipelineContext:
    profile_id: str
    python: str
    repo_path: str
    run_dir: str
    ruleset_path: str
    budget_path: str
    specs_path: str
    gate_path: str


@dataclass(frozen=True)
class PipelineStage:
    step_id: str
    commands: tuple[tuple[str, tuple[str, ...]], ...] = field(default_factory=tuple)
    action: str = ""
    required_artifacts: tuple[str, ...] = field(default_factory=tuple)
    optional_artifacts: tuple[str, ...] = field(default_factory=tuple)
    artifact_ids: tuple[str, ...] = field(default_factory=tuple)
    skipped: bool = False


class PipelineStageError(RuntimeError):
    def __init__(self, step_id: str, reason: str):
        super().__init__(reason)
        self.step_id = step_id
        self.reason = reason


def _cmd(context: PipelineContext, *args: str) -> tuple[str, ...]:
    return (context.python, "-m", "reposense", *args)


def build_review_pipeline(context: PipelineContext) -> list[PipelineStage]:
    full = context.profile_id == "full_review"
    contract = Path(context.repo_path) / "reposense.authz.yaml"
    matrix_args = [
        "authz", "matrix", context.run_dir, "--repo", context.repo_path, "--json", "--markdown"
    ]
    if contract.is_file():
        matrix_args.extend(["--contract", str(contract)])

    stages = [
        PipelineStage("preparing", action="prepare"),
        PipelineStage(
            "scanning_facts",
            commands=(("Base repository scan", _cmd(
                context,
                "scan", context.repo_path,
                "--out", context.run_dir,
                "--ruleset", context.ruleset_path,
                "--budget", context.budget_path,
                "--specs", context.specs_path,
            )),),
            required_artifacts=("report.json", "coverage.json"),
            artifact_ids=("main_html_report",),
        ),
        PipelineStage(
            "building_event_graph",
            action="validate_artifacts",
            required_artifacts=("event_graph.json", "api_surface.json"),
            artifact_ids=("main_html_report",),
        ),
        PipelineStage(
            "detecting_patterns",
            commands=(
                ("Pattern analysis", _cmd(context, "ai", "patterns", context.run_dir, "--json")),
                ("Grounded AI summary", _cmd(context, "ai", "summary", context.run_dir, "--json", "--markdown")),
                ("Grounded AI risks", _cmd(context, "ai", "risks", context.run_dir, "--json", "--markdown")),
            ) if full else (),
            required_artifacts=("patterns.json", "pattern_summary.json", "ai_summary.md") if full else (),
            skipped=not full,
        ),
        PipelineStage(
            "analyzing_code_health",
            commands=(("Code Health review", _cmd(
                context, "health", "scan", context.run_dir, "--repo", context.repo_path, "--json", "--markdown"
            )),) if full else (),
            required_artifacts=("code_health_summary.json", "maintainability_risks.json") if full else (),
            artifact_ids=("code_health_summary", "maintainability_risks"),
            skipped=not full,
        ),
        PipelineStage(
            "reviewing_permissions",
            commands=(
                ("Permission review", _cmd(
                    context, "authz", "scan", context.run_dir, "--repo", context.repo_path, "--json", "--markdown"
                )),
                ("AuthZ matrix", _cmd(context, *matrix_args)),
            ) if full else (),
            required_artifacts=("permission_risks.json", "authz_matrix_diff.json") if full else (),
            artifact_ids=("permission_risk_report", "authz_matrix_report", "authz_negative_test_plan"),
            skipped=not full,
        ),
        PipelineStage(
            "correlating_transactions",
            action="validate_artifacts",
            optional_artifacts=("transaction_correlation_summary.json", "typeorm_db_summary.json"),
            artifact_ids=("transaction_correlation_summary", "typeorm_db_summary"),
        ),
        PipelineStage(
            "reviewing_queue_reliability",
            action="validate_artifacts",
            optional_artifacts=("queue_reliability_summary.json",),
            artifact_ids=("queue_reliability_summary", "queue_reliability_risks"),
        ),
        PipelineStage(
            "building_repository_review",
            commands=(
                ("Backend verifier", _cmd(context, "backend", "report", context.run_dir, "--json", "--markdown")),
                ("Repository Review", _cmd(context, "review", "report", context.run_dir, "--json", "--markdown")),
            ) if full else (),
            required_artifacts=(
                "backend_verifier_report.json",
                "repository_review_report.json",
                "review_risk_matrix.json",
                "human_review_required.md",
            ) if full else (),
            artifact_ids=("backend_verifier_report", "repository_review_report", "human_review_required"),
            skipped=not full,
        ),
        PipelineStage(
            "building_context_pack",
            action="context_pack",
            required_artifacts=(
                "context_pack/README.md",
                "context_pack/REVIEW/README.md",
                "exports/context_pack.zip",
            ) if full else ("context_pack/README.md", "exports/context_pack.zip"),
            artifact_ids=("context_pack_review_readme", "ai_maintenance_constraints", "context_pack_zip"),
        ),
        PipelineStage(
            "strict_verification",
            commands=(
                ("SARIF export", _cmd(
                    context, "export", "sarif", context.run_dir,
                    "--out", os.path.join(context.run_dir, "exports", "report.sarif.json")
                )),
                ("Run manifest", _cmd(context, "run", "manifest", context.run_dir, "--json")),
                ("Strict verification", _cmd(context, "verify", context.run_dir, "--json", "--strict")),
            ),
            required_artifacts=("exports/report.sarif.json", "run_manifest.json"),
            artifact_ids=("sarif_report", "run_manifest"),
        ),
        PipelineStage(
            "quality_gate",
            commands=(("Quality gate", _cmd(
                context, "gate", context.run_dir, "--gate", context.gate_path, "--json"
            )),),
            required_artifacts=("quality_gate.json",),
            artifact_ids=("quality_gate",),
        ),
        PipelineStage(
            "finalizing",
            commands=(
                ("Concept graph", _cmd(
                    context, "specs", "graph", "build", "--specs", context.specs_path,
                    "--out", os.path.join(context.run_dir, "concepts.json")
                )),
                ("Learn site", _cmd(
                    context, "learn", "build", context.run_dir,
                    "--out", os.path.join(context.run_dir, "learn_site"),
                    "--concept-graph", os.path.join(context.run_dir, "concepts.json")
                )),
                ("SARIF export", _cmd(
                    context, "export", "sarif", context.run_dir,
                    "--out", os.path.join(context.run_dir, "exports", "report.sarif.json")
                )),
                ("Patch exports", _cmd(context, "patch", "exports", context.run_dir)),
                ("Run manifest", _cmd(context, "run", "manifest", context.run_dir, "--json")),
            ),
            required_artifacts=(
                "learn_site/index.html",
                "exports/report.sarif.json",
                "run_manifest.json",
            ),
            artifact_ids=("learn_index", "sarif_report", "run_manifest"),
        ),
    ]
    return stages


def _run_internal_action(action: str, context: PipelineContext) -> None:
    if action in {"", "prepare", "validate_artifacts"}:
        return
    if action == "context_pack":
        if context.profile_id == "full_review":
            from ..context_pack import build_context_pack, zip_context_pack

            build_context_pack(context.run_dir)
            zip_context_pack(context.run_dir)
            return
        from ..context_pack import run_context_pack

        run_context_pack(
            context.run_dir,
            os.path.join(context.run_dir, "context_pack"),
            zip=True,
        )
        source_zip = os.path.join(context.run_dir, "context_pack.zip")
        target_zip = os.path.join(context.run_dir, "exports", "context_pack.zip")
        if os.path.isfile(source_zip):
            os.makedirs(os.path.dirname(target_zip), exist_ok=True)
            os.replace(source_zip, target_zip)
        return
    raise ValueError("unknown_pipeline_action")


def _artifact_state(run_dir: str, paths: tuple[str, ...]) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for relative_path in paths:
        path = Path(run_dir).joinpath(*Path(relative_path).parts)
        (present if path.exists() else missing).append(relative_path)
    return present, missing


def execute_review_pipeline(
    context: PipelineContext,
    run_command: Callable[[str, str, tuple[str, ...]], None],
    update_step: Callable[..., None],
    run_internal: Callable[[str, PipelineContext], None] | None = None,
) -> None:
    internal = run_internal or _run_internal_action
    for stage in build_review_pipeline(context):
        if stage.skipped:
            update_step(stage.step_id, "skipped", "Not included in this analysis profile.", stage.artifact_ids, False)
            continue
        update_step(stage.step_id, "running", "", stage.artifact_ids, False)
        try:
            for label, command in stage.commands:
                run_command(stage.step_id, label, command)
            internal(stage.action, context)
            _, required_missing = _artifact_state(context.run_dir, stage.required_artifacts)
            if required_missing:
                raise PipelineStageError(stage.step_id, "required_artifact_missing")
            present_optional, missing_optional = _artifact_state(context.run_dir, stage.optional_artifacts)
            if stage.optional_artifacts and not present_optional:
                update_step(
                    stage.step_id,
                    "warned",
                    "Capability artifacts were not generated for this repository.",
                    stage.artifact_ids,
                    True,
                )
                continue
            message = ""
            status = "passed"
            warning = False
            if stage.step_id == "quality_gate":
                try:
                    gate = json.loads(Path(context.run_dir, "quality_gate.json").read_text(encoding="utf-8"))
                    if gate.get("status") == "warn":
                        status = "warned"
                        warning = True
                        message = "Quality gate completed with warnings."
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    raise PipelineStageError(stage.step_id, "quality_gate_malformed")
            elif missing_optional:
                status = "warned"
                warning = True
                message = "Some optional capability artifacts were not generated."
            update_step(stage.step_id, status, message, stage.artifact_ids, warning)
        except PipelineStageError:
            raise
        except Exception as exc:
            raise PipelineStageError(stage.step_id, exc.__class__.__name__) from exc
