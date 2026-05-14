import os
import tempfile
import unittest
from reposense.versioning import ruleset_fingerprint


class RulesetFingerprintStableTest(unittest.TestCase):
    def test_line_endings_and_comments(self):
        d = tempfile.mkdtemp(prefix="ruleset_fp_")
        p = os.path.join(d, "rules.yaml")
        open(p, "wb").write(b"key: value\r\n# comment\r\nanother: x\r\n")
        fp1 = ruleset_fingerprint(d)
        open(p, "wb").write(b"key: value\n# comment changed\nanother: x\n")
        fp2 = ruleset_fingerprint(d)
        self.assertEqual(fp1, fp2)


if __name__ == "__main__":
    unittest.main()
