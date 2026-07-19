import json
import os
import re
import unittest


class RealRepoSmokeConfigTest(unittest.TestCase):
    def test_cases_are_pinned_public_and_portable(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        path = os.path.join(root, "tools", "validation", "real_repo_cases.json")
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        cases = payload.get("cases") or []
        self.assertGreaterEqual(len(cases), 4)
        ids = [case.get("case_id") for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("typescript-bullmq-redis-ecommerce", ids)
        self.assertIn("java-spring-kafka-reactive", ids)
        text = json.dumps(payload)
        self.assertNotRegex(text, r"(?<![A-Za-z])[A-Za-z]:[\\/]")
        for case in cases:
            self.assertTrue(case.get("repository_url", "").startswith("https://github.com/"))
            self.assertIn(case.get("language"), {"typescript", "javascript", "java"})
            self.assertTrue(case.get("license"))
            sha = str(case.get("commit_sha") or "")
            self.assertRegex(sha, r"^[0-9a-f]{40}$")
            self.assertNotIn(sha.lower(), {"main", "master"})
            self.assertTrue(case.get("expected_capabilities"))
            self.assertGreater(case.get("max_repository_size_mb", 0), 0)


if __name__ == "__main__":
    unittest.main()
