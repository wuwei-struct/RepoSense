import os
import json
import tempfile
import unittest
from reposense.ci import run_ci


class NoRedactFlagKeepsPathsTest(unittest.TestCase):
    def test_no_redact_keeps_paths(self):
        repo = tempfile.mkdtemp(prefix="repo_keep_")
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        for root, _, fs in os.walk(src):
            for nm in fs:
                rp = os.path.relpath(os.path.join(root, nm), src)
                dst = os.path.join(repo, rp)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(os.path.join(root, nm), "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
        out = tempfile.mkdtemp(prefix="no_redact_")
        os.environ["REPOSENSE_REDACT"] = "0"
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False, redact=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        ci = json.load(open(os.path.join(rd, "ci_summary.json"), "r", encoding="utf-8"))
        run_dir = os.path.abspath(ci.get("run_dir") or "")
        self.assertIn(os.path.abspath(out), run_dir)
        self.assertEqual(run_dir, os.path.abspath(rd))
        s = json.dumps(ci)
        self.assertNotIn("<REPO_ROOT>", s)
        self.assertNotIn("<REDACTED>", s)
        self.assertFalse(ci.get("redaction_enabled"))


if __name__ == "__main__":
    unittest.main()
