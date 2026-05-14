import os, unittest, json, subprocess, sys
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class LearningPathToposortTest(unittest.TestCase):
    def test_toposort(self):
        cmd = [sys.executable, "-m", "reposense", "learn", "path", "infra.queue", "--graph", cg_path(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue("order" in data)
        self.assertTrue(len(data["order"]) >= 1)
