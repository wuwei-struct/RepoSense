import os, unittest, subprocess, sys, json
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class CliCasesTest(unittest.TestCase):
    def test_cases_output(self):
        rd = mk_run_dir()
        cmd = [sys.executable, "-m", "reposense", "learn", "cases", "infra.queue", "--from", rd, "--graph", cg_path(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        cases = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(len(cases) >= 1)
        for c in cases:
            self.assertTrue(len(c["evidence_refs"]) >= 1)
