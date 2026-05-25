import os
import tempfile
import unittest

from reposense.studio.server import resolve_local_repo_path
from reposense.studio.workspace import WorkspaceManager


class StudioLocalPathApiTest(unittest.TestCase):
    def test_resolve_rejects_empty(self):
        with self.assertRaises(ValueError):
            resolve_local_repo_path("")

    def test_resolve_rejects_missing(self):
        with self.assertRaises(ValueError):
            resolve_local_repo_path("Z:/definitely/missing/repo")

    def test_resolve_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as td:
            fp = os.path.join(td, "x.txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write("x")
            with self.assertRaises(ValueError):
                resolve_local_repo_path(fp)

    def test_resolve_accepts_directory(self):
        with tempfile.TemporaryDirectory() as td:
            out = resolve_local_repo_path(td)
            self.assertTrue(os.path.isabs(out))
            self.assertTrue(os.path.isdir(out))

    def test_workspace_import_local_path(self):
        with tempfile.TemporaryDirectory() as td:
            repo = os.path.join(td, "repo")
            os.makedirs(repo, exist_ok=True)
            ws = WorkspaceManager(base_dir=os.path.join(td, "studio"))
            project_id = ws.import_local_path(repo)
            self.assertTrue(project_id)
            self.assertEqual(ws.get_project_path(project_id), os.path.abspath(repo))


if __name__ == "__main__":
    unittest.main()
