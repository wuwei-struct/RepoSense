import unittest

from reposense.analysis.typescript.import_graph import (
    build_typescript_index,
    resolve_type,
)
from tests.analysis.test_typescript_import_graph_schema import FIXTURE


class TypeScriptImportGraphResolutionTest(unittest.TestCase):
    def test_direct_and_default_imports_resolve_to_source_file(self):
        index = build_typescript_index(FIXTURE)
        direct, _, limits = resolve_type(
            index, "src/services.ts", "UserRepository"
        )
        default, _, default_limits = resolve_type(
            index, "src/services.ts", "DefaultUserRepository"
        )
        self.assertFalse(limits)
        self.assertFalse(default_limits)
        self.assertEqual(direct[0]["symbol"]["file"], "src/user.repository.ts")
        self.assertEqual(
            default[0]["symbol"]["name"], "DefaultUserRepository"
        )


if __name__ == "__main__":
    unittest.main()
