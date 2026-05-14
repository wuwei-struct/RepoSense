import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class CiRunDefaultProfileIsDemoTest(unittest.TestCase):
    def test_ci_default_demo(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_json"))
        out = tempfile.mkdtemp(prefix="ci_demo_")
        os.environ["REPOSENSE_EDITION"] = "oss"
        code = run_ci(repo, out, with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        cfg = json.load(open(os.path.join(rd, "meta","config.json"), "r", encoding="utf-8"))
        self.assertEqual(cfg.get("profile"), "demo")
        self.assertTrue(cfg.get("gate_path"))


if __name__ == "__main__":
    unittest.main()
