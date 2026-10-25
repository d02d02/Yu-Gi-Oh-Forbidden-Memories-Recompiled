"""Tests for studio/provided.validate() and fail_count().

Covers combination of bone and pose validations and counting fails.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import provided as provided_mod

class TestValidateAndFailCount(unittest.TestCase):
    def test_combined_fail_and_warn(self):
        # provided missing a bone (fail) and extra bone (warn)
        provided_bones = ["hip", "tail"]
        expected_bones = ["hip", "spine"]
        # pose matches for common bone, no pose warnings
        pose = {
            "hip": {"pos": (0, 0, 0), "rot": (0, 0, 0, 1)},
        }
        expected_pose = pose.copy()
        findings = provided_mod.validate(provided_bones, pose, expected_bones, expected_pose)
        # expect two findings: one fail bone-missing, one warn bone-extra
        self.assertEqual(len(findings), 2)
        ids = [f["id"] for f in findings]
        self.assertIn("provide.bone-missing", ids)
        self.assertIn("provide.bone-extra", ids)
        self.assertEqual(provided_mod.fail_count(findings), 1)

    def test_pose_warning_and_no_fails(self):
        # bones match, but pose differs => warning, no fails
        bones = ["hip", "spine"]
        expected_bones = ["hip", "spine"]
        provided_pose = {
            "hip": {"pos": (0.03, 0, 0), "rot": (0, 0, 0, 1)},  # position diff > tol
            "spine": {"pos": (0, 0, 0), "rot": (0, 0, 0, 1)},
        }
        expected_pose = {
            "hip": {"pos": (0, 0, 0), "rot": (0, 0, 0, 1)},
            "spine": {"pos": (0, 0, 0), "rot": (0, 0, 0, 1)},
        }
        findings = provided_mod.validate(bones, provided_pose, expected_bones, expected_pose)
        # one warning from pose, no bone warnings/fails
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "provide.rest-pose")
        self.assertEqual(provided_mod.fail_count(findings), 0)

if __name__ == "__main__":
    unittest.main()
