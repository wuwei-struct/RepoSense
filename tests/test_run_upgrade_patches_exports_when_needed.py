import os
import json
import tempfile
import zipfile
import unittest
from reposense.run_upgrade import upgrade_run


class RunUpgradePatchesExportsWhenNeededTest(unittest.TestCase):
    def test_patch_exports(self):
        rd = tempfile.mkdtemp(prefix="upgrade_patch_")
        # minimal files
        os.makedirs(os.path.join(rd, "exports"), exist_ok=True)
        os.makedirs(os.path.join(rd, "context_pack","ARTIFACTS"), exist_ok=True)
        # sarif without gate_status
        with open(os.path.join(rd, "exports", "report.sarif.json"), "w", encoding="utf-8") as f:
            json.dump({"version":"2.1.0","runs":[{"properties":{},"results":[]}]}, f)
        # quality_gate.json present with status
        with open(os.path.join(rd, "quality_gate.json"), "w", encoding="utf-8") as f:
            json.dump({"status":"warn","generated_by":{"tool":"reposense","reposense_version":"0.1.0","ruleset_id":"","ruleset_fingerprint":"","schema_version":1}}, f)
        # context_pack.zip missing gate
        zpath = os.path.join(rd, "exports", "context_pack.zip")
        with zipfile.ZipFile(zpath, "w") as zf:
            zf.writestr("ARTIFACTS/dummy.txt", "x")
        code = upgrade_run(rd, inplace=True)
        self.assertEqual(code, 0)
        s = json.load(open(os.path.join(rd, "exports", "report.sarif.json"), "r", encoding="utf-8"))
        props = (s.get("runs") or [{}])[0].get("properties", {})
        self.assertIsNotNone(props.get("reposense.gate_status"))
        with zipfile.ZipFile(zpath, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("quality_gate.json" in n for n in names))


if __name__ == "__main__":
    unittest.main()
