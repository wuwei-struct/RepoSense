import os, unittest, subprocess, sys, json
def cg_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "learn", "graph", "concepts.json"))
class CliConceptsTest(unittest.TestCase):
    def test_concepts_json(self):
        cmd = [sys.executable, "-m", "reposense", "learn", "concepts", "--graph", cg_path(), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        self.assertEqual(res.returncode, 0)
        items = json.loads(res.stdout.decode("utf-8"))
        ids = [ (i.get("concept_id") or i.get("concept")).lower() for i in items ]
        self.assertEqual(len(ids), len(set(ids)))
        # prerequisites must exist
        idset = set(ids)
        for i in items:
            for ref in i.get("prerequisites") or []:
                self.assertIn(ref.lower(), idset)
