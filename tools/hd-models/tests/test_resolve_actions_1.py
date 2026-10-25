#!/usr/bin/env python3
"""Tests for tools/hd-models/studio/resolve_actions.py (missing_act_finding).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Add the tools/hd-models directory to sys.path so we can import studio.resolve_actions
sys.path.insert(0, str(HERE.parent))

import unittest

# Import the module under test
import studio.resolve_actions as ra  # noqa: E402


class TestMissingActFinding(unittest.TestCase):
    def test_idle_finding(self):
        f = ra.missing_act_finding("idle")
        self.assertEqual(f["id"], "S5.missing-act")
        self.assertEqual(f["level"], "fail")
        self.assertIsNone(f["value"])  # idle => value None

    def test_nonidle_finding(self):
        act = "enter"
        f = ra.missing_act_finding(act)
        self.assertEqual(f["id"], "S5.missing-act")
        self.assertEqual(f["level"], "warn")
        self.assertEqual(f["value"], act)

    def test_invalid_act(self):
        with self.assertRaises(ValueError):
            ra.missing_act_finding("foo")


if __name__ == "__main__":
    unittest.main()
