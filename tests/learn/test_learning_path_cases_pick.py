import os, unittest, json, subprocess, sys, tempfile
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class LearningPathCasesPickTest(unittest.TestCase):
    def test_pick_from_run(self):
        rd = mk_run_dir()
        cmd = [sys.executable, "-m", "reposense", "learn", "path", "infra.queue", "--graph", cg_path(), "--from", rd, "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(len(data["picks"]) >= 1)
