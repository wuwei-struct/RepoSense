import os
import zipfile
import tempfile
import unittest
from reposense.scan import run_scan


class ContextPackZipContainsStructureTest(unittest.TestCase):
    def test_context_pack_zip_shape(self):
        repo = tempfile.mkdtemp(prefix="repo_cpz_")
        with open(os.path.join(repo, "main.py"), "w", encoding="utf-8") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/hello')\ndef h():\n    return {}\n")
        out = tempfile.mkdtemp(prefix="out_cpz_")
        rd = run_scan(repo, out, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rulesets", "specs_v2")), os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "presets", "prod_lite.json")))
        zp = os.path.join(rd, "exports", "context_pack.zip")
        self.assertTrue(os.path.isfile(zp))
        with zipfile.ZipFile(zp, "r") as z:
            names = z.namelist()
            self.assertIn("context_pack/README.md", names)
            self.assertIn("context_pack/MAP/index.json", names)
            self.assertIn("context_pack/SPEC/ruleset_summary.json", names)
            self.assertIn("context_pack/manifest.json", names)
            info = z.getinfo("context_pack/README.md")
            self.assertGreaterEqual(info.file_size, 200)


if __name__ == "__main__":
    unittest.main()

