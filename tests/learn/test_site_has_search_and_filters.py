import os, tempfile, unittest
from ._mk_run_dir import mk_run_dir
from reposense.learn.site_builder import build_site
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class SiteSearchFiltersTest(unittest.TestCase):
    def test_search_filter_hooks(self):
        rd = mk_run_dir()
        outd = tempfile.mkdtemp(prefix="learn-out-")
        build_site(rd, outd, cg_path())
        with open(os.path.join(outd, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("data-search", html)
        self.assertIn("data-filter-difficulty", html)
        self.assertIn("data-filter-parse-level", html)
        self.assertIn("data-filter-confidence", html)
        self.assertIn("data-filter-category", html)
