import os, unittest, subprocess, sys, tempfile
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class LearnConceptCliTest(unittest.TestCase):
    def test_concept_exists(self):
        rd = mk_run_dir()
        cmd = [sys.executable, "-m", "reposense", "learn", "concept", "queue", "--from", rd, "--max", "5", "--json", "--concept-graph", cg_path()]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        out = res.stdout.decode("utf-8")
        self.assertIn("short_definition", out)
    def test_concept_missing(self):
        rd = mk_run_dir()
        cmd = [sys.executable, "-m", "reposense", "learn", "concept", "nonexist", "--from", rd, "--concept-graph", cg_path()]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 2)
