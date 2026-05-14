import os
import unittest


class ReleaseProcessExistsTest(unittest.TestCase):
    def test_release_process_exists(self):
        path = "docs/release/RELEASE_PROCESS.md"
        self.assertTrue(os.path.isfile(path), f"missing release process doc: {path}")

    def test_release_process_has_key_steps(self):
        path = "docs/release/RELEASE_PROCESS.md"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()

        markers = [
            "select version",
            "run demo",
            "run regression checks",
            "review release notes",
            "review assets",
            "prepare tag",
            "publish release",
            "publish announcement",
            "record known limitations",
        ]
        for m in markers:
            self.assertIn(m, text, f"missing process marker: {m}")


if __name__ == "__main__":
    unittest.main()
