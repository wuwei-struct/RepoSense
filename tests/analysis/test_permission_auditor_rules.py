import os
import shutil
import unittest

from reposense.analysis.authz.authz_scanner import scan_permission_auditor
from tests._tmpdir import make_temp_dir


class PermissionAuditorRulesTest(unittest.TestCase):
    def test_mvp_rules_hit_fixture(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "repos", "authz_smoke_min"))
        run_dir = make_temp_dir(prefix="authz_rules_run_")
        try:
            surface, risks = scan_permission_auditor(run_dir, repo)
            rules = {r.get("rule_id") for r in risks.get("risks") or []}
            self.assertIn("AUTHZ-001", rules)
            self.assertIn("AUTHZ-002", rules)
            self.assertIn("AUTHZ-003", rules)
            self.assertIn("AUTHZ-004", rules)
            self.assertIn("AUTHZ-005", rules)
            self.assertTrue(surface.get("routes"))
            self.assertTrue(surface.get("frontend_permission_signals"))
        finally:
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_role_guard_prevents_admin_missing_role_risk(self):
        repo = make_temp_dir(prefix="authz_safe_repo_")
        run_dir = make_temp_dir(prefix="authz_safe_run_")
        try:
            os.makedirs(os.path.join(repo, "src"), exist_ok=True)
            with open(os.path.join(repo, "src", "server.ts"), "w", encoding="utf-8") as f:
                f.write("app.post('/api/admin/rebuild', requireAuth, requireRole('admin'), (req, res) => res.json({ok:true}))\n")
            _surface, risks = scan_permission_auditor(run_dir, repo)
            self.assertNotIn("AUTHZ-003", {r.get("rule_id") for r in risks.get("risks") or []})
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

