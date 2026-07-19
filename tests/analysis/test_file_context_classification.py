import unittest

from reposense.analysis.context.file_context import classify_file_contexts
from tests.analysis._review_context_fixture import fixture_repo


class FileContextClassificationTest(unittest.TestCase):
    def test_generated_seed_template_and_production(self):
        rows = classify_file_contexts(fixture_repo())
        by_file = {row["file"]: row for row in rows}
        self.assertEqual(by_file["src/generated/client.ts"]["context"], "generated")
        self.assertEqual(by_file["src/database/seeds/demo.seed.ts"]["context"], "seed")
        self.assertEqual(by_file["src/templates/service.template.ts"]["context"], "template")
        self.assertEqual(by_file["src/services/order.service.ts"]["context"], "production")
        self.assertEqual(by_file["src/services/order.service.ts"]["review_modifier"], "normal")

    def test_repository_name_does_not_make_production_files_templates(self):
        rows = classify_file_contexts(fixture_repo())
        production = next(row for row in rows if row["file"] == "src/services/order.service.ts")
        self.assertNotEqual(production["context"], "template")


if __name__ == "__main__":
    unittest.main()
