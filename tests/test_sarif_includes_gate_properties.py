import os
import json
import tempfile
import unittest
from reposense.sarif import export_sarif


class SarifIncludesGatePropertiesTest(unittest.TestCase):
    def test_sarif_includes_gate_props(self):
        rd = tempfile.mkdtemp(prefix="sarif_gate_")
        with open(os.path.join(rd, "report.json"), "w", encoding="utf-8") as f:
            json.dump({"findings": []}, f)
        with open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "fail", "violations": [{"level":"fail","metric":"artifacts_missing_count","message":"缺失"}]}, f)
        with open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8") as f:
            json.dump({}, f)
        out = os.path.join(rd, "exports", "report.sarif.json")
        export_sarif(rd, out)
        s = json.load(open(out, "r", encoding="utf-8"))
        props = ((s.get("runs") or [{}])[0].get("properties") or {})
        self.assertIn("reposense.gate_status", props)
        results = ((s.get("runs") or [{}])[0].get("results") or [])
        self.assertTrue(any((r.get("ruleId") or "").startswith("reposense.gate.") for r in results))


if __name__ == "__main__":
    unittest.main()

