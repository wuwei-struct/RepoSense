import os
import tempfile
import unittest
from reposense.studio.workspace import WorkspaceManager
from reposense.studio.jobs import JobManager


class StubJobManager(JobManager):
    def _run_cmd(self, run_id, cmd):
        if ("export" in cmd) and ("sarif" in cmd):
            out_idx = cmd.index("--out") + 1
            outp = cmd[out_idx]
            os.makedirs(os.path.dirname(outp), exist_ok=True)
            with open(outp, "w", encoding="utf-8") as f:
                f.write("{}")
        elif ("context" in cmd) and ("pack" in cmd):
            out_idx = cmd.index("--out") + 1
            outd = cmd[out_idx]
            os.makedirs(outd, exist_ok=True)
            with open(os.path.join(outd, "manifest.json"), "w", encoding="utf-8") as f:
                f.write("{}")
        else:
            # simulate other stages no-op
            return


class StudioExportArtifactsTest(unittest.TestCase):
    def test_export_stage_outputs(self):
        base = tempfile.mkdtemp(prefix="ws-")
        ws = WorkspaceManager(base_dir=base)
        pid = "proj-1"
        os.makedirs(os.path.join(ws.projects_dir, pid), exist_ok=True)
        run_id, run_dir = ws.create_run(pid)
        jm = StubJobManager(ws)
        repo_path = ws.get_project_path(pid)
        # init job state
        jm.jobs[run_id] = {
            "status": "queued",
            "phase": "queued",
            "logs": [],
            "logs_tail": [],
            "project_id": pid,
            "run_dir": run_dir,
            "start_time": 0,
            "updated_at": 0,
            "error": "",
            "log_path": os.path.join(run_dir, "logs.txt"),
            "output_paths": {"run_dir": run_dir},
        }
        jm._run_pipeline(run_id, repo_path, run_dir, "rulesets/basic", "presets/default.json", "specs", None)
        sarif = os.path.join(run_dir, "exports", "report.sarif.json")
        ctx_dir = os.path.join(run_dir, "context_pack")
        ctx_zip = os.path.join(run_dir, "exports", "context_pack.zip")
        self.assertTrue(os.path.exists(sarif))
        self.assertTrue(os.path.exists(os.path.join(ctx_dir, "manifest.json")))
        self.assertTrue(os.path.exists(ctx_zip))


if __name__ == "__main__":
    unittest.main()
