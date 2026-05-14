import os, unittest, subprocess, sys, json
class SchemaConceptValidateTest(unittest.TestCase):
    def test_all_concepts_valid_via_cli(self):
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "check", "--specs", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs")), "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
