import os
import json
import tempfile
import unittest
from reposense.baseline import compute_diff


class DiffAddedRemovedAndSeverityChangeTest(unittest.TestCase):
    def test_diff_correct(self):
        rd = tempfile.mkdtemp(prefix="baseline_diff_")
        base = {
            "schema_version": 1,
            "findings": [
                {"fp":"fpA","severity":"note","ruleId":"rA","concept":"A","path":"x.py","startLine":1,"endLine":2},
                {"fp":"fpB","severity":"warning","ruleId":"rB","concept":"B","path":"y.py","startLine":3,"endLine":4}
            ]
        }
        bpath = os.path.join(rd, "base.json")
        with open(bpath, "w", encoding="utf-8") as f:
            json.dump(base, f)
        os.makedirs(os.path.join(rd, "new", "exports"), exist_ok=True)
        sarif = {
            "runs": [{
                "results": [
                    {"ruleId":"rA","level":"warning","locations":[{"physicalLocation":{"artifactLocation":{"uri":"x.py"}, "region":{"startLine":1,"endLine":2}}}], "fingerprints":{"reposense/v1":"fpA"}, "properties":{"concept":"A"}},
                    {"ruleId":"rC","level":"error","locations":[{"physicalLocation":{"artifactLocation":{"uri":"z.py"}, "region":{"startLine":7,"endLine":8}}}], "fingerprints":{"reposense/v1":"fpC"}, "properties":{"concept":"C"}}
                ]
            }]
        }
        with open(os.path.join(rd, "new", "exports", "report.sarif.json"), "w", encoding="utf-8") as f:
            json.dump(sarif, f)
        out = os.path.join(rd, "diff.json")
        d = compute_diff(bpath, os.path.join(rd, "new"), out)
        st = d.get("stats", {})
        self.assertEqual(st.get("added_error"), 1)
        self.assertEqual(st.get("added_warning"), 0)
        self.assertEqual(st.get("severity_upgrades"), 1)
        self.assertGreaterEqual(len(d.get("removed", [])), 1)


if __name__ == "__main__":
    unittest.main()
