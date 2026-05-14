import os
import unittest


class ContextPackDocsExistTest(unittest.TestCase):
    def test_context_pack_docs_exist(self):
        files = [
            "docs/context-pack/CONTEXT_PACK_SPEC.md",
            "docs/context-pack/AI_ASSISTANT_USAGE.md",
            "docs/context-pack/EXAMPLES.md",
        ]
        for path in files:
            self.assertTrue(os.path.isfile(path), f"missing doc: {path}")


if __name__ == "__main__":
    unittest.main()

