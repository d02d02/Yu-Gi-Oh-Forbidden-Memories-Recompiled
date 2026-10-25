"""Tests for studio/provided.validate_bones().

The tests cover the required behaviours described in JOB.md:
* missing bones → fail findings (one per missing bone, in expected order)
* extra bones → a single warning finding with a comma‑separated list of extra names
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Add the project root (tests/..) and the tools/hd-models directory to sys.path
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import provided  # noqa: E402


class TestValidateBones(unittest.TestCase):
    def test_no_issues(self):
        provided_list = ["hip", "spine"]
        expected = ["hip", "spine"]
        findings = provided.validate_bones(provided_list, expected)
        self.assertEqual(findings, [])

    def test_missing_one(self):
        provided_list = ["hip"]
        expected = ["hip", "spine"]
        findings = provided.validate_bones(provided_list, expected)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "provide.bone-missing")
        self.assertEqual(f["level"], "fail")
        self.assertIn("spine", f["message"])  # message contains missing name

    def test_extra_one(self):
        provided_list = ["hip", "tail"]
        expected = ["hip"]
        findings = provided.validate_bones(provided_list, expected)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "provide.bone-extra")
        self.assertEqual(f["level"], "warn")
        self.assertEqual(f["value"], "tail")

    def test_missing_and_extra(self):
        provided_list = ["hip", "tail"]
        expected = ["hip", "spine"]
        findings = provided.validate_bones(provided_list, expected)
        # Expect two findings: one missing (fail), one extra (warn)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "provide.bone-missing")
        self.assertEqual(findings[1]["id"], "provide.bone-extra")
        self.assertEqual(findings[1]["value"], "tail")

    def test_multiple_extra_sorted(self):
        provided_list = ["tail", "arm"]
        expected = []
        findings = provided.validate_bones(provided_list, expected)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "provide.bone-extra")
        self.assertEqual(f["value"], "arm, tail")
        self.assertEqual(f["level"], "warn")


if __name__ == "__main__":
    unittest.main()
