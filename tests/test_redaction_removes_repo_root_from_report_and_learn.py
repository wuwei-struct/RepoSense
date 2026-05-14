import os
import json
import tempfile
import unittest
from reposense.ci import run_ci
from reposense.learn.site_builder import build_site as learn_build


class RedactionRemovesRepoRootFromReportAndLearnTest(unittest.TestCase):
    def test_redact_paths(self):
        repo = tempfile.mkdtemp(prefix="repo_root_")
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        for root, _, fs in os.walk(src):
            for nm in fs:
                rp = os.path.relpath(os.path.join(root, nm), src)
                dst = os.path.join(repo, rp)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(os.path.join(root, nm), "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
        out = tempfile.mkdtemp(prefix="redact_repo_")
        os.environ["REPOSENSE_REDACT"] = "1"
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=True)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        learn_build(run_dir=rd, out_dir=os.path.join(rd, "learn"), concept_graph_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "concept_graph_demo.json")), max_cases_per_concept=5)
        report = open(os.path.join(rd, "report.html"), "r", encoding="utf-8").read()
        self.assertNotIn(os.path.abspath(repo), report)
        li = os.path.join(rd, "learn", "index.html")
        self.assertTrue(os.path.isfile(li))
        self.assertNotIn(os.path.abspath(repo), open(li, "r", encoding="utf-8").read())


if __name__ == "__main__":
    unittest.main()
