import os, json, unittest, sys, subprocess, hashlib
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
def sha(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        h.update(f.read())
    return h.hexdigest()
class ArchViewsDeterministicTest(unittest.TestCase):
    def test_deterministic_build(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rd])
        av = os.path.join(rd, "arch_views")
        h1 = {nm: sha(os.path.join(av, nm)) for nm in ["api_surface.json","service_map.json","data_surface.json","async_surface.json","deps_surface.json"]}
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rd])
        h2 = {nm: sha(os.path.join(av, nm)) for nm in ["api_surface.json","service_map.json","data_surface.json","async_surface.json","deps_surface.json"]}
        self.assertEqual(h1, h2)
