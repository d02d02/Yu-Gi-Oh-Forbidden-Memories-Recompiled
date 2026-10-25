#!/usr/bin/env python3
"""Tests for `offered` resolution catalogue.

The job requires at least four independent assertions.
"""
import unittest
from pathlib import Path

# Add the package root (tools/hd-models) to sys.path, as other tests do.
HERE = Path(__file__).resolve().parent
sys_path = str(HERE.parent)
import sys  # noqa: E402
sys.path.insert(0, sys_path)

import studio
from studio import resolutions


class TestOffered(unittest.TestCase):
    def test_fail_removes_accept(self):
        finding = {"id": "S5.missing-act", "level": "fail"}
        kinds = resolutions.offered(finding)
        self.assertNotIn("accept", kinds)
        # The other expected kinds should still be present.
        for k in ["provide.glb", "provide.library", "provide.file", "fallback"]:
            self.assertIn(k, kinds)

    def test_warn_includes_accept(self):
        finding = {"id": "S5.missing-act", "level": "warn"}
        kinds = resolutions.offered(finding)
        self.assertIn("accept", kinds)
        # Full catalogue length should be 5 for this ID.
        self.assertEqual(len(kinds), 5)

    def test_unknown_id_returns_empty(self):
        finding = {"id": "unknown.id", "level": "warn"}
        self.assertEqual(resolutions.offered(finding), [])

    def test_pick_kind(self):
        finding = {"id": "S0.category", "level": "info"}
        self.assertEqual(resolutions.offered(finding), ["pick"])


if __name__ == "__main__":
    unittest.main()
