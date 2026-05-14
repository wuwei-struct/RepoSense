import os, json, unittest, tempfile, sys, subprocess
from ._mk_run_dir import mk_run_dir
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class LibraryVerifyTest(unittest.TestCase):
    def test_verify_fail_missing_evidence_refs(self):
        rd = mk_run_dir()
        lib = tempfile.mkdtemp(prefix="case-lib-")
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "init", lib])
        subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "add", rd, "--lib", lib, "--min-confidence", "0.0", "--graph", cg_path()])
        # tamper casebank: remove evidence_refs in first source
        p = os.path.join(lib, "casebank.jsonl")
        with open(p, "r", encoding="utf-8") as f:
            items = [json.loads(ln) for ln in f.read().strip().splitlines()]
        if items:
            items[0]["sources"][0].pop("evidence_refs", None)
        with open(p, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        res = subprocess.run([sys.executable, "-m", "reposense", "learn", "library", "verify", "--lib", lib, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
