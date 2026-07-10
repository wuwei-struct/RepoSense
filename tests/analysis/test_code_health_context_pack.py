import json
import os
import unittest

from reposense.analysis.health.health_export import export_code_health
from reposense.context_pack import build_context_pack
from tests._tmpdir import make_temp_dir


class CodeHealthContextPackTest(unittest.TestCase):
    def test_context_pack_includes_code_health_artifacts(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "code_health_smoke_min"))
        run_dir = make_temp_dir(prefix="code_health_pack_run_")
        try:
            for name, obj in [
                ("report.json", {"run_summary": {"findings_count": 0, "events_count": 0}, "findings": []}),
                ("event_graph.json", {"nodes": [], "edges": []}),
                ("coverage.json", {"walk": {"included_files": 1}, "warnings": []}),
            ]:
                with open(os.path.join(run_dir, name), "w", encoding="utf-8") as f:
                    json.dump(obj, f)
            export_code_health(run_dir, repo_path=repo)
            pack = build_context_pack(run_dir)
            for name in ["code_health.json", "code_health_summary.json", "maintainability_risks.json"]:
                self.assertTrue(os.path.isfile(os.path.join(pack, "ARTIFACTS", name)), name)
            with open(os.path.join(pack, "MAP", "index.json"), "r", encoding="utf-8") as f:
                idx = json.load(f)
            outputs = idx.get("outputs") or {}
            self.assertIn("code_health", outputs)
            self.assertIn("code_health_summary", outputs)
        finally:
            import shutil

            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
