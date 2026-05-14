import os, unittest, sys, subprocess, json, tempfile
class RulesetCompileTest(unittest.TestCase):
    def test_compile_rulesets(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "rulesets"), exist_ok=True)
        with open(os.path.join(td, "rulesets", "concurrency.idempotency.yaml"), "w", encoding="utf-8") as f:
            f.write("concept: Idempotency\nsignals:\n  any_of:\n    keywords: [idempotent]\n    patterns: ['\\\\bretry\\\\b']\n")
        outd = tempfile.mkdtemp(prefix="rs-out-")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", td, "--out", outd, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertTrue(os.path.isfile(os.path.join(outd, "rules.yaml")))
