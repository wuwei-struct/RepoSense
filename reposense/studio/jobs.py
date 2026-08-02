import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from .analysis_profiles import get_analysis_profile, public_analysis_profile
from .pipeline_status import (
    build_pipeline_steps,
    build_public_pipeline,
    safe_pipeline_message,
    transition_pipeline_step,
)
from .review_pipeline import (
    PipelineContext,
    PipelineStageError,
    execute_review_pipeline,
)
from .workspace import WorkspaceManager


class PipelineCommandError(RuntimeError):
    def __init__(self, label, return_code):
        super().__init__(f"{label} failed with exit code {return_code}")
        self.label = label
        self.return_code = return_code


class JobManager:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace
        self.jobs = {}
        self.lock = threading.RLock()

    def start_run(
        self,
        project_id,
        ruleset=None,
        budget=None,
        specs=None,
        concept_graph=None,
        profile_id="quick_scan",
    ):
        del concept_graph  # Retained for backwards-compatible callers.
        profile = get_analysis_profile(profile_id)
        repo_path = self.workspace.get_project_path(project_id)
        repo_label = Path(repo_path).name or "Imported repository"
        run_id, run_dir = self.workspace.create_run(project_id)
        now = int(time.time())
        job_info = {
            "status": "queued",
            "phase": "queued",
            "logs": [],
            "logs_tail": [],
            "project_id": project_id,
            "repo_label": repo_label,
            "run_dir": run_dir,
            "start_time": now,
            "updated_at": now,
            "error": "",
            "log_path": os.path.join(run_dir, "logs.txt"),
            "output_paths": {"run_dir": run_dir},
            "profile": public_analysis_profile(profile["profile_id"]),
            "pipeline_steps": build_pipeline_steps(),
        }
        with self.lock:
            self.jobs[run_id] = job_info
        self._persist_state(run_id)
        self._append_log_file(run_id, "[INIT] queued")

        context = PipelineContext(
            profile_id=profile["profile_id"],
            python=sys.executable,
            repo_path=repo_path,
            run_dir=run_dir,
            ruleset_path=str(ruleset or profile["ruleset_path"]),
            budget_path=str(budget or profile["budget_path"]),
            specs_path=str(specs or profile["specs_path"]),
            gate_path=profile["gate_path"],
        )
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(run_id, context),
            daemon=True,
        )
        with self.lock:
            self.jobs[run_id]["thread"] = thread
        thread.start()
        return run_id

    def _append_log_file(self, run_id, line):
        try:
            with open(self.jobs[run_id]["log_path"], "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except Exception:
            pass

    def _state_snapshot(self, run_id):
        info = self.jobs[run_id]
        return {
            "run_id": run_id,
            "project_id": info["project_id"],
            "repo_label": info.get("repo_label", "Repository"),
            "status": info["status"],
            "phase": info["phase"],
            "created_at": int(info["start_time"]),
            "updated_at": int(info["updated_at"]),
            "error_message": info.get("error", ""),
            "log_path": info["log_path"],
            "output_paths": info.get("output_paths", {"run_dir": info["run_dir"]}),
            "stats": info.get("stats", {}),
            "profile": info.get("profile", {}),
            "pipeline": build_public_pipeline(
                info.get("profile", {}),
                info.get("pipeline_steps", []),
                info.get("phase", ""),
            ),
        }

    def _persist_state(self, run_id):
        try:
            with self.lock:
                if run_id not in self.jobs:
                    return
                snapshot = self._state_snapshot(run_id)
            self.workspace.write_run_state(run_id, snapshot)
        except Exception:
            pass

    def _log(self, run_id, message):
        with self.lock:
            if run_id not in self.jobs:
                return
            stamp = time.strftime("[%H:%M:%S] ", time.localtime())
            line = stamp + str(message)
            self.jobs[run_id]["logs"].append(line)
            self.jobs[run_id]["logs_tail"].append(line)
            self.jobs[run_id]["logs_tail"] = self.jobs[run_id]["logs_tail"][-400:]
            self.jobs[run_id]["updated_at"] = int(time.time())
        self._append_log_file(run_id, line)
        self._persist_state(run_id)

    def _update_step(self, run_id, step_id, status, message="", artifact_ids=None, warning=False):
        with self.lock:
            info = self.jobs[run_id]
            info["pipeline_steps"] = transition_pipeline_step(
                info["pipeline_steps"],
                step_id,
                status,
                message,
                artifact_ids,
                warning,
            )
            info["phase"] = step_id
            info["updated_at"] = int(time.time())
        if status in {"running", "warned", "failed"}:
            suffix = f": {message}" if message else ""
            self._log(run_id, f"{step_id} {status}{suffix}")
        else:
            self._persist_state(run_id)

    def _run_pipeline(self, run_id, context):
        try:
            with self.lock:
                self.jobs[run_id]["status"] = "running"
                self.jobs[run_id]["updated_at"] = int(time.time())
            self._log(run_id, "Review pipeline started")
            execute_review_pipeline(
                context,
                lambda step_id, label, command: self._run_cmd(run_id, step_id, label, command),
                lambda step_id, status, message, artifacts, warning: self._update_step(
                    run_id, step_id, status, message, artifacts, warning
                ),
            )
            with self.lock:
                self.jobs[run_id]["status"] = "completed"
                self.jobs[run_id]["phase"] = "done"
                self.jobs[run_id]["error"] = ""
                self.jobs[run_id]["updated_at"] = int(time.time())
                self.jobs[run_id]["output_paths"] = {
                    "run_dir": context.run_dir,
                    "sarif_path": os.path.join(context.run_dir, "exports", "report.sarif.json"),
                    "context_pack_dir": os.path.join(context.run_dir, "context_pack"),
                    "context_pack_zip": os.path.join(context.run_dir, "exports", "context_pack.zip"),
                    "quality_gate_path": os.path.join(context.run_dir, "quality_gate.json"),
                }
            self._log(run_id, "Review pipeline completed")
        except PipelineStageError as exc:
            message = safe_pipeline_message(exc.reason, "Stage failed; see local logs.")
            with self.lock:
                info = self.jobs[run_id]
                info["status"] = "failed"
                info["phase"] = exc.step_id
                info["error"] = f"{exc.step_id}: {message}"
                info["updated_at"] = int(time.time())
            try:
                self._update_step(run_id, exc.step_id, "failed", message, [], True)
            except ValueError:
                pass
            self._log(run_id, f"Pipeline stopped at {exc.step_id}")
        except Exception as exc:
            message = safe_pipeline_message(exc.__class__.__name__, "Pipeline failed; see local logs.")
            with self.lock:
                info = self.jobs[run_id]
                info["status"] = "failed"
                info["phase"] = "failed"
                info["error"] = message
                info["updated_at"] = int(time.time())
            self._log(run_id, "Review pipeline failed")

    def _run_cmd(self, run_id, step_id, label, command):
        self._log(run_id, f"Running {label}")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            close_fds=False,
            env=env,
        )
        try:
            if process.stdout:
                for line in process.stdout:
                    self._log(run_id, line.strip())
        finally:
            if process.stdout:
                process.stdout.close()
        process.wait()
        if process.returncode != 0:
            raise PipelineCommandError(label, process.returncode)

    def get_job_status(self, run_id):
        with self.lock:
            info = self.jobs.get(run_id)
            if not info:
                return None
            return {
                "run_id": run_id,
                "status": info.get("status"),
                "phase": info.get("phase"),
                "logs_tail": list(info.get("logs_tail", [])),
                "updated_at": info.get("updated_at", int(time.time())),
                "start_time": info.get("start_time", 0),
                "error_message": info.get("error", ""),
                "repo_label": info.get("repo_label", "Repository"),
                "profile": dict(info.get("profile", {})),
                "pipeline": build_public_pipeline(
                    info.get("profile", {}),
                    info.get("pipeline_steps", []),
                    info.get("phase", ""),
                ),
            }

    def get_all_jobs(self):
        with self.lock:
            return [
                {
                    "run_id": run_id,
                    "status": info["status"],
                    "phase": info["phase"],
                    "start_time": info["start_time"],
                    "updated_at": info.get("updated_at", info["start_time"]),
                    "repo_label": info.get("repo_label", "Repository"),
                    "profile": dict(info.get("profile", {})),
                    "pipeline": build_public_pipeline(
                        info.get("profile", {}),
                        info.get("pipeline_steps", []),
                        info.get("phase", ""),
                    ),
                }
                for run_id, info in self.jobs.items()
            ]
