import unittest
from pathlib import Path


class FreshVenvSmokeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path(
            "tools/release/fresh_venv_runtime_smoke.py"
        ).read_text(encoding="utf-8")

    def test_offline_fresh_venv_contract_is_explicit(self):
        self.assertIn('"-m", "venv"', self.text)
        self.assertNotIn("--system-site-packages", self.text)
        self.assertIn('"--no-index"', self.text)
        self.assertIn('"--find-links"', self.text)
        self.assertIn('"pip", "check"', self.text)
        self.assertIn('"PIP_NO_INDEX": "1"', self.text)
        self.assertIn('"PYTHONPATH"', self.text)

    def test_external_identity_and_runtime_surfaces_are_checked(self):
        self.assertIn('"external-cwd"', self.text)
        self.assertIn("source repository appears", self.text)
        self.assertIn('"studio", "serve"', self.text)
        self.assertIn('"learn", "concepts"', self.text)
        self.assertIn('"ci",', self.text)
        self.assertIn('"verify", run_dir, "--strict"', self.text)
        self.assertIn('"gate", run_dir, "--json"', self.text)
        self.assertIn('"context_pack": "pass"', self.text)


if __name__ == "__main__":
    unittest.main()
