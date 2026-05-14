import os, tempfile, unittest, sys, subprocess
from ._mk_run_dir import mk_run_dir
from reposense.learn.site_builder import build_site
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class SiteBuildFromLibraryTest(unittest.TestCase):
    def test_build_from_lib(self):
        rd = mk_run_dir()
        lib = tempfile.mkdtemp(prefix="case-lib-")
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "init", lib])
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "add", rd, "--lib", lib, "--min-confidence", "0.0", "--graph", cg_path()])
        outd = tempfile.mkdtemp(prefix="learn-out-")
        build_site(None, outd, cg_path(), lib_dir=lib)
        self.assertTrue(os.path.exists(os.path.join(outd, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(outd, "concepts", "queue.html")))
