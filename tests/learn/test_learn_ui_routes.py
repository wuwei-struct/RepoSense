import shutil
import unittest

from reposense.learn.ui.app import LearnUIApp
from tests.learn._learn_ui_fixture import build_learn_ui_fixture


class LearnUIRoutesTest(unittest.TestCase):
    def setUp(self):
        self.fx = build_learn_ui_fixture()
        self.app = LearnUIApp(cases_dir=self.fx["cases_dir"], concepts_path=self.fx["concepts_path"])

    def tearDown(self):
        shutil.rmtree(self.fx["root"], ignore_errors=True)

    def _get_html(self, path: str):
        status, content_type, body = self.app.route(path, {})
        self.assertEqual(content_type, "text/html; charset=utf-8")
        return status, body.decode("utf-8")

    def test_concepts_page_route(self):
        status, html = self._get_html("/learn/concepts")
        self.assertEqual(status, 200)
        self.assertIn("Concept Navigator", html)
        self.assertIn("data.transaction_boundary", html)

    def test_concept_detail_route(self):
        status, html = self._get_html("/learn/concepts/data.transaction_boundary")
        self.assertEqual(status, 200)
        self.assertIn("Transaction Boundary", html)
        self.assertIn("View cases", html)

    def test_cases_page_route(self):
        status, html = self._get_html("/learn/cases")
        self.assertEqual(status, 200)
        self.assertIn("Case Browser", html)
        self.assertIn("Order service transaction", html)

    def test_case_detail_route(self):
        status, html = self._get_html("/learn/cases/case-a")
        self.assertEqual(status, 200)
        self.assertIn("Order service transaction", html)
        self.assertIn("Copy summary", html)
        self.assertIn("snippet #1", html)

    def test_not_found_concept_route(self):
        status, html = self._get_html("/learn/concepts/not-exist")
        self.assertEqual(status, 404)
        self.assertIn("Concept not found", html)

    def test_not_found_case_route(self):
        status, html = self._get_html("/learn/cases/not-exist")
        self.assertEqual(status, 404)
        self.assertIn("Case not found", html)
