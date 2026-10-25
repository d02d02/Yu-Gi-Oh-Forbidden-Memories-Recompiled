"""Tests for studio.provide.check_provided().

Covers:
- Same skeleton returns no findings.
- Skeleton with a dropped bone returns a provide.bone-missing fail finding.
"""
import sys
import unittest
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# add project root and tools/hd-models to sys.path
sys.path.insert(0, str(HERE.parent.parent))  # project root
sys.path.insert(0, str(HERE.parent))         # tools/hd-models

from studio import provide as provide_mod
from studio import corpus

class TestCheckProvided(unittest.TestCase):
    def test_same_skeleton_no_findings(self):
        with tempfile.TemporaryDirectory() as td:
            model_path = Path(td) / "model.glb"
            provided_path = Path(td) / "provided.glb"
            bones = corpus.humanoid_bones()
            # write identical glb for model and provided
            corpus.write_glb(model_path, bones, skinned=True, clips=False, meshes=1)
            corpus.write_glb(provided_path, bones, skinned=True, clips=False, meshes=1)
            findings = provide_mod.check_provided(model_path, provided_path)
            self.assertEqual(findings, [])

    def test_dropped_bone_missing_finding(self):
        with tempfile.TemporaryDirectory() as td:
            model_path = Path(td) / "model.glb"
            provided_path = Path(td) / "provided.glb"
            full_bones = corpus.humanoid_bones()
            dropped_bones = corpus._drop_bones(full_bones, ("hand_r",))
            corpus.write_glb(model_path, full_bones, skinned=True, clips=False, meshes=1)
            corpus.write_glb(provided_path, dropped_bones, skinned=True, clips=False, meshes=1)
            findings = provide_mod.check_provided(model_path, provided_path)
            # Expect at least one fail finding with id provide.bone-missing
            self.assertTrue(any(f.get("id") == "provide.bone-missing" and f.get("level") == "fail" for f in findings))

    def test_unreadable_provided_file(self):
        with tempfile.TemporaryDirectory() as td:
            model_path = Path(td) / "model.glb"
            provided_path = Path(td) / "nonexistent.glb"
            bones = corpus.humanoid_bones()
            corpus.write_glb(model_path, bones, skinned=True, clips=False, meshes=1)
            # do not create provided file
            findings = provide_mod.check_provided(model_path, provided_path)
            self.assertTrue(any(f.get("id") == "provide.unreadable" for f in findings))

if __name__ == "__main__":
    unittest.main()
