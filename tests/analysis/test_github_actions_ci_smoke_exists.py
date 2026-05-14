import os
import unittest


class GitHubActionsCiSmokeExistsTest(unittest.TestCase):
    def test_ci_smoke_workflow_exists_and_intent(self):
        p = ".github/workflows/ci-smoke.yml"
        self.assertTrue(os.path.isfile(p))
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()

        required = [
            "actions/checkout",
            "actions/setup-python",
            "python -m unittest",
            "reposense ci run",
            "reposense ai patterns",
            "reposense ai summary",
            "reposense ai risks",
            "reposense run manifest",
        ]
        for marker in required:
            self.assertIn(marker, text, f"ci-smoke missing marker: {marker}")


if __name__ == "__main__":
    unittest.main()
