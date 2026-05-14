import os
import json
import tempfile
import zipfile
import unittest
from reposense.patch_exports import patch_context_pack_with_gate


class GatePatchAddsQualityGateToContextPackZipTest(unittest.TestCase):
    def test_patch_context_pack_zip_contains_gate(self):
        rd = tempfile.mkdtemp(prefix="gate_ctx_")
        ctx = os.path.join(rd, "context_pack")
        os.makedirs(os.path.join(ctx, "ARTIFACTS"), exist_ok=True)
        gate_path = os.path.join(rd, "quality_gate.json")
        with open(gate_path, "w", encoding="utf-8") as f:
            json.dump({"status":"fail","violations":[]}, f)
        zip_path = os.path.join(rd, "exports", "context_pack.zip")
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        res = patch_context_pack_with_gate(rd, ctx, zip_path, gate_path)
        self.assertTrue(res.get("ok"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("quality_gate.json" in n for n in names))


if __name__ == "__main__":
    unittest.main()
