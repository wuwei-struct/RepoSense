import os
import tempfile
import unittest
import time
from reposense.studio.workspace import WorkspaceManager


class WorkspaceRunStatePersistenceTest(unittest.TestCase):
    def test_write_read_list(self):
        base = tempfile.mkdtemp(prefix="ws-")
        ws = WorkspaceManager(base_dir=base)
        pid = "proj-1"
        # create project dir manually
        os.makedirs(os.path.join(ws.projects_dir, pid), exist_ok=True)
        run_id, run_dir = ws.create_run(pid)
        state = {
            "run_id": run_id,
            "project_id": pid,
            "status": "completed",
            "phase": "done",
            "created_at": int(time.time()) - 10,
            "updated_at": int(time.time()),
            "error_message": "",
            "log_path": os.path.join(run_dir, "logs.txt"),
            "output_paths": {"run_dir": run_dir},
        }
        ws.write_run_state(run_id, state)
        st = ws.read_run_state(run_id)
        self.assertIsNotNone(st)
        self.assertEqual(st["run_id"], run_id)
        self.assertEqual(st["status"], "completed")
        lst = ws.list_runs()
        self.assertTrue(any(x["run_id"] == run_id for x in lst))
