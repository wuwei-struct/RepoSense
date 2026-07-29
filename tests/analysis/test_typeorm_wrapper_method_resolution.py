import unittest

from reposense.analysis.typescript.import_graph import build_typescript_index
from reposense.analysis.typescript.wrapper_resolution import (
    resolve_typeorm_wrappers,
)
from tests.analysis.test_typescript_import_graph_schema import FIXTURE


def fake_operations():
    return [
        {
            "operation_id": "save-create",
            "kind": "db.write",
            "file": "src/user.repository.ts",
            "line_start": 13,
        },
        {
            "operation_id": "delete-remove",
            "kind": "db.write",
            "file": "src/user.repository.ts",
            "line_start": 17,
        },
        {
            "operation_id": "save-store",
            "kind": "db.write",
            "file": "src/user.repository.ts",
            "line_start": 28,
        },
    ]


class TypeOrmWrapperMethodResolutionTest(unittest.TestCase):
    def test_direct_alias_barrel_default_and_local_assignment_resolve(self):
        rows, duplicates = resolve_typeorm_wrappers(
            build_typescript_index(FIXTURE), fake_operations()
        )
        self.assertEqual(duplicates, 0)
        by_class = {item["source_class"]: item for item in rows}
        self.assertEqual(
            by_class["DirectService"]["resolution_status"],
            "resolved_direct_import",
        )
        self.assertEqual(
            by_class["AliasService"]["resolution_status"], "resolved_barrel"
        )
        self.assertEqual(
            by_class["BarrelService"]["resolution_status"],
            "resolved_local_assignment",
        )
        self.assertEqual(
            by_class["DefaultService"]["resolved_class"],
            "DefaultUserRepository",
        )


if __name__ == "__main__":
    unittest.main()
