import hashlib
import os
import unittest


class DemoScriptsDoNotTouchTrackedArchiveLogTest(unittest.TestCase):
    def setUp(self):
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.log_path = os.path.join(
            self.root, "docs", "archive", "local-artifacts", "MOVED_FROM_ROOT.md"
        )
        with open(self.log_path, "rb") as handle:
            self.log_digest = hashlib.sha256(handle.read()).hexdigest()

    def tearDown(self):
        with open(self.log_path, "rb") as handle:
            current_digest = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(self.log_digest, current_digest)

    def test_runtime_scripts_do_not_reference_tracked_archive_paths(self):
        tools_dir = os.path.join(self.root, "tools")
        checked = []
        for name in os.listdir(tools_dir):
            if not name.endswith(".ps1"):
                continue
            path = os.path.join(tools_dir, name)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            checked.append(name)
            self.assertNotIn("MOVED_FROM_ROOT.md", text, name)
            self.assertNotIn("docs\\archive\\local-artifacts\\root-moved", text, name)
        self.assertTrue(checked)


if __name__ == "__main__":
    unittest.main()
