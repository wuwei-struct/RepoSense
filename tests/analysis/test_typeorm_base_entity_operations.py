import unittest

from reposense.parsers.typescript_typeorm import detect_typeorm_operations


class TypeOrmBaseEntityOperationsTest(unittest.TestCase):
    def test_confirmed_base_entity_static_calls(self):
        lines = [
            "import { BaseEntity } from 'typeorm';",
            "class User extends BaseEntity {}",
            "User.findOne({ where: { id: 1 } });",
            "User.save({ id: 1 });",
        ]
        items = detect_typeorm_operations(lines)
        self.assertEqual(
            {(item["operation"], item["kind"]) for item in items},
            {("findOne", "db.read"), ("save", "db.write")},
        )


if __name__ == "__main__":
    unittest.main()
