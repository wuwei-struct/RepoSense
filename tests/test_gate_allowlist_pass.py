import os, json, sqlite3, subprocess, unittest, sys
from reposense.scan import run_scan
from reposense.diff import stable_finding_id
def fx(*p):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", *p))
def out_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "analysis_runs"))
def ruleset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "basic"))
def budget_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "default.json"))
def policy_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "policies", "default.json"))
class GateAllowlistPassTest(unittest.TestCase):
    def test_gate_allowlist(self):
        rd = run_scan(fx("repos","gate_fail"), out_dir(), ruleset_dir(), budget_path())
        # collect violating stable ids
        conn = sqlite3.connect(os.path.join(rd, "detections.sqlite"))
        c = conn.cursor()
        rows = c.execute("select f.fid, f.concept, f.rule_id, e.parse_level, f.confidence, f.primary_eid, f.meta_json from findings f join evidence e on e.eid=f.primary_eid").fetchall()
        conn.close()
        sids = []
        for fid, concept, rule_id, parse_level, confidence, primary_eid, meta_json in rows:
            if concept in ("External IO","Secrets/Config") and parse_level in ("L2","L3"):
                m = {}
                try:
                    m = json.loads(meta_json or "{}")
                except:
                    m = {}
                sid, ok = stable_finding_id({"concept": concept, "rule_id": rule_id, "parse_level": parse_level, "confidence": confidence, "primary_eid": primary_eid, "meta": m})
                sids.append(sid)
        # write allowlist
        with open(os.path.join(rd, "manifest.json"), "r", encoding="utf-8") as f:
            man = json.load(f)
        repo_root = man.get("repo_root")
        os.makedirs(os.path.join(repo_root, ".reposense"), exist_ok=True)
        with open(os.path.join(repo_root, ".reposense", "allowlist.json"), "w", encoding="utf-8") as f:
            json.dump({"findings": sids}, f)
        cmd = [sys.executable, "-m", "reposense", "gate", rd, "--policy", policy_path()]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
