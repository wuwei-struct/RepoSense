import os, tempfile, unittest
from reposense.learn.site_builder import build_site
def cg_path(tmp_graph):
    return tmp_graph
def specs_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs"))
class SiteConceptSpecsFieldsTest(unittest.TestCase):
    def test_concept_page_contains_specs_fields(self):
        outd = tempfile.mkdtemp(prefix="learn-out-")
        # build graph from specs first
        import subprocess, sys
        tmp_graph = os.path.join(outd, "concepts.json")
        subprocess.run([sys.executable, "-m", "reposense", "specs", "graph", "build", "--specs", specs_dir(), "--out", tmp_graph])
        # provide empty library to avoid run_dir dependency
        libd = tempfile.mkdtemp(prefix="lib-")
        open(os.path.join(libd, "casebank.jsonl"), "w", encoding="utf-8").write("")
        build_site(None, outd, cg_path(tmp_graph), specs_dir=specs_dir(), lib_dir=libd)
        # pick one concept
        p = os.path.join(outd, "concepts", "concurrency_idempotency.html")
        # concurrency.idempotency concept_id maps to slug concurrency_idempotency
        # Since our graph json may use different IDs, check existence loosely
        # iterate concept pages
        cons = os.listdir(os.path.join(outd, "concepts"))
        self.assertTrue(len(cons) >= 1)
        # open first concept page and assert headings present
        html = open(os.path.join(outd, "concepts", cons[0]), "r", encoding="utf-8").read()
        self.assertIn("What", html)
        self.assertIn("Why", html)
        self.assertIn("Non-goals", html)
        self.assertIn("Consequences", html)
        self.assertIn("Objectives", html)
