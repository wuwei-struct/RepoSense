import os, json, unittest, subprocess, sys
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class ConceptMapCheckTest(unittest.TestCase):
    def test_check_ok(self):
        # use default map
        mp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concept_map.json"))
        cmd = [sys.executable, "-m", "reposense", "learn", "graph", "check", "--graph", cg_path(), "--map", mp, "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
    def test_unknown_target(self):
        # create bad map
        tmp = os.path.abspath(os.path.join(os.path.dirname(__file__), "bad_map.json"))
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"map":{"API":"unknown.id"}}, f)
        cmd = [sys.executable, "-m", "reposense", "learn", "graph", "check", "--graph", cg_path(), "--map", tmp, "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
