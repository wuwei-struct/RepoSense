import unittest

from reposense.analysis.context.context_schema import (
    FILE_CONTEXTS,
    REVIEW_MODIFIERS,
    normalize_file_context,
)


class FileContextSchemaTest(unittest.TestCase):
    def test_stable_id_and_allowed_values(self):
        item = {
            "file": "src/generated/client.ts",
            "context": "generated",
            "signals": ["generated_header"],
            "review_modifier": "exclude_from_primary_review",
        }
        first = normalize_file_context(item)
        second = normalize_file_context(item)
        self.assertEqual(first["annotation_id"], second["annotation_id"])
        self.assertIn(first["context"], FILE_CONTEXTS)
        self.assertIn(first["review_modifier"], REVIEW_MODIFIERS)


if __name__ == "__main__":
    unittest.main()
