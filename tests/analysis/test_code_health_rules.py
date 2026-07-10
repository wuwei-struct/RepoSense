import os
import shutil
import unittest

from reposense.analysis.health.health_scanner import scan_code_health
from tests._tmpdir import make_temp_dir


class CodeHealthRulesTest(unittest.TestCase):
    def test_mvp_rules_detect_debt_type_escape_and_swallowed_error(self):
        repo = make_temp_dir(prefix="code_health_rules_repo_")
        run_dir = make_temp_dir(prefix="code_health_rules_run_")
        try:
            os.makedirs(os.path.join(repo, "src"), exist_ok=True)
            path = os.path.join(repo, "src", "service.ts")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    "export function run(input: any) {\n"
                    "  // FIXME: remove temporary workaround\n"
                    "  // @ts-ignore\n"
                    "  const x = input as any;\n"
                    "  try { risky(x); } catch (err) { return null; }\n"
                    "  return x;\n"
                    "}\n"
                )
            findings = scan_code_health(run_dir, repo, thresholds={"large_file_lines": 5, "giant_file_lines": 50})
            rules = {f.get("rule_id") for f in findings}
            self.assertIn("CHD-001", rules)
            self.assertIn("CHD-002", rules)
            self.assertIn("CHD-003", rules)
            self.assertIn("CHD-004", rules)
            self.assertTrue(all(not os.path.isabs(f.get("file") or "") for f in findings))
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(run_dir, ignore_errors=True)

    def test_logged_catch_is_not_swallowed_error(self):
        repo = make_temp_dir(prefix="code_health_logged_repo_")
        run_dir = make_temp_dir(prefix="code_health_logged_run_")
        try:
            os.makedirs(os.path.join(repo, "src"), exist_ok=True)
            with open(os.path.join(repo, "src", "safe.ts"), "w", encoding="utf-8") as f:
                f.write("try { risky(); } catch (err) { console.error(err); throw err; }\n")
            findings = scan_code_health(run_dir, repo)
            self.assertNotIn("CHD-004", {f.get("rule_id") for f in findings})
        finally:
            shutil.rmtree(repo, ignore_errors=True)
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

