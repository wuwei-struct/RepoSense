import os
import json
import tempfile
import zipfile
import unittest
from reposense.ci import run_ci


class ContextPackZipIsScrubbedTest(unittest.TestCase):
    def test_pack_scrub(self):
        repo = tempfile.mkdtemp(prefix="repo_ctx_")
        src = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        for root, _, fs in os.walk(src):
            for nm in fs:
                rp = os.path.relpath(os.path.join(root, nm), src)
                dst = os.path.join(repo, rp)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(os.path.join(root, nm), "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
        out = tempfile.mkdtemp(prefix="ctx_scrub_")
        os.environ["REPOSENSE_REDACT"] = "1"
        code = run_ci(repo, out, profile="demo", with_context_pack=True, json_stdout=False)
        self.assertIn(code, (0,2))
        rd = sorted([os.path.join(out, d) for d in os.listdir(out) if d.startswith("run-")])[-1]
        zp = os.path.join(rd, "exports", "context_pack.zip")
        self.assertTrue(os.path.isfile(zp))
        rnd = os.path.abspath(repo)
        with zipfile.ZipFile(zp, "r") as z:
            names = z.namelist()
            for nm in names:
                if nm.endswith(".json") or nm.endswith(".md") or nm.endswith(".html"):
                    data = z.read(nm).decode("utf-8", errors="ignore")
                    self.assertNotIn(rnd, data)


if __name__ == "__main__":
    unittest.main()
