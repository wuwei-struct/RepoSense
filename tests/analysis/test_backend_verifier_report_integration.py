import json
import os
import shutil
import tempfile
import unittest

from reposense.analysis.reports.backend_verifier_report import export_backend_verifier_report
from reposense.scan import run_scan

class BackendVerifierReportIntegrationTest(unittest.TestCase):
    def test_integration_outputs_and_manifest(self):
        local_tmp = os.path.join(os.getcwd(), ".tmp_os00", "temp")
        os.makedirs(local_tmp, exist_ok=True)
        repo = tempfile.mkdtemp(prefix="repo_bvr_int_", dir=local_tmp)
        with open(os.path.join(repo, "app.py"), "w", encoding="utf-8") as f:
            f.write(
                "from fastapi import FastAPI\n"
                "app = FastAPI()\n"
                "@app.post('/orders')\n"
                "def create_order(payload):\n"
                "    save(payload)\n"
                "    send(payload)\n"
                "    return {'ok': True}\n"
            )
        out = tempfile.mkdtemp(prefix="out_bvr_int_", dir=local_tmp)
        try:
            rd = run_scan(
                repo,
                out,
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rulesets", "specs_v2")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "presets", "prod_lite.json")),
            )
            res = export_backend_verifier_report(rd)
            self.assertTrue(os.path.isfile(res["json_path"]))
            self.assertTrue(os.path.isfile(res["markdown_path"]))
            with open(res["json_path"], "r", encoding="utf-8") as f:
                obj = json.load(f)
            self.assertEqual(obj.get("report_type"), "backend_verifier_report")
            self.assertEqual(len(obj.get("sections") or []), 9)
            self.assertTrue(os.path.isfile(os.path.join(rd, "run_manifest.json")))
            with open(os.path.join(rd, "run_manifest.json"), "r", encoding="utf-8") as f:
                rm = json.load(f)
            paths = set([x.get("path") for x in (rm.get("artifacts") or [])])
            self.assertIn("backend_verifier_report.json", paths)
            self.assertIn("backend_verifier_report.md", paths)
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
