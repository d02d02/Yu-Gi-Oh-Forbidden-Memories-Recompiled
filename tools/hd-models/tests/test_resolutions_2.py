#!/usr/bin/env python3
"""Tests for `choose` resolution function.

The job requires at least four independent assertions.
"""
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys_path = str(HERE.parent)
import sys  # noqa: E402
sys.path.insert(0, sys_path)

import studio
from studio import resolutions

class TestChoose(unittest.TestCase):
    def test_invalid_kind_raises(self):
        finding = {"id": "S5.missing-act", "level": "warn"}
        recipe = {}
        with self.assertRaises(ValueError):
            resolutions.choose(recipe, finding, "invalid-kind")

    def test_returns_new_recipe_not_mutated(self):
        finding = {"id": "S5.missing-act", "level": "warn"}
        recipe = {"resolutions": []}
        new = resolutions.choose(recipe, finding, "provide.glb", extra=1)
        self.assertIsNot(new, recipe)
        self.assertEqual(recipe["resolutions"], [])  # original unchanged
        self.assertEqual(len(new["resolutions"]), 1)
        entry = new["resolutions"][0]
        self.assertEqual(entry["check"], "S5.missing-act")
        self.assertIs(entry["data"].get("extra"), 1)

    def test_replace_existing_entry(self):
        finding = {"id": "S5.missing-act", "level": "warn"}
        recipe = {"resolutions": [{"check": "S5.missing-act", "value": None, "kind": "fallback", "data": {}}]}
        new = resolutions.choose(recipe, finding, "provide.glb", foo="bar")
        self.assertEqual(len(new["resolutions"]), 1)
        entry = new["resolutions"][0]
        self.assertEqual(entry["kind"], "provide.glb")
        self.assertEqual(entry["data"], {"foo": "bar"})

    def test_offered_respects_fail_level(self):
        finding = {"id": "S5.missing-act", "level": "fail"}
        recipe = {}
        # 'accept' should not be offered for fail, so choosing it raises
        with self.assertRaises(ValueError):
            resolutions.choose(recipe, finding, "accept")

if __name__ == "__main__":
    unittest.main()
