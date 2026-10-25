import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import provided as provided_mod

class TestValidateRestPose(unittest.TestCase):
    def setUp(self):
        # Expected pose with three bones
        self.expected = {
            "hip": {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "spine": {"pos": (0.1, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "head": {"pos": (0.2, 0.1, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
        }

    def test_identical(self):
        prov_data = self.expected.copy()
        findings = provided_mod.validate_rest_pose(prov_data, self.expected)
        self.assertEqual(findings, [])

    def test_position_tolerance(self):
        prov_data = {
            "hip": {"pos": (0.03, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "spine": {"pos": (0.1, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "head": {"pos": (0.2, 0.1, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
        }
        findings = provided_mod.validate_rest_pose(prov_data, self.expected)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["value"], "hip")

    def test_rotation_tolerance(self):
        prov_data = {
            "hip": {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 0.9)},
            "spine": {"pos": (0.1, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "head": {"pos": (0.2, 0.1, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
        }
        findings = provided_mod.validate_rest_pose(prov_data, self.expected)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["value"], "hip")

    def test_quaternion_sign_flip(self):
        prov_data = {
            "hip": {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, -1.0)},
            "spine": {"pos": (0.1, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, -1.0)},
            "head": {"pos": (0.2, 0.1, 0.0), "rot": (0.0, 0.0, 0.0, -1.0)},
        }
        findings = provided_mod.validate_rest_pose(prov_data, self.expected)
        # sign flip should make rotations match, no findings
        self.assertEqual(findings, [])

    def test_missing_and_extra_bones_ignored(self):
        prov_data = {
            "hip": {"pos": (0.0, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "spine": {"pos": (0.1, 0.0, 0.0), "rot": (0.0, 0.0, 0.0, 1.0)},
            "extra": {"pos": (1,1,1), "rot": (0,0,0,1)},
        }
        findings = provided_mod.validate_rest_pose(prov_data, self.expected)
        # only common bone 'hip' and 'spine' match, extra and missing ignored => no findings
        self.assertEqual(findings, [])

if __name__ == "__main__":
    unittest.main()
