import os
import json
import tempfile
import unittest
from reposense.patch_exports import patch_sarif_with_gate


class GatePatchInjectsSarifGateStatusTest(unittest.TestCase):
    def test_patch_injects_gate_status(self):
        rd = tempfile.mkdtemp(prefix="gate_patch_")
        sarif_dir = os.path.join(rd, "exports")
        os.makedirs(sarif_dir, exist_ok=True)
        sarif_path = os.path.join(sarif_dir, "report.sarif.json")
        with open(sarif_path, "w", encoding="utf-8") as f:
            json.dump({"version":"2.1.0","runs":[{"tool":{"driver":{"name":"RepoSense","rules":[]}},"results":[],"properties":{}}]}, f)
        gate_path = os.path.join(rd, "quality_gate.json")
        with open(gate_path, "w", encoding="utf-8") as f:
            json.dump({"status":"warn","violations":[]}, f)
        res = patch_sarif_with_gate(rd, sarif_path, gate_path)
        self.assertTrue(res.get("ok"))
        s = json.load(open(sarif_path, "r", encoding="utf-8"))
        props = (s.get("runs") or [{}])[0].get("properties", {})
        self.assertEqual(props.get("reposense.gate_status"), "warn")


if __name__ == "__main__":
    unittest.main()
