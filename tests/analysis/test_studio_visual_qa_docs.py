import os
import re
import unittest


class StudioVisualQaDocsTest(unittest.TestCase):
    def test_manual_visual_qa_record_is_complete(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        path = os.path.join(root, "docs", "validation", "STUDIO_VISUAL_QA_V02.md")
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()

        for marker in [
            "2026-07-30",
            "c5f1110ff39915df5881eb449a15896130d8ce52",
            "Chromium",
            "1440 x 900",
            "run-1785373708-af7e4069",
            "Manual visual QA result: passed",
            "not generated",
            "does not prove repository safety",
        ]:
            self.assertIn(marker, text)

        self.assertIsNone(
            re.search(r"[A-Za-z]:[\\/](?:Users|projects|workspaces)[\\/]", text),
            "QA documentation must not contain a local absolute path",
        )


if __name__ == "__main__":
    unittest.main()
