import os
import unittest


class ReleaseCandidateExistsTest(unittest.TestCase):
    def test_release_candidate_exists(self):
        path = "docs/release/RELEASE_CANDIDATE_v0.1.0.md"
        self.assertTrue(os.path.isfile(path), f"missing release candidate doc: {path}")

    def test_release_candidate_has_required_markers(self):
        path = "docs/release/RELEASE_CANDIDATE_v0.1.0.md"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        markers = [
            "candidate version",
            "completed items",
            "pending items",
            "release blockers / non-blockers",
            "blockers",
            "non-blockers",
        ]
        for m in markers:
            self.assertIn(m, text, f"missing candidate marker: {m}")

    def test_readme_has_release_entrypoints(self):
        with open("README.md", "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn("docs/release/RELEASE_CHECKLIST_PUBLIC.md", text)
        self.assertIn("docs/release/RELEASE_PROCESS.md", text)


if __name__ == "__main__":
    unittest.main()
