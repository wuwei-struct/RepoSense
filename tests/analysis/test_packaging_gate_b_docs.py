import unittest
from pathlib import Path


class PackagingGateBDocsTest(unittest.TestCase):
    def test_gate_b_docs_and_index_exist(self):
        guide = Path("docs/release/OFFLINE_WHEELHOUSE_FRESH_VENV.md")
        runtime = Path("docs/release/PACKAGING_RUNTIME_ASSETS.md")
        checklist = Path("docs/RELEASE_CHECKLIST.md")
        index = Path("docs/INDEX.md")
        self.assertTrue(guide.is_file())
        guide_text = guide.read_text(encoding="utf-8")
        runtime_text = runtime.read_text(encoding="utf-8")
        checklist_text = checklist.read_text(encoding="utf-8")
        index_text = index.read_text(encoding="utf-8")
        for marker in (
            "Controlled Offline Wheelhouse",
            "fresh venv",
            "--no-index",
            "wheelhouse.lock.json",
            "PR-RELEASE-02",
        ):
            self.assertIn(marker, guide_text)
        self.assertIn("Packaging Gate B", runtime_text)
        self.assertIn("wheel hashes verified", checklist_text)
        self.assertIn("OFFLINE_WHEELHOUSE_FRESH_VENV.md", index_text)

    def test_docs_do_not_claim_v020_is_released(self):
        files = (
            Path("docs/release/OFFLINE_WHEELHOUSE_FRESH_VENV.md"),
            Path("docs/release/PACKAGING_RUNTIME_ASSETS.md"),
        )
        text = "\n".join(path.read_text(encoding="utf-8") for path in files)
        self.assertIn("v0.2.0 has not been released", text)
        self.assertNotIn("v0.2.0 is released", text)


if __name__ == "__main__":
    unittest.main()
