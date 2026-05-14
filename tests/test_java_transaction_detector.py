import unittest
from reposense.parsers.java_minimal import detect_java_transactions


class JavaTransactionDetectorTest(unittest.TestCase):
    def test_method_level_transactional(self):
        lines = [
            "class Svc {",
            "  @Transactional",
            "  public void save() { }",
            "}",
        ]
        out = detect_java_transactions(lines)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["scope"], "method")
        self.assertEqual(out[0]["method_name"], "save")

    def test_class_level_transactional(self):
        lines = [
            "@Transactional",
            "class Svc {",
            "  public void save() { }",
            "}",
        ]
        out = detect_java_transactions(lines)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["scope"], "class")
        self.assertEqual(out[0]["class_name"], "Svc")

    def test_non_transactional_not_reported(self):
        lines = [
            "class Svc {",
            "  @Deprecated",
            "  public void save() { }",
            "}",
        ]
        out = detect_java_transactions(lines)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
