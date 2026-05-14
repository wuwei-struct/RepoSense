import os, unittest, sys, subprocess, json, tempfile
class SpecCheckBadCategoryTest(unittest.TestCase):
    def test_bad_category(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "concepts"), exist_ok=True)
        os.makedirs(os.path.join(td, "taxonomies"), exist_ok=True)
        with open(os.path.join(td, "taxonomies", "categories.yaml"), "w", encoding="utf-8") as f:
            f.write("categories:\n  - io\n")
        with open(os.path.join(td, "concepts", "api.yaml"), "w", encoding="utf-8") as f:
            f.write("id: io.api\nconcept: api\ncategory: infra\nrelationships:\n  prerequisites: []\n")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "check", "--specs", td, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
