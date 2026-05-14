import unittest
from reposense.linking.path_normalize import normalize_path, template_match


class PathNormalizeCrossLanguageTest(unittest.TestCase):
    def test_placeholder_normalization(self):
        self.assertEqual(normalize_path("/users/:id"), "/users/{id}")
        self.assertEqual(normalize_path("/users/{id}"), "/users/{id}")

    def test_slash_and_query_normalization(self):
        self.assertEqual(normalize_path("/users//1/?x=1"), "/users/1")

    def test_template_match(self):
        self.assertTrue(template_match("/users/{id}", "/users/123"))
        self.assertFalse(template_match("/users/{id}", "/users/123/orders"))


if __name__ == "__main__":
    unittest.main()
