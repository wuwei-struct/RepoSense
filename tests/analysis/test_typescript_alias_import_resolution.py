import unittest

from reposense.analysis.typescript.import_graph import (
    build_typescript_index,
    resolve_type,
)
from tests.analysis.test_typescript_import_graph_schema import FIXTURE


class TypeScriptAliasImportResolutionTest(unittest.TestCase):
    def test_named_alias_keeps_imported_symbol(self):
        index = build_typescript_index(FIXTURE)
        rows, imported, limits = resolve_type(
            index, "src/services.ts", "AccountRepository"
        )
        self.assertFalse(limits)
        self.assertEqual(imported["imported"], "UserRepository")
        self.assertEqual(imported["local"], "AccountRepository")
        self.assertEqual(rows[0]["symbol"]["name"], "UserRepository")


if __name__ == "__main__":
    unittest.main()
