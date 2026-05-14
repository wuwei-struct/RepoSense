import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class CiRunProfileProdLiteUsesDemoV1InOssTest(unittest.TestCase):
    def test_ci_prod_lite_maps_demo_v1(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_json"))
        out = tempfile.mkdtemp(prefix="ci_plite_")
        os.environ["REPOSENSE_EDITION"] = "oss"
        code = run_ci(repo, out, profile="prod_lite", with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        cfg = json.load(open(os.path.join(rd, "meta","config.json"), "r", encoding="utf-8"))
        self.assertEqual(cfg.get("profile"), "prod_lite")
        self.assertTrue(cfg.get("gate_path").endswith(os.path.join("presets","gates","prod_lite.json")))


if __name__ == "__main__":
    unittest.main()
