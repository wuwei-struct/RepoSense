import os
import shutil
import unittest

from reposense.learn.ui.app import LearnUIApp
from tests.learn._learn_ui_fixture import build_learn_ui_fixture


def _snapshots_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "snapshots"))


class LearnUISnapshotsTest(unittest.TestCase):
    def setUp(self):
        self.fx = build_learn_ui_fixture()
        self.app = LearnUIApp(cases_dir=self.fx["cases_dir"], concepts_path=self.fx["concepts_path"])

    def tearDown(self):
        shutil.rmtree(self.fx["root"], ignore_errors=True)

    def _assert_snapshot(self, route: str, name: str):
        status, _ct, body = self.app.route(route, {})
        self.assertEqual(status, 200)
        got = body.decode("utf-8")
        snap_path = os.path.join(_snapshots_dir(), name)
        with open(snap_path, "r", encoding="utf-8") as f:
            expected_lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
        for needle in expected_lines:
            self.assertIn(needle, got)

    def test_snapshot_concepts_page(self):
        self._assert_snapshot("/learn/concepts", "concepts_page.snap")

    def test_snapshot_concept_detail_page(self):
        self._assert_snapshot("/learn/concepts/data.transaction_boundary", "concept_detail_page.snap")

    def test_snapshot_cases_page(self):
        self._assert_snapshot("/learn/cases", "cases_page.snap")

    def test_snapshot_case_detail_page(self):
        self._assert_snapshot("/learn/cases/case-a", "case_detail_page.snap")
