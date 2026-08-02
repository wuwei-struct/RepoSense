import unittest
from pathlib import Path


class StudioLegacyUiAuditTest(unittest.TestCase):
    def test_only_one_routed_studio_page_exists(self):
        studio_indexes = list(Path("webui/studio").rglob("index.html"))
        self.assertEqual(studio_indexes, [Path("webui/studio/index.html")])
        server = Path("reposense/studio/server.py").read_text(encoding="utf-8")
        self.assertIn('self.path == "/" or self.path == "/studio" or self.path == "/studio/"', server)
        self.assertIn('"studio", "index.html"', server)

    def test_report_and_learn_surfaces_are_still_consumed(self):
        server = Path("reposense/studio/server.py").read_text(encoding="utf-8")
        self.assertTrue(Path("reposense/report.py").is_file())
        self.assertIn("learn", server)
        self.assertIn("report.html", Path("reposense/studio/artifact_catalog.py").read_text(encoding="utf-8"))
        docs = Path("docs/studio/STUDIO_WORKBENCH.md").read_text(encoding="utf-8")
        self.assertIn("No second", docs)
        self.assertIn("legacy Studio HTML page", docs)
        self.assertIn("static report, Learn", docs)


if __name__ == "__main__":
    unittest.main()
