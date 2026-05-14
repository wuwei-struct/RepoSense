import os
import json
import tempfile
import unittest
from reposense.baseline import save_baseline


class BaselineSaveSchemaAndStableOrderTest(unittest.TestCase):
    def test_save_baseline_schema_and_order(self):
        rd = tempfile.mkdtemp(prefix="baseline_save_")
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        sarif = {
            "runs": [{
                "results": [
                    {"ruleId":"r1","level":"warning","locations":[{"physicalLocation":{"artifactLocation":{"uri":"a.py"}, "region":{"startLine":10,"endLine":12}}}], "fingerprints":{"reposense/v1":"fp1"}, "properties":{"concept":"A"}},
                    {"ruleId":"r2","level":"error","locations":[{"physicalLocation":{"artifactLocation":{"uri":"b.py"}, "region":{"startLine":5,"endLine":6}}}], "fingerprints":{"reposense/v1":"fp2"}, "properties":{"concept":"B"}}
                ]
            }]
        }
        with open(os.path.join(rd, "exports", "report.sarif.json"), "w", encoding="utf-8") as f:
            json.dump(sarif, f)
        out = os.path.join(rd, "baseline.json")
        save_baseline(rd, out)
        data = json.load(open(out, "r", encoding="utf-8"))
        self.assertEqual(data.get("schema_version"), 1)
        fnds = data.get("findings", [])
        self.assertEqual(fnds[0]["severity"], "error")
        self.assertEqual(fnds[0]["fp"], "fp2")


if __name__ == "__main__":
    unittest.main()
