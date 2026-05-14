import os, json, sqlite3, unittest, tempfile, sys, subprocess
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class LibraryAddAndDedupeTest(unittest.TestCase):
    def test_dedupe_sources(self):
        rd1 = mk_run_dir()
        rd2 = mk_run_dir()
        lib = tempfile.mkdtemp(prefix="case-lib-")
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "init", lib])
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "add", rd1, "--lib", lib, "--min-confidence", "0.0", "--graph", cg_path()])
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "add", rd2, "--lib", lib, "--min-confidence", "0.0", "--graph", cg_path()])
        with open(os.path.join(lib, "casebank.jsonl"), "r", encoding="utf-8") as f:
            lines = [json.loads(ln) for ln in f.read().strip().splitlines()]
        # should have at least one case with multiple sources
        has_multi = any(len(item.get("sources",[])) >= 2 for item in lines)
        self.assertTrue(has_multi)
