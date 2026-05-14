import os
import json
import tempfile
import zipfile
import unittest
from reposense.context_pack import build_context_pack, zip_context_pack


class ContextPackIncludesBaselineAndDiffTest(unittest.TestCase):
    def test_context_pack_has_baseline_artifacts(self):
        rd = tempfile.mkdtemp(prefix="ctx_pack_base_")
        # minimal
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"profile":"p","ruleset":"r","budget":{}}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        json.dump({"run_summary":{},"findings":[]}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        # baseline files
        json.dump({"schema_version":1}, open(os.path.join(rd, "baseline_diff.json"), "w", encoding="utf-8"))
        json.dump({}, open(os.path.join(rd, "baseline_in.json"), "w", encoding="utf-8"))
        # build and zip
        build_context_pack(rd, top_n=0)
        zpath = zip_context_pack(rd)
        self.assertTrue(os.path.isfile(zpath))
        with zipfile.ZipFile(zpath, "r") as zf:
            names = zf.namelist()
        self.assertTrue(any("ARTIFACTS/baseline_diff.json" in n for n in names))
        self.assertTrue(any("ARTIFACTS/baseline_in.json" in n for n in names))


if __name__ == "__main__":
    unittest.main()
