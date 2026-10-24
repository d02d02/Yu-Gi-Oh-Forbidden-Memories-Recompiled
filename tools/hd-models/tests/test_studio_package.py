"""Tests for studio/package.py (S9 package checks)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import audit, package


class TestParse(unittest.TestCase):
    def test_parse_native_check_errors_and_warnings(self):
        text = (
            "error: mymod/model1.hdm: bad vertex count\n"
            "warning: mymod/model2.hdm: high triangle count\n"
            "mymod: 12.5 MB for all its models, if they all show (the game's budget: 512 MB)\n"
            "2 errors, 1 warnings\n"
        )
        parsed = package.parse_native_check(text)
        self.assertEqual(parsed["errors"], [("mymod/model1.hdm", "bad vertex count")])
        self.assertEqual(parsed["warnings"], [("mymod/model2.hdm", "high triangle count")])
        self.assertEqual(parsed["total_mb"], 12.5)
        self.assertEqual(parsed["budget_mb"], 512)

    def test_parse_native_check_blank(self):
        parsed = package.parse_native_check("")
        self.assertEqual(parsed["errors"], [])
        self.assertEqual(parsed["warnings"], [])
        self.assertIsNone(parsed["total_mb"])
        self.assertIsNone(parsed["budget_mb"])

    def test_parse_native_check_ignores_descriptive(self):
        text = (
            "mymod/model1.hdm: 5000 vertices, 10000 triangles, 32 bones, 3 clips, 2.1 MB\n"
            "  bind pose: 180 game units tall, soles -90 below the root, 80 wide, 60 deep\n"
            "  clip idle: 60 frames at 30 fps\n"
            "mymod: 2.1 MB for all its models, if they all show (the game's budget: 512 MB)\n"
            "0 errors, 0 warnings\n"
        )
        parsed = package.parse_native_check(text)
        self.assertEqual(parsed["errors"], [])
        self.assertEqual(parsed["warnings"], [])
        self.assertEqual(parsed["total_mb"], 2.1)
        self.assertEqual(parsed["budget_mb"], 512)


class TestNativeCheck(unittest.TestCase):
    def test_check_native_errors_and_warnings(self):
        parsed = {
            "errors": [("mymod/model1.hdm", "bad vertex count")],
            "warnings": [("mymod/model2.hdm", "high triangle count")],
            "total_mb": 12.5,
            "budget_mb": 512,
        }
        findings = package.check_native(parsed)
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]["id"], "S9.native_check")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertEqual(findings[0]["message"], "mymod/model1.hdm: bad vertex count")
        self.assertEqual(findings[0]["fix"], "Open the stage named in the message.")
        self.assertEqual(findings[0]["value"], "mymod/model1.hdm")
        self.assertEqual(findings[1]["level"], "warn")
        self.assertEqual(findings[1]["message"], "mymod/model2.hdm: high triangle count")

    def test_check_native_clean(self):
        parsed = package.parse_native_check("")
        self.assertEqual(package.check_native(parsed), [])

    def test_check_native_only_warnings(self):
        parsed = {
            "errors": [],
            "warnings": [("mymod/model2.hdm", "high triangle count")],
            "total_mb": None,
            "budget_mb": None,
        }
        findings = package.check_native(parsed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["level"], "warn")
        self.assertEqual(findings[0]["id"], "S9.native_check")


class TestBudget(unittest.TestCase):
    def test_check_budget_fail_over_budget(self):
        parsed = {"total_mb": 600.0, "budget_mb": 512}
        findings = package.check_budget(parsed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S9.budget")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertEqual(findings[0]["message"], "Native models use 600.0 MB of 512 MB.")
        self.assertEqual(findings[0]["fix"], "Lower the atlas or triangle count.")

    def test_check_budget_warn_at_80_percent(self):
        parsed = {"total_mb": 410.0, "budget_mb": 512}
        findings = package.check_budget(parsed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["level"], "warn")
        self.assertEqual(findings[0]["message"], "Native models use 410.0 MB of 512 MB.")

    def test_check_budget_clean_below_80(self):
        parsed = {"total_mb": 400.0, "budget_mb": 512}
        findings = package.check_budget(parsed)
        self.assertEqual(findings, [])

    def test_check_budget_none_values(self):
        parsed = {"total_mb": None, "budget_mb": None}
        findings = package.check_budget(parsed)
        self.assertEqual(findings, [])


class TestIdentical(unittest.TestCase):
    def test_check_identical_equal(self):
        build_a = [("a.hdm", "abc"), ("b.hdm", "def")]
        build_b = [("a.hdm", "abc"), ("b.hdm", "def")]
        self.assertEqual(package.check_identical(build_a, build_b), [])

    def test_check_identical_differ(self):
        build_a = [("a.hdm", "abc"), ("b.hdm", "def")]
        build_b = [("a.hdm", "abc"), ("c.hdm", "xyz")]
        findings = package.check_identical(build_a, build_b)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S9.identical")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertEqual(findings[0]["message"], "2 file(s) differ between two builds.")
        self.assertEqual(findings[0]["fix"], "Report this: the recipe is not deterministic.")
        self.assertEqual(findings[0]["value"], ["b.hdm", "c.hdm"])

class TestProvenance(unittest.TestCase):
    def test_check_provenance_all_present(self):
        meta = {"author": "Jane", "license": "MIT", "url": "http://example.com"}
        self.assertEqual(package.check_provenance(meta), [])

    def test_check_provenance_missing_key(self):
        meta = {"author": "Jane", "license": "MIT"}
        findings = package.check_provenance(meta)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], "S9.provenance")
        self.assertEqual(findings[0]["level"], "fail")
        self.assertEqual(findings[0]["message"], "Missing url.")
        self.assertEqual(findings[0]["fix"], "Fill S0.")

    def test_check_provenance_empty_value(self):
        meta = {"author": "  ", "license": "MIT", "url": "http://example.com"}
        findings = package.check_provenance(meta)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["message"], "Missing author.")

    def test_valid_package_name_valid(self):
        self.assertTrue(package.valid_package_name("my_mod-01"))

    def test_valid_package_name_empty(self):
        self.assertFalse(package.valid_package_name(""))

    def test_valid_package_name_too_long(self):
        self.assertFalse(package.valid_package_name("a" * 65))
        self.assertTrue(package.valid_package_name("a" * 64))

    def test_valid_package_name_starts_with_dash(self):
        self.assertFalse(package.valid_package_name("-bad"))

    def test_valid_package_name_invalid_chars(self):
        self.assertFalse(package.valid_package_name("bad.name!"))



if __name__ == "__main__":
    unittest.main()