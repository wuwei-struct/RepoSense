import os, json, tempfile, unittest, sys, subprocess
class SpecsGraphBuildTest(unittest.TestCase):
    def test_graph_build_from_specs(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "concepts"), exist_ok=True)
        os.makedirs(os.path.join(td, "taxonomies"), exist_ok=True)
        with open(os.path.join(td, "taxonomies", "categories.yaml"), "w", encoding="utf-8") as f:
            f.write("categories:\n  - io\n  - infra\n")
        with open(os.path.join(td, "concepts", "api.yaml"), "w", encoding="utf-8") as f:
            f.write("id: io.api\nconcept: api\ntitle: API\ncategory: io\nrelationships:\n  prerequisites: []\n  related: []\n")
        with open(os.path.join(td, "concepts", "queue.yaml"), "w", encoding="utf-8") as f:
            f.write("id: infra.queue\nconcept: queue\ntitle: Queue\ncategory: infra\nrelationships:\n  prerequisites: [io.api]\n  related: []\n")
        outp = os.path.join(td, "graph.json")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "graph", "build", "--specs", td, "--out", outp], stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.isfile(outp))
        data = json.load(open(outp, "r", encoding="utf-8"))
        ids = [c.get("concept_id") for c in data.get("concepts", [])]
        self.assertEqual(len(ids), len(set(ids)))
