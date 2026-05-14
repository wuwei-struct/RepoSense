import threading
import subprocess
import os
import sys
import time
import json
import zipfile
from .workspace import WorkspaceManager

class JobManager:
    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace
        self.jobs = {}  # run_id -> {status, thread, logs, phase}
        self.lock = threading.RLock()

    def start_run(self, project_id, ruleset, budget, specs, concept_graph=None):
        run_id, run_dir = self.workspace.create_run(project_id)
        repo_path = self.workspace.get_project_path(project_id)
        
        job_info = {
            "status": "queued",
            "phase": "queued",
            "logs": [],
            "logs_tail": [],
            "project_id": project_id,
            "run_dir": run_dir,
            "start_time": time.time(),
            "updated_at": int(time.time()),
            "error": "",
            "log_path": os.path.join(run_dir, "logs.txt"),
            "output_paths": {"run_dir": run_dir},
        }
        
        with self.lock:
            self.jobs[run_id] = job_info
        try:
            with open(job_info["log_path"], "a", encoding="utf-8") as f:
                f.write("[INIT] queued\n")
        except Exception:
            pass

        t = threading.Thread(target=self._run_pipeline, args=(run_id, repo_path, run_dir, ruleset, budget, specs, concept_graph))
        t.start()
        return run_id

    def _log(self, run_id, msg):
        with self.lock:
            if run_id in self.jobs:
                ts = time.strftime("[%H:%M:%S] ", time.localtime())
                line = ts + msg
                self.jobs[run_id]["logs"].append(line)
                self.jobs[run_id]["logs_tail"].append(line)
                if len(self.jobs[run_id]["logs_tail"]) > 400:
                    self.jobs[run_id]["logs_tail"] = self.jobs[run_id]["logs_tail"][-400:]
                self.jobs[run_id]["updated_at"] = int(time.time())
                try:
                    with open(self.jobs[run_id]["log_path"], "a", encoding="utf-8") as f:
                        f.write(line + "\n")
                except Exception:
                    pass
                try:
                    state = {
                        "run_id": run_id,
                        "project_id": self.jobs[run_id]["project_id"],
                        "status": self.jobs[run_id]["status"],
                        "phase": self.jobs[run_id]["phase"],
                        "created_at": int(self.jobs[run_id]["start_time"]),
                        "updated_at": self.jobs[run_id]["updated_at"],
                        "error_message": self.jobs[run_id].get("error", ""),
                        "log_path": self.jobs[run_id]["log_path"],
                        "output_paths": self.jobs[run_id].get("output_paths", {"run_dir": self.jobs[run_id]["run_dir"]}),
                        "stats": self.jobs[run_id].get("stats", {}),
                    }
                    self.workspace.write_run_state(run_id, state)
                except Exception:
                    pass

    def _set_phase(self, run_id, phase):
        with self.lock:
            if run_id in self.jobs:
                self.jobs[run_id]["phase"] = phase
        self._log(run_id, f"Phase changed to: {phase}")

    def _run_pipeline(self, run_id, repo_path, run_dir, ruleset, budget, specs, concept_graph):
        try:
            with self.lock:
                if run_id in self.jobs:
                    self.jobs[run_id]["status"] = "running"
                    self.jobs[run_id]["updated_at"] = int(time.time())
            self._log(run_id, "Pipeline started")
            # 1. Scan
            self._set_phase(run_id, "scan")
            cmd_scan = [
                sys.executable, "-m", "reposense", "scan", repo_path,
                "--out", run_dir,
                "--ruleset", ruleset,
                "--budget", budget
            ]
            if specs:
                cmd_scan.extend(["--specs", specs])
            
            self._run_cmd(run_id, cmd_scan)
            cov_path = os.path.join(run_dir, "coverage.json")
            with self.lock:
                self.jobs[run_id].setdefault("output_paths", {"run_dir": run_dir})
                self.jobs[run_id]["output_paths"]["coverage_path"] = cov_path
            try:
                if os.path.exists(cov_path):
                    with open(cov_path, "r", encoding="utf-8") as f:
                        cov = json.load(f)
                    with self.lock:
                        self.jobs[run_id]["stats"] = {"coverage": cov}
            except Exception:
                pass

            # 2. Verify
            self._set_phase(run_id, "verify")
            cmd_verify = [
                sys.executable, "-m", "reposense", "verify", run_dir, "--json"
            ]
            self._run_cmd(run_id, cmd_verify)

            # 3. Learn
            self._set_phase(run_id, "learn")
            learn_out = os.path.join(run_dir, "learn_site")
            # Ensure concept graph path
            concept_graph_path = concept_graph
            if not concept_graph_path:
                concept_graph_path = os.path.join(run_dir, "concepts.json")
                if not os.path.exists(concept_graph_path):
                    if not specs:
                        raise Exception("Learn build requires --concept-graph. Provide concept_graph or specs.")
                    cmd_graph = [
                        sys.executable, "-m", "reposense", "specs", "graph", "build",
                        "--specs", specs,
                        "--out", concept_graph_path
                    ]
                    self._run_cmd(run_id, cmd_graph)
            cmd_learn = [
                sys.executable, "-m", "reposense", "learn", "build", run_dir,
                "--out", learn_out,
                "--concept-graph", concept_graph_path
            ]
            self._run_cmd(run_id, cmd_learn)

            # 4. Export
            self._set_phase(run_id, "export")
            exports_dir = os.path.join(run_dir, "exports")
            try:
                os.makedirs(exports_dir, exist_ok=True)
            except Exception:
                pass
            sarif_path = os.path.join(exports_dir, "report.sarif.json")
            cmd_sarif = [
                sys.executable, "-m", "reposense", "export", "sarif", run_dir, "--out", sarif_path
            ]
            self._run_cmd(run_id, cmd_sarif)

            context_dir = os.path.join(run_dir, "context_pack")
            cmd_ctx = [
                sys.executable, "-m", "reposense", "context", "pack", run_dir, "--out", context_dir
            ]
            self._run_cmd(run_id, cmd_ctx)

            # optional zip
            context_zip = os.path.join(exports_dir, "context_pack.zip")
            try:
                with zipfile.ZipFile(context_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for base, _, files in os.walk(context_dir):
                        for f in files:
                            p = os.path.join(base, f)
                            rel = os.path.relpath(p, context_dir).replace("\\", "/")
                            zf.write(p, arcname=rel)
            except Exception as e:
                self._log(run_id, f"Context pack zip failed: {e}")
                # still proceed; export is considered required, but zip optional

            # update output paths
            with self.lock:
                self.jobs[run_id]["output_paths"] = {
                    "run_dir": run_dir,
                    "sarif_path": sarif_path,
                    "context_pack_dir": context_dir,
                    "context_pack_zip": context_zip,
                }
            self._log(run_id, "Export completed")
            # hard checks: export must exist and be non-trivial
            try:
                if (not os.path.exists(sarif_path)) or (os.path.getsize(sarif_path) < 200):
                    raise Exception("export_sarif_missing_or_too_small")
                if (not os.path.isdir(context_dir)) or (not os.path.exists(os.path.join(context_dir, "context_manifest.json"))):
                    raise Exception("context_pack_missing_or_invalid")
                if (not os.path.exists(context_zip)) or (os.path.getsize(context_zip) < 200):
                    raise Exception("context_pack_zip_missing_or_too_small")
            except Exception as e:
                raise Exception(f"Export validation failed: {e}")

            # 5. Quality Gate
            self._set_phase(run_id, "gate")
            qpath = ""
            gate_status = "N/A"
            try:
                from ..quality_gate import load_gate_config, collect_metrics, evaluate, write_quality_gate
                cfg = load_gate_config(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "presets", "gates", "prod_lite.json"))
                obj = evaluate(collect_metrics(run_dir), cfg)
                qpath = write_quality_gate(run_dir, obj)
                gate_status = obj.get("status", "N/A")
            except Exception as e:
                self._log(run_id, f"Gate failed to run: {e}")

            # 6. Post Gate Patch
            self._set_phase(run_id, "post_gate_patch")
            try:
                cmd_patch = [sys.executable, "-m", "reposense", "patch", "exports", run_dir]
                self._run_cmd(run_id, cmd_patch)
                with self.lock:
                    self.jobs[run_id]["output_paths"]["patched_at"] = int(time.time())
                # build run manifest
                try:
                    from ..run_manifest import build_run_manifest
                    build_run_manifest(run_dir, write=True)
                except Exception as e:
                    self._log(run_id, f"Run manifest build failed: {e}")
            except Exception as e:
                self._log(run_id, f"Post gate patch failed: {e}")

            with self.lock:
                self.jobs[run_id]["output_paths"]["quality_gate_path"] = qpath
                if gate_status == "fail":
                    self.jobs[run_id]["status"] = "failed"
                    self.jobs[run_id]["phase"] = "failed"
                    self.jobs[run_id]["error"] = "quality_gate_fail"
                else:
                    self.jobs[run_id]["status"] = "completed"
                    self.jobs[run_id]["phase"] = "done"
                self.jobs[run_id]["updated_at"] = int(time.time())
            self._log(run_id, f"Pipeline completed, gate={gate_status}")

        except Exception as e:
            with self.lock:
                self.jobs[run_id]["status"] = "failed"
                self.jobs[run_id]["error"] = str(e)
                self.jobs[run_id]["phase"] = "failed"
                self.jobs[run_id]["updated_at"] = int(time.time())
            self._log(run_id, f"Pipeline failed: {str(e)}")

    def _run_cmd(self, run_id, cmd):
        self._log(run_id, f"Executing: {' '.join(cmd)}")
        # On windows, sometimes closing std handles helps prevent hangs
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1, # Line buffered
            close_fds=False, # Windows issue with close_fds=True
            env=env
        )
        
        try:
            try:
                for line in process.stdout:
                    self._log(run_id, line.strip())
            except Exception as e:
                self._log(run_id, f"Log read error: {e}")
        finally:
            try:
                if process.stdout:
                    process.stdout.close()
            except Exception:
                pass
        process.wait()
        if process.returncode != 0:
            raise Exception(f"Command failed with exit code {process.returncode}")

    def get_job_status(self, run_id):
        with self.lock:
            info = self.jobs.get(run_id)
            if not info:
                return None
            return {
                "run_id": run_id,
                "status": info.get("status"),
                "phase": info.get("phase"),
                "logs_tail": info.get("logs_tail", []),
                "updated_at": info.get("updated_at", int(time.time())),
                "error_message": info.get("error", ""),
            }

    def get_all_jobs(self):
        with self.lock:
            # Return summary list
            return [{
                "run_id": rid,
                "status": j["status"],
                "phase": j["phase"],
                "start_time": j["start_time"]
            } for rid, j in self.jobs.items()]
