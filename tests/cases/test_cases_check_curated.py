import os, json, unittest, sys, subprocess, tempfile
class CasesCheckCuratedTest(unittest.TestCase):
    def test_curated_check(self):
        td = tempfile.mkdtemp(prefix="cases-")
        cur = os.path.join(td, "curated")
        os.makedirs(cur, exist_ok=True)
        with open(os.path.join(cur, "good.case.json"), "w", encoding="utf-8") as f:
            json.dump({"case_id":"x","concept_id":"io.api","title":"API Case","teach":{"steps":[]}, "questions":{"q1":"?"}, "evidence_refs":[{"eid":"E1"}]}, f)
        res = subprocess.run([sys.executable, "-m", "reposense", "cases", "check", cur, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
