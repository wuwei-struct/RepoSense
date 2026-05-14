import os
import json
import tempfile
import unittest
from reposense.verifier import run_verify


class VerifyStrictFailsWhenMissingStampTest(unittest.TestCase):
    def test_strict_fail(self):
        rd = tempfile.mkdtemp(prefix="strict_run_")
        os.makedirs(os.path.join(rd, "meta"), exist_ok=True)
        json.dump({"repo_root": rd}, open(os.path.join(rd, "manifest.json"), "w", encoding="utf-8"))
        json.dump({"version":"0.1.0"}, open(os.path.join(rd, "meta","tool_version.json"), "w", encoding="utf-8"))
        json.dump({"version":{"version":"1.0.0"}}, open(os.path.join(rd, "meta","ruleset_version.json"), "w", encoding="utf-8"))
        json.dump({"budget": {}}, open(os.path.join(rd, "meta","config.json"), "w", encoding="utf-8"))
        open(os.path.join(rd, "report.html"), "w", encoding="utf-8").write("<html></html>")
        json.dump({"findings":[],"run_summary":{}}, open(os.path.join(rd, "report.json"), "w", encoding="utf-8"))
        json.dump({"nodes":[],"edges":[]}, open(os.path.join(rd, "event_graph.json"), "w", encoding="utf-8"))
        json.dump({"endpoints":[],"stats":{},"mismatches":{}}, open(os.path.join(rd, "api_surface.json"), "w", encoding="utf-8"))
        json.dump({"entrypoints":[],"stats":{}}, open(os.path.join(rd, "entrypoints.json"), "w", encoding="utf-8"))
        json.dump({"walk":{}}, open(os.path.join(rd, "coverage.json"), "w", encoding="utf-8"))
        # strict should exit=2
        with self.assertRaises(SystemExit) as cm:
            run_verify(rd, as_json=True, strict=True)
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
