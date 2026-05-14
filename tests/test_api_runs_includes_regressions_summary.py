import os
import json
import threading
import time
import urllib.request
import unittest
from reposense.studio.workspace import WorkspaceManager
from reposense.studio.server import run_server


class ApiRunsIncludesRegressionsSummaryTest(unittest.TestCase):
    def test_api_runs_contains_regressions(self):
        wm = WorkspaceManager()
        # create run and write state
        run_id, run_dir = wm.create_run("proj")
        with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
            json.dump({"run_id": run_id, "status":"completed","phase":"done","created_at":int(time.time()),"updated_at":int(time.time())}, f)
        with open(os.path.join(run_dir, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump({"baseline_used": True, "regressions": {"total":3,"added_error":1,"severity_upgrades":1,"added_warning":1}}, f)
        # start server
        t = threading.Thread(target=run_server, args=(8020,), daemon=True)
        t.start()
        time.sleep(0.2)
        with urllib.request.urlopen("http://127.0.0.1:8020/api/runs") as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self.assertTrue(any("summary" in item for item in data))
        found = [item for item in data if item.get("summary",{}).get("baseline_used")]
        self.assertTrue(len(found) >= 1)
        sm = found[0]["summary"]
        self.assertEqual(sm.get("regressions",{}).get("total"), 3)


if __name__ == "__main__":
    unittest.main()
