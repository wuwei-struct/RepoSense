import os, unittest, yaml
def tax_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "specs", "taxonomies"))
class TaxonomyEnumsTest(unittest.TestCase):
    def test_categories_cover_required(self):
        with open(os.path.join(tax_dir(), "categories.yaml"), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cats = [c.get("id") for c in data.get("categories", [])]
        required = {"async","concurrency","consistency","integration","observability","reliability","storage"}
        self.assertTrue(required.issubset(set(cats)))
        self.assertEqual(len(cats), len(set(cats)))
