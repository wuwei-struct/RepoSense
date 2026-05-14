import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class LanguageCapabilitiesArtifactSmokeTest(unittest.TestCase):
    def test_capabilities_artifact_exists(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        out = tempfile.mkdtemp(prefix="lang_caps_")
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0, 2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        cp = os.path.join(rd, "language_capabilities.json")
        self.assertTrue(os.path.isfile(cp))
        data = json.load(open(cp, "r", encoding="utf-8"))
        self.assertIn("registered_languages", data)
        self.assertIn("capability_matrix", data)
        self.assertIn("detected_languages", data)
        ts = (data.get("capability_matrix") or {}).get("typescript") or {}
        self.assertIn("queue.dispatch", ts.get("event_kinds") or [])
        self.assertIn("queue.consume", ts.get("event_kinds") or [])
        self.assertIn("cache.read", ts.get("event_kinds") or [])
        self.assertIn("cache.write", ts.get("event_kinds") or [])
        self.assertIn("cache.invalidate", ts.get("event_kinds") or [])
        jv = (data.get("capability_matrix") or {}).get("java") or {}
        self.assertIn("api.route", jv.get("event_kinds") or [])
        self.assertIn("db.transaction", jv.get("event_kinds") or [])
        self.assertIn("queue.dispatch", jv.get("event_kinds") or [])
        self.assertIn("queue.consume", jv.get("event_kinds") or [])
        self.assertIn("db.read", jv.get("event_kinds") or [])
        self.assertIn("db.write", jv.get("event_kinds") or [])
        self.assertTrue(os.path.isfile(os.path.join(rd, "exports", "context_pack.zip")))


if __name__ == "__main__":
    unittest.main()
