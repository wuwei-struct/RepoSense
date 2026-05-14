import unittest
from reposense.parsers.java_minimal import detect_java_db_ops


class JavaDbDetectorTest(unittest.TestCase):
    def test_jpa_repo_and_entity_manager(self):
        lines = [
            "class S {",
            "  UserRepository repo;",
            "  EntityManager entityManager;",
            "  void run(){ repo.save(x); repo.findById(id); entityManager.persist(x); entityManager.find(X.class,id); }",
            "}",
        ]
        out = detect_java_db_ops(lines)
        self.assertTrue(any(x.get("db_style") == "jpa_repository" and x.get("event_kind") == "db.write" for x in out))
        self.assertTrue(any(x.get("db_style") == "jpa_repository" and x.get("event_kind") == "db.read" for x in out))
        self.assertTrue(any(x.get("db_style") == "entity_manager" and x.get("event_kind") == "db.write" for x in out))
        self.assertTrue(any(x.get("db_style") == "entity_manager" and x.get("event_kind") == "db.read" for x in out))

    def test_mybatis_mapper_and_sql_session(self):
        lines = [
            "class S {",
            "  UserMapper mapper;",
            "  SqlSession sqlSession;",
            "  void run(){ mapper.insert(x); mapper.selectOne(id); sqlSession.update(\"u\",x); sqlSession.selectList(\"u\"); }",
            "}",
        ]
        out = detect_java_db_ops(lines)
        self.assertTrue(any(x.get("db_style") == "mybatis_mapper" and x.get("event_kind") == "db.write" for x in out))
        self.assertTrue(any(x.get("db_style") == "mybatis_mapper" and x.get("event_kind") == "db.read" for x in out))
        self.assertTrue(any(x.get("db_style") == "sql_session" and x.get("event_kind") == "db.write" for x in out))
        self.assertTrue(any(x.get("db_style") == "sql_session" and x.get("event_kind") == "db.read" for x in out))

    def test_no_false_positive(self):
        lines = [
            "class X {",
            "  Obj obj;",
            "  void run(){ obj.save(x); obj.find(y); obj.select(z); }",
            "}",
        ]
        out = detect_java_db_ops(lines)
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
