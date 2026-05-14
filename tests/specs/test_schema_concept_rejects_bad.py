import os, unittest, tempfile, yaml, json, subprocess, sys
class SchemaConceptRejectsBadTest(unittest.TestCase):
    def test_rejects_missing_field(self):
        td = tempfile.mkdtemp(prefix="specs-")
        os.makedirs(os.path.join(td, "concepts"), exist_ok=True)
        os.makedirs(os.path.join(td, "taxonomies"), exist_ok=True)
        open(os.path.join(td, "taxonomies", "categories.yaml"), "w", encoding="utf-8").write("categories:\n  - concurrency\n")
        # bad concept: missing definition.what and extra field
        open(os.path.join(td, "concepts", "bad.yaml"), "w", encoding="utf-8").write("spec_version: '1.0'\nid: concurrency.bad\ntitle: Bad\ncategory: concurrency\nlevel: core\nstability: stable\ndefinition: {}\nunknown_field: x\n")
        res = subprocess.run([sys.executable, "-m", "reposense", "specs", "check", "--specs", td, "--strict-schema", "--json"], stdout=subprocess.PIPE)
        data = json.loads(res.stdout.decode("utf-8"))
        self.assertFalse(data["ok"])
        msg = "\n".join(data["errors"])
        self.assertTrue("required" in msg or "additionalProperties" in msg or "jsonschema_missing" in msg or "schema_missing" in msg)
