import os, json, unittest, sys, subprocess, tempfile
from tests.learn._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class ExtractCasesCaseSpecTest(unittest.TestCase):
    def test_case_spec_output(self):
        rd = mk_run_dir()
        outd = tempfile.mkdtemp(prefix="case-out-")
        res = subprocess.run([sys.executable, "-m", "reposense", "learn", "extract-cases", rd, "--out", outd, "--min-confidence", "0.0", "--graph", cg_path(), "--case-spec"], stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        # concept id 'infra.queue' should exist based on map/graph
        any_dir = [d for d in os.listdir(outd) if os.path.isdir(os.path.join(outd, d))]
        self.assertTrue(len(any_dir) >= 1)
        # has at least one case json
        found = False
        for d in any_dir:
            p = os.path.join(outd, d)
            files = [f for f in os.listdir(p) if f.endswith(".case.json")]
            if files:
                found = True
                with open(os.path.join(p, files[0]), "r", encoding="utf-8") as f:
                    js = json.load(f)
                self.assertTrue(len(js.get("evidence_refs", [])) >= 1)
        self.assertTrue(found)
