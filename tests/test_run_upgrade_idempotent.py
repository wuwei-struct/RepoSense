import os
import json
import tempfile
import unittest
from reposense.run_upgrade import upgrade_run


class RunUpgradeIdempotentTest(unittest.TestCase):
    def test_idempotent(self):
        rd = tempfile.mkdtemp(prefix="upgrade_idem_")
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"budget": {}, "ruleset_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"nodes":[],"edges":[]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        json.dump({"endpoints":[],"stats":{},"mismatches":{}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints":[],"stats":{}}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        json.dump({"walk":{},"warnings":[]}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        code = upgrade_run(rd, inplace=True)
        self.assertEqual(code, 0)
        # capture bytes
        a1 = open(os.path.join(rd, "run_manifest.json"), "rb").read()
        a2 = open(os.path.join(rd, "report.json"), "rb").read()
        code2 = upgrade_run(rd, inplace=True)
        self.assertEqual(code2, 0)
        b1 = open(os.path.join(rd, "run_manifest.json"), "rb").read()
        b2 = open(os.path.join(rd, "report.json"), "rb").read()
        self.assertEqual(a1, b1)
        self.assertEqual(a2, b2)


if __name__ == "__main__":
    unittest.main()
