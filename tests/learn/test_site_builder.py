import os, json, tempfile, unittest
from ._mk_run_dir import mk_run_dir
from reposense.learn.site_builder import build_site
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class SiteBuilderTest(unittest.TestCase):
    def test_build_site(self):
        rd = mk_run_dir()
        outd = tempfile.mkdtemp(prefix="learn-out-")
        build_site(rd, outd, cg_path(), max_cases_per_concept=10)
        self.assertTrue(os.path.exists(os.path.join(outd, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(outd, "concepts", "queue.html")))
        self.assertTrue(os.path.exists(os.path.join(outd, "casebank.jsonl")))
        with open(os.path.join(outd, "casebank.jsonl"), "r", encoding="utf-8") as f:
            line = f.readline()
            import json as _json
            _json.loads(line)
        with open(os.path.join(outd, "learn_manifest.json"), "r", encoding="utf-8") as f:
            man = json.load(f)
        self.assertTrue("run_dir" in man)
