import os
import json
import tempfile
import unittest
from reposense.run_upgrade import upgrade_run


class RunUpgradeAddsStampsAndManifestTest(unittest.TestCase):
    def test_upgrade_adds_stamps(self):
        rd = tempfile.mkdtemp(prefix="upgrade_add_")
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"budget": {}, "ruleset_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2"))}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"nodes":[],"edges":[]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        json.dump({"endpoints":[],"stats":{},"mismatches":{}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints":[],"stats":{}}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        json.dump({"walk":{},"warnings":[]}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        code = upgrade_run(rd, inplace=True)
        self.assertEqual(code, 0)
        # check stamps
        for rel in ["report.json","event_graph.json","api_surface.json","entrypoints.json","coverage.json"]:
            o = json.load(open(os.path.join(rd, rel), "r", encoding="utf-8"))
            self.assertIsNotNone(o.get("generated_by"))
            self.assertEqual(o.get("schema_version"), 1)
        self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))


if __name__ == "__main__":
    unittest.main()
