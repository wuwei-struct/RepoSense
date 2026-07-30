import re
import unittest
from pathlib import Path


FILES = (
    Path("docs/release/V0_2_0_RELEASE_READINESS_AUDIT.md"),
    Path("docs/release/V0_2_0_RELEASE_PLAN.md"),
    Path("docs/release/V0_2_0_CHANGELOG_DRAFT.md"),
    Path("docs/release/V0_2_0_RELEASE_NOTES_DRAFT.md"),
    Path("docs/INDEX.md"),
    Path("docs/RELEASE_CHECKLIST.md"),
)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9])[A-Z]:[\\/]|"
    r"(?<![A-Za-z0-9:])/(?:home|Users|tmp|private|root)(?:/|\b)|"
    r"file://"
)


class V020ReleaseLinksTest(unittest.TestCase):
    def test_release_document_links_resolve(self):
        missing = []
        for path in FILES:
            text = path.read_text(encoding="utf-8")
            for match in LINK_RE.finditer(text):
                target = match.group(1).strip().strip("<>")
                if target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = target.split("#", 1)[0].split("?", 1)[0]
                if target and not (path.parent / target).exists():
                    missing.append(f"{path}: {target}")
        self.assertEqual(missing, [])

    def test_readme_images_exist(self):
        for readme in (Path("README.md"), Path("README.zh-CN.md")):
            text = readme.read_text(encoding="utf-8")
            images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
            self.assertTrue(images, str(readme))
            for target in images:
                if not target.startswith(("http://", "https://")):
                    self.assertTrue((readme.parent / target).is_file(), target)

    def test_new_release_documents_have_no_local_absolute_paths(self):
        for path in FILES[:4]:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(ABSOLUTE_PATH_RE.search(text), str(path))

    def test_index_and_checklist_link_all_release_documents(self):
        index = Path("docs/INDEX.md").read_text(encoding="utf-8")
        checklist = Path("docs/RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
        for name in (
            "V0_2_0_RELEASE_READINESS_AUDIT.md",
            "V0_2_0_RELEASE_PLAN.md",
            "V0_2_0_CHANGELOG_DRAFT.md",
            "V0_2_0_RELEASE_NOTES_DRAFT.md",
        ):
            self.assertIn(name, index)
            self.assertIn(name, checklist)


if __name__ == "__main__":
    unittest.main()
