import hashlib
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.release.offline_wheelhouse import (
    ALLOWED_PACKAGES,
    EXPECTED_DIRECT,
    OFFICIAL_INDEX,
    WheelhouseError,
    _environment_contract,
    normalize_name,
    verify_wheelhouse,
)


VERSIONS = {
    "certifi": "1.0",
    "charset-normalizer": "1.0",
    "idna": "1.0",
    "pyyaml": "1.0",
    "requests": "1.0",
    "urllib3": "1.0",
}
TEMP_ROOT = Path(".tmp_test_runs/temp")


class OfflineWheelhouseVerifierTest(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=TEMP_ROOT)
        self.root = Path(self.temp.name)
        self.downloads = self.root / "downloads"
        self.downloads.mkdir()
        self.lock_path = self.root / "lock.json"
        self.lock = self._create_valid_wheelhouse()

    def tearDown(self):
        self.temp.cleanup()

    def _write_wheel(self, name, version, requires=()):
        distribution = name.replace("-", "_")
        filename = f"{distribution}-{version}-py3-none-any.whl"
        path = self.downloads / filename
        metadata = [
            "Metadata-Version: 2.1",
            f"Name: {name}",
            f"Version: {version}",
        ]
        metadata.extend(f"Requires-Dist: {item}" for item in requires)
        metadata.append("")
        dist_info = f"{distribution}-{version}.dist-info"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(f"{dist_info}/METADATA", "\n".join(metadata))
            archive.writestr(
                f"{dist_info}/WHEEL",
                "Wheel-Version: 1.0\nGenerator: test\n"
                "Root-Is-Purelib: true\nTag: py3-none-any\n",
            )
        return path

    def _create_valid_wheelhouse(self):
        requirements = {
            "requests": (
                "certifi>=1",
                "charset-normalizer>=1",
                "idna>=1",
                "urllib3>=1",
            )
        }
        entries = []
        for normalized_name in sorted(ALLOWED_PACKAGES):
            display_name = "PyYAML" if normalized_name == "pyyaml" else normalized_name
            path = self._write_wheel(
                display_name,
                VERSIONS[normalized_name],
                requirements.get(normalized_name, ()),
            )
            dependencies = [
                {
                    "normalized_name": normalize_name(item.split(">=")[0]),
                    "specifier": ">=1",
                }
                for item in requirements.get(normalized_name, ())
            ]
            entries.append(
                {
                    "name": display_name,
                    "normalized_name": normalized_name,
                    "exact_version": VERSIONS[normalized_name],
                    "filename": path.name,
                    "wheel_tags": ["py3-none-any"],
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "dependency_type": (
                        "direct"
                        if normalized_name in EXPECTED_DIRECT
                        else "transitive"
                    ),
                    "expected_source": OFFICIAL_INDEX,
                    "dependencies": dependencies,
                }
            )
        lock = {
            "schema_version": 1,
            **_environment_contract(),
            "repo_wheel_version": "0.1.0",
            "forbidden_sdist": True,
            "expected_source": OFFICIAL_INDEX,
            "packages": entries,
        }
        self.lock_path.write_text(
            json.dumps(lock, indent=2) + "\n", encoding="utf-8"
        )
        return lock

    def test_valid_wheelhouse_passes(self):
        result = verify_wheelhouse(self.root, self.lock_path)
        self.assertEqual(result["wheelhouse_integrity"], "pass")
        self.assertEqual(result["dependency_closure"], "pass")
        self.assertEqual(result["package_count"], 6)

    def test_missing_wheel_fails(self):
        (self.downloads / self.lock["packages"][0]["filename"]).unlink()
        with self.assertRaisesRegex(WheelhouseError, "files missing"):
            verify_wheelhouse(self.root, self.lock_path)

    def test_hash_mismatch_fails(self):
        path = self.downloads / self.lock["packages"][0]["filename"]
        path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaisesRegex(WheelhouseError, "hash mismatch"):
            verify_wheelhouse(self.root, self.lock_path)

    def test_extra_wheel_fails(self):
        source = self.downloads / self.lock["packages"][0]["filename"]
        shutil.copy2(source, self.downloads / "extra-1.0-py3-none-any.whl")
        with self.assertRaisesRegex(WheelhouseError, "unexpected wheelhouse files"):
            verify_wheelhouse(self.root, self.lock_path)

    def test_sdist_fails(self):
        (self.downloads / "requests-1.0.tar.gz").write_bytes(b"not allowed")
        with self.assertRaisesRegex(WheelhouseError, "non-wheel files rejected"):
            verify_wheelhouse(self.root, self.lock_path)

    def test_metadata_version_mismatch_fails(self):
        self.lock["packages"][0]["exact_version"] = "2.0"
        self.lock_path.write_text(
            json.dumps(self.lock, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(WheelhouseError, "version mismatch"):
            verify_wheelhouse(self.root, self.lock_path)


if __name__ == "__main__":
    unittest.main()
