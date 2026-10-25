#!/usr/bin/env python3
"""Tests for `chosen` and `is_resolved` resolution functions.

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

class TestChosenAndIsResolved(unittest.TestCase):
    def test_chosen_returns_stored(self):
        finding = {"id": "S5.missing-act", "value": None}
        recipe = {"resolutions": [{"check": "S5.missing-act", "value": None, "kind": "fallback", "data": {"x": 1}}]}
        result = resolutions.chosen(recipe, finding)
        self.assertEqual(result, {"kind": "fallback", "data": {"x": 1}})

    def test_chosen_ack_fallback(self):
        finding = {"id": "S5.missing-act", "value": None}
        recipe = {"acks": [{"check": "S5.missing-act", "value": None}]}
        result = resolutions.chosen(recipe, finding)
        self.assertEqual(result, {"kind": "accept", "data": {}})

    def test_chosen_stored_beats_ack(self):
        finding = {"id": "S5.missing-act", "value": None}
        recipe = {
            "resolutions": [{"check": "S5.missing-act", "value": None, "kind": "fallback", "data": {}}],
            "acks": [{"check": "S5.missing-act", "value": None}]
        }
        result = resolutions.chosen(recipe, finding)
        self.assertEqual(result["kind"], "fallback")

    def test_is_resolved_true_false(self):
        finding = {"id": "S5.missing-act", "value": None}
        recipe1 = {"resolutions": [{"check": "S5.missing-act", "value": None, "kind": "fallback", "data": {}}]}
        recipe2 = {"acks": [{"check": "S5.missing-act", "value": None}]}
        recipe3 = {}
        self.assertTrue(resolutions.is_resolved(recipe1, finding))
        self.assertTrue(resolutions.is_resolved(recipe2, finding))
        self.assertFalse(resolutions.is_resolved(recipe3, finding))

if __name__ == "__main__":
    unittest.main()
