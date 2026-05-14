import os
import json
import tempfile
import subprocess
import sys
import unittest
from reposense.ci import run_ci


class GateWithoutFlagReadsGatePathFromMetaConfigTest(unittest.TestCase):
    def test_gate_fallback_meta(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "api_json"))
        out = tempfile.mkdtemp(prefix="gate_meta_")
        os.environ["REPOSENSE_EDITION"] = "oss"
        code = run_ci(repo, out, with_context_pack=False, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        cfg = json.load(open(os.path.join(rd, "meta","config.json"), "r", encoding="utf-8"))
        self.assertTrue(cfg.get("gate_path"))
        p = subprocess.run([sys.executable,"-m","reposense","gate", rd, "--json"], capture_output=True, text=True)
        self.assertIn(p.returncode, (0,2))


if __name__ == "__main__":
    unittest.main()
