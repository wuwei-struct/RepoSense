import os, unittest, json, tempfile, sys, subprocess
class SchemaCaseRejectsBadTest(unittest.TestCase):
    def test_bad_case_loc_types(self):
        td = tempfile.mkdtemp(prefix="cases-")
        bad = {"case_id":"x","concept_id":"io.api","evidence_refs":[{"kind":"code.string","file":"a.py","loc":{"start":"1","end":"2"},"snippet":"x","hash":"sha256:..."}]}
        with open(os.path.join(td, "bad.case.json"), "w", encoding="utf-8") as f:
            json.dump(bad, f)
        res = subprocess.run([sys.executable, "-m", "reposense", "cases", "check", td, "--strict-schema", "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
        msg = "\n".join(data["errors"])
        self.assertTrue("type" in msg or "jsonschema_missing" in msg)
