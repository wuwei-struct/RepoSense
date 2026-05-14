import os, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ArchViewsBuildTest(unittest.TestCase):
    def test_build_views(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rd])
        av = os.path.join(rd, "arch_views")
        self.assertTrue(os.path.isdir(av))
        for nm in ["api_surface.json","service_map.json","data_surface.json","async_surface.json","deps_surface.json"]:
            p = os.path.join(av, nm)
            self.assertTrue(os.path.isfile(p))
            self.assertTrue(os.path.getsize(p) > 0)
