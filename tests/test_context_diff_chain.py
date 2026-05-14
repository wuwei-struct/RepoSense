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
class ContextDiffChainTest(unittest.TestCase):
    def test_diff_between_packs(self):
        rdA = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        rdB = subprocess.run([sys.executable, "-m", "reposense", "scan", fx("repos","graph_mix_v2"), "--out", out_dir(), "--ruleset", ruleset_dir(), "--budget", budget_path()], stdout=subprocess.PIPE).stdout.decode("utf-8").strip().splitlines()[-1]
        # build arch views
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rdA])
        subprocess.run([sys.executable, "-m", "reposense", "arch", "build", rdB])
        packA = os.path.join(out_dir(), "packsA")
        packB = os.path.join(out_dir(), "packsB")
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rdA, "--out", packA, "--include-evidence", "--include-brief"])
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rdB, "--out", packB, "--include-evidence", "--include-brief"])
        # zip
        pa = packA + ".zip"; pb = packB + ".zip"
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rdA, "--out", packA, "--include-evidence", "--include-brief", "--zip"])
        subprocess.run([sys.executable, "-m", "reposense", "context", "pack", rdB, "--out", packB, "--include-evidence", "--include-brief", "--zip"])
        diff_out = os.path.join(out_dir(), "diff_out")
        subprocess.run([sys.executable, "-m", "reposense", "context", "diff", pa, pb, "--out", diff_out, "--json"], stdout=subprocess.PIPE)
        with open(os.path.join(diff_out, "diff_report.json"), "r", encoding="utf-8") as f:
            diffj = json.load(f)
        # events added contains queue:rabbitmq or infra queue
        ev_added = diffj["snapshot"]["events"]["added"]
        self.assertTrue(any(k.endswith("queue:rabbitmq") or (t=="queue") for t,k in ev_added))
        # tables added should be non-empty on v2
        self.assertTrue(len(diffj["arch"]["data_surface"]["tables"]["added"]) >= 1)
        # md includes basic headings
        md = open(os.path.join(diff_out, "diff_report.md"), "r", encoding="utf-8").read()
        self.assertIn("Snapshot Diff", md)
        self.assertIn("added", md)
        # deterministic
        diff_out2 = os.path.join(out_dir(), "diff_out2")
        subprocess.run([sys.executable, "-m", "reposense", "context", "diff", pa, pb, "--out", diff_out2], stdout=subprocess.PIPE)
        s1 = sha(os.path.join(diff_out, "diff_report.md"))
        s2 = sha(os.path.join(diff_out2, "diff_report.md"))
        self.assertEqual(s1, s2)
