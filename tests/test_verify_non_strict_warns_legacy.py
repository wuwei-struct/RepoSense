import os
import json
import tempfile
import unittest
from reposense.verifier import run_verify


class VerifyNonStrictWarnsLegacyTest(unittest.TestCase):
    def test_legacy_missing_stamp_warns(self):
        rd = tempfile.mkdtemp(prefix="legacy_run_")
        # minimal files
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"repo_root": rd}, open(os.path.join(rd, "manifest.json"), "w", encoding="utf-8"))
        json.dump({"version":"0.1.0"}, open(os.path.join(rd, "meta","tool_version.json"), "w", encoding="utf-8"))
        json.dump({"version":{"version":"1.0.0"}}, open(os.path.join(rd, "meta","ruleset_version.json"), "w", encoding="utf-8"))
        json.dump({"budget": {}}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        open(os.path.join(rd, "report.html"), "w", encoding="utf-8").write("<html></html>")
        # legacy artifacts missing stamps
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"nodes":[],"edges":[]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        json.dump({"endpoints":[],"stats":{},"mismatches":{}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints":[],"stats":{}}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        json.dump({"walk":{}}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        # verifier should not fail in non-strict
        try:
            run_verify(rd, as_json=True, strict=False)
        except SystemExit as e:
            self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
