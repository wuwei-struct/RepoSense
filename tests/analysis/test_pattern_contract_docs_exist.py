import os
import unittest


class PatternContractDocsExistTest(unittest.TestCase):
    def test_contract_docs_and_schema_exist(self):
        files = [
            "docs/rules/PATTERN_CONTRACT.md",
            "docs/rules/RULE_AUTHORING_GUIDE.md",
            "schemas/pattern.schema.json",
        ]
        for path in files:
            self.assertTrue(os.path.isfile(path), f"missing file: {path}")


if __name__ == "__main__":
    unittest.main()

