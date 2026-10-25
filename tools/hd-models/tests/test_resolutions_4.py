#!/usr/bin/env python3
"""Tests for `stand_ins` resolution function.

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


class TestStandIns(unittest.TestCase):
    def test_empty_returns_empty(self):
        recipe = {}
        self.assertEqual(resolutions.stand_ins(recipe), [])

    def test_filters_fallback_and_accept(self):
        recipe = {
            "resolutions": [
                {"kind": "fallback", "check": "S3.dropped"},
                {"kind": "provide.file", "check": "S1.skin"},
                {"kind": "accept", "check": "S5.missing-act"},
                {"kind": "text", "check": "S0.attribution"},
            ]
        }
        result = resolutions.stand_ins(recipe)
        self.assertEqual(len(result), 2)
        kinds = [e["kind"] for e in result]
        self.assertListEqual(kinds, ["fallback", "accept"])

    def test_preserves_order(self):
        recipe = {
            "resolutions": [
                {"kind": "accept", "check": "A"},
                {"kind": "fallback", "check": "B"},
                {"kind": "accept", "check": "C"},
            ]
        }
        result = resolutions.stand_ins(recipe)
        self.assertListEqual([e["kind"] for e in result], ["accept", "fallback", "accept"])


if __name__ == "__main__":
    unittest.main()
