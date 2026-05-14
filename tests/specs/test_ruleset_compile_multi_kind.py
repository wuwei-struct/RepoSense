import os, unittest, tempfile, sys, subprocess, json, yaml
class RulesetCompileMultiKindTest(unittest.TestCase):
    def test_compile_multi_kind(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "rulesets"), exist_ok=True)
        open(os.path.join(td, "rulesets", "api_openapi.yaml"), "w", encoding="utf-8").write("spec_version: '1.0'\nid: api_openapi\nconcept: API\ndetector:\n  kind: openapi\nsignals:\n  any_of:\n    openapi:\n      methods: [GET]\n      paths: [/users]\n")
        open(os.path.join(td, "rulesets", "compose_kv.yaml"), "w", encoding="utf-8").write("spec_version: '1.0'\nid: compose_kv\nconcept: KV\ndetector:\n  kind: compose\nsignals:\n  any_of:\n    compose:\n      infra_type: [cache]\n")
        open(os.path.join(td, "rulesets", "sql_storage.yaml"), "w", encoding="utf-8").write("spec_version: '1.0'\nid: sql_storage\nconcept: Storage\ndetector:\n  kind: sql_ddl\nsignals:\n  any_of:\n    sql_ddl:\n      tables: [users]\n")
        open(os.path.join(td, "rulesets", "gha_async.yaml"), "w", encoding="utf-8").write("spec_version: '1.0'\nid: gha_async\nconcept: Workflow\ndetector:\n  kind: gha\nsignals:\n  any_of:\n    gha:\n      item_kind: [scheduling]\n")
        outd = tempfile.mkdtemp(prefix="rs-out-")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "compile", "rulesets", "--specs", td, "--out", outd, "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertTrue(data["ok"])
        rules = yaml.safe_load(open(os.path.join(outd, "rules.yaml"), "r", encoding="utf-8").read())
        kinds = set([r["kind"] for r in rules])
        self.assertTrue({"openapi","compose","sql_ddl","gha"}.issubset(kinds))
