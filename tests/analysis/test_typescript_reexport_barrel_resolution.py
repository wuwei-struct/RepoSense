import unittest

from reposense.analysis.typescript.import_graph import (
    build_typescript_index,
    resolve_type,
)
from tests.analysis.test_typescript_import_graph_schema import FIXTURE


class TypeScriptReexportBarrelResolutionTest(unittest.TestCase):
    def test_barrel_resolution_is_bounded_and_traceable(self):
        index = build_typescript_index(FIXTURE)
        rows, _, limits = resolve_type(
            index, "src/services.ts", "AccountRepository"
        )
        self.assertFalse(limits)
        self.assertEqual(rows[0]["depth"], 2)
        self.assertEqual(
            rows[0]["path"],
            ["src/index.ts", "src/repositories.ts", "src/user.repository.ts"],
        )
        self.assertEqual(len(rows[0]["reexport_evidence_refs"]), 2)


if __name__ == "__main__":
    unittest.main()
