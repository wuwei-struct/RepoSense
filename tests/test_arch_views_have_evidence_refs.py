import os, json, unittest, sys, subprocess
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
class ArchViewsEvidenceRefsTest(unittest.TestCase):
    def test_evidence_refs_exist(self):
        rd = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rd])
        av = os.path.join(rd, "arch_views")
        for nm in ["api_surface.json","service_map.json","data_surface.json","async_surface.json","deps_surface.json"]:
            p = os.path.join(av, nm)
            data = json.load(open(p, "r", encoding="utf-8"))
            # pick first few items depending on file structure
            items = []
            if "items" in data: items = data["items"]
            if "services" in data: items += data["services"]
            if "infra" in data: items += data["infra"]
            if "edges" in data: items += data["edges"]
            if "tables" in data: items += data["tables"]
            if "indexes" in data: items += data["indexes"]
            if "workflows" in data: items += data["workflows"]
            if "schedulers" in data: items += data["schedulers"]
            if "queues" in data: items += data["queues"]
            if "deps" in data: items += data["deps"]
            for it in items[:3]:
                evs = it.get("evidence") or []
                self.assertTrue(len(evs) >= 1)
                # evidence file exists
                e = evs[0]
                if isinstance(e, str) and e.startswith("E"):
                    ep = os.path.join(rd, "evidence", f"{e}.json")
                    self.assertTrue(os.path.isfile(ep))
