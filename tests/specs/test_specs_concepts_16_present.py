import os, unittest
def concepts_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs", "concepts"))
class SpecsConcepts16PresentTest(unittest.TestCase):
    def test_16_concepts_present_and_unique(self):
        files = [f for f in os.listdir(concepts_dir()) if f.endswith(".yaml")]
        self.assertTrue(len(files) >= 16)
        ids = set()
        import yaml
        for f in files:
            data = yaml.safe_load(open(os.path.join(concepts_dir(), f), "r", encoding="utf-8").read())
            cid = (data.get("id") or "").lower()
            self.assertTrue(cid)
            self.assertNotIn(cid, ids)
            ids.add(cid)
