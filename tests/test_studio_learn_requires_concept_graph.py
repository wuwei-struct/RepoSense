import os
import tempfile
import unittest
from reposense.studio.workspace import WorkspaceManager
from reposense.studio.jobs import JobManager


class StubJobManager(JobManager):
    def __init__(self, workspace):
        super().__init__(workspace)
        self.last_learn_cmd = None

    def _run_cmd(self, run_id, cmd):
        txt = " ".join(cmd)
        # simulate graph build: write out file to --out path
        if "specs" in cmd and "graph" in cmd and "build" in cmd:
            if "--out" in cmd:
                out_idx = cmd.index("--out") + 1
                outp = cmd[out_idx]
                os.makedirs(os.path.dirname(outp), exist_ok=True)
                with open(outp, "w", encoding="utf-8") as f:
                    f.write("{}")
        # capture learn build invocation
        if "learn" in cmd and "build" in cmd:
            self.last_learn_cmd = cmd
        # do nothing else (skip actual subprocess)
        return


class StudioLearnRequiresConceptGraphTest(unittest.TestCase):
    def test_learn_always_has_concept_graph(self):
        base = tempfile.mkdtemp(prefix="ws-")
        ws = WorkspaceManager(base_dir=base)
        # prepare project
        pid = "proj-1"
        os.makedirs(os.path.join(ws.projects_dir, pid), exist_ok=True)
        run_id, run_dir = ws.create_run(pid)
        jm = StubJobManager(ws)
        repo_path = ws.get_project_path(pid)
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
        }
        # execute pipeline with no concept_graph provided
        jm._run_pipeline(run_id, repo_path, run_dir, "rulesets/basic", "presets/default.json", "specs", None)
        self.assertIsNotNone(jm.last_learn_cmd)
        self.assertIn("--concept-graph", jm.last_learn_cmd)
        # default generated path is run_dir/concepts.json
        cg_idx = jm.last_learn_cmd.index("--concept-graph") + 1
        cg_path = jm.last_learn_cmd[cg_idx]
        self.assertTrue(cg_path.endswith("concepts.json"))
        self.assertTrue(os.path.exists(cg_path))
        self.assertNotIn("--specs", jm.last_learn_cmd)


if __name__ == "__main__":
    unittest.main()
