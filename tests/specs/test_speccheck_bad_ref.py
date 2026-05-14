import os, unittest, sys, subprocess, json, tempfile
class SpecCheckBadRefTest(unittest.TestCase):
    def test_bad_prereq(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "concepts"), exist_ok=True)
        with open(os.path.join(td, "concepts", "a.yaml"), "w", encoding="utf-8") as f:
            f.write("id: a\nconcept: a\ncategory: io\nrelationships:\n  prerequisites: [missing.id]\n")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "check", "--specs", td, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
