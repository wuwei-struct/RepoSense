import os
import json
import tempfile
import unittest
from reposense.scan import run_scan


class ContextPackL1ShapeTest(unittest.TestCase):
    def test_context_pack_structure(self):
        repo = tempfile.mkdtemp(prefix="repo_cp_")
        with open(os.path.join(repo, "main.py"), "w", encoding="utf-8") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/hello')\ndef h():\n    return {}\n")
        out = tempfile.mkdtemp(prefix="out_cp_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        root = os.path.join(rd, "context_pack")
        self.assertTrue(os.path.isfile(os.path.join(root, "README.md")))
        self.assertTrue(os.path.isfile(os.path.join(root, "MAP", "index.json")))
        self.assertTrue(os.path.isfile(os.path.join(root, "SPEC", "ruleset_summary.json")))
        self.assertTrue(os.path.isfile(os.path.join(root, "manifest.json")))
        with open(os.path.join(root, "README.md"), "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertGreaterEqual(len(lines), 50)
        tf_dir = os.path.join(root, "EVIDENCE", "top_findings")
        te_dir = os.path.join(root, "EVIDENCE", "top_events")
        # at least one evidence file exists for this fixture
        self.assertTrue(len(os.listdir(tf_dir)) >= 1)
        self.assertTrue(len(os.listdir(te_dir)) >= 1)
        # MAP has outputs and stats
        with open(os.path.join(root, "MAP", "index.json"), "r", encoding="utf-8") as f:
            idx = json.load(f)
        self.assertIn("outputs", idx)
        self.assertIn("stats", idx)


if __name__ == "__main__":
    unittest.main()

