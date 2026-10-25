"""Tests for studio.provide.record().

Covers:
- Successful recording when no fail findings are present, adding a provide.file resolution with correct path and SHA256.
- Raising ValueError when fail findings are present.
"""
import sys
import unittest
import tempfile
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Add project root and tools/hd-models to sys.path
sys.path.insert(0, str(HERE.parent.parent))  # project root
sys.path.insert(0, str(HERE.parent))         # tools/hd-models

from studio import provide as provide_mod
from studio import resolutions

class TestRecord(unittest.TestCase):
    def test_successful_record_adds_resolution(self):
        # Prepare a temporary file to act as the provided glb
        with tempfile.TemporaryDirectory() as td:
            glb_path = Path(td) / "file.glb"
            glb_path.write_bytes(b"dummy content")
            # Simple recipe placeholder
            recipe = {}
            # Finding that offers "provide.file"
            finding = {"id": "S5.missing-act", "level": "info"}
            # No fail findings
            findings = []
            new_recipe = provide_mod.record(recipe, finding, glb_path, findings)
            # Verify resolution entry
            self.assertIn("resolutions", new_recipe)
            self.assertEqual(len(new_recipe["resolutions"]), 1)
            entry = new_recipe["resolutions"][0]
            self.assertEqual(entry["kind"], "provide.file")
            self.assertEqual(entry["check"], finding["id"])  # value is None by default
            self.assertEqual(entry["value"], None)
            # Data should contain path and correct sha256
            expected_sha = hashlib.sha256(glb_path.read_bytes()).hexdigest()
            self.assertEqual(entry["data"]["path"], str(glb_path))
            self.assertEqual(entry["data"]["sha256"], expected_sha)

    def test_record_raises_on_fail_findings(self):
        with tempfile.TemporaryDirectory() as td:
            glb_path = Path(td) / "file.glb"
            glb_path.write_bytes(b"dummy")
            recipe = {}
            finding = {"id": "S5.missing-act", "level": "info"}
            # Include a fail finding
            fail_finding = {"id": "provide.bone-missing", "level": "fail", "message": "missing", "fix": ""}
            findings = [fail_finding]
            with self.assertRaises(ValueError):
                provide_mod.record(recipe, finding, glb_path, findings)

if __name__ == "__main__":
    unittest.main()
