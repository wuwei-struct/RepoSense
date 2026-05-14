import os
import unittest


class DemoShowcaseFixtureShapeTest(unittest.TestCase):
    def test_files_present(self):
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "repos", "demo_showcase"))
        req = ["README.md","openapi.yaml","app_fastapi.py","app_flask.py","express_app.js","sql_tx.sql","tasks_celery.py","cache_redis.py","docker-compose.yml",os.path.join(".github","workflows","ci.yml")]
        for r in req:
            self.assertTrue(os.path.isfile(os.path.join(base, r)))


if __name__ == "__main__":
    unittest.main()
