import json
import os
import shutil
import unittest

from reposense.analysis.authz.authz_export import export_permission_auditor
from reposense.context_pack import build_context_pack
from tests._tmpdir import make_temp_dir


class PermissionAuditorContextPackTest(unittest.TestCase):
    def test_context_pack_includes_permission_artifacts(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = make_temp_dir(prefix="authz_pack_run_")
        try:
            for name, obj in [
                ("report.json", {"run_summary": {"findings_count": 0, "events_count": 0}, "findings": []}),
                ("event_graph.json", {"nodes": [], "edges": []}),
                ("coverage.json", {"walk": {"included_files": 1}, "warnings": []}),
            ]:
                with open(os.path.join(run_dir, name), "w", encoding="utf-8") as f:
                    json.dump(obj, f)
            export_permission_auditor(run_dir, repo_path=repo)
            pack = build_context_pack(run_dir)
            for name in ["permission_surface.json", "permission_risks.json", "permission_risk_report.md", "human_permission_review_required.md", "authz_negative_test_plan.md"]:
                self.assertTrue(os.path.isfile(os.path.join(pack, "ARTIFACTS", name)), name)
            with open(os.path.join(pack, "MAP", "index.json"), "r", encoding="utf-8") as f:
                idx = json.load(f)
            outputs = idx.get("outputs") or {}
            self.assertIn("permission_surface", outputs)
            self.assertIn("permission_risks", outputs)
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

