import os, json, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ArchViewsCountsTest(unittest.TestCase):
    def test_counts(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rd])
        av = os.path.join(rd, "arch_views")
        api = json.load(open(os.path.join(av, "api_surface.json"), "r", encoding="utf-8"))["items"]
        svc = json.load(open(os.path.join(av, "service_map.json"), "r", encoding="utf-8"))
        data = json.load(open(os.path.join(av, "data_surface.json"), "r", encoding="utf-8"))
        self.assertTrue(len(api) >= 1)
        self.assertTrue(len(svc.get("services", [])) >= 1)
        self.assertTrue(len(svc.get("edges", [])) >= 1)
        self.assertTrue(len(data.get("tables", [])) >= 1 or len(data.get("indexes", [])) >= 1)
