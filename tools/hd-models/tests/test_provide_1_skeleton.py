"""Tests for tools/hd-models/studio/provide.skeleton_of().

Covers:
- Successful extraction of names and pose from a generated humanoid GLB.
- Correct handling of unreadable (non‑existent) files.
- Pose values correspond to the bone definitions (position matches, rotation identity, scale 1.0).
"""
import sys
import unittest
import tempfile
from pathlib import Path

# Add project root and tools/hd-models to import path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))  # project root
sys.path.insert(0, str(HERE.parent))         # tools/hd-models

from studio import provide as provide_mod
from studio import corpus

class TestSkeletonOf(unittest.TestCase):
    def test_successful_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            glb_path = Path(td) / "humanoid.glb"
            bones = corpus.humanoid_bones()
            corpus.write_glb(glb_path, bones, skinned=True, clips=False, meshes=1)
            names, pose = provide_mod.skeleton_of(glb_path)
            # Expect names to match the bone list order
            expected_names = [b[0] for b in bones]
            self.assertEqual(names, expected_names)
            # Verify pose entries exist and have correct structure
            for name, _, pos in bones:
                self.assertIn(name, pose)
                entry = pose[name]
                self.assertEqual(entry["pos"], tuple(float(v) for v in pos))
                # Default rotation is identity quaternion
                self.assertEqual(entry["rot"], (0.0, 0.0, 0.0, 1.0))
                # Scale should be 1.0 (average of (1,1,1))
                self.assertAlmostEqual(entry["scale"], 1.0)

    def test_unreadable_file(self):
        # Pass a non‑existent path; expect AuditError to be raised by skeleton_of
        with self.assertRaises(Exception):
            provide_mod.skeleton_of(Path("/nonexistent/path.glb"))

    def test_check_provided_unreadable(self):
        # Provide an unreadable file to check_provided; should return a single unreadable finding.
        findings = provide_mod.check_provided("dummy_model.glb", "/nonexistent/file.glb")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "provide.unreadable")
        self.assertEqual(findings[0]["level"], "fail")

if __name__ == "__main__":
    unittest.main()
