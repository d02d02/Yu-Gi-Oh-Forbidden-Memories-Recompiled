#!/usr/bin/env python3
"""Tests for `use_clip` in resolve_actions.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Ensure the hd-models directory is on sys.path
sys.path.insert(0, str(HERE.parent))

import unittest

import studio.state as state  # noqa: E402
import studio.resolve_actions as ra  # noqa: E402

class TestUseClip(unittest.TestCase):
    def setUp(self):
        self.studio = state.Studio()

    def test_successful_use_clip(self):
        act = "enter"
        clip = "myClip.glb"
        edits = ra.use_clip(self.studio, act, clip)
        self.assertEqual(edits, 2)
        # Verify recipe changes
        self.assertIn(act, self.studio.recipe.get("acts", {}))
        self.assertEqual(self.studio.recipe["acts"][act]["source"], clip)
        # Verify resolution entry
        res_entry = {
            "check": "S5.missing-act",
            "value": act,
            "kind": "provide.glb",
            "data": {"act": act, "clip": clip},
        }
        self.assertIn(res_entry, self.studio.recipe.get("resolutions", []))

    def test_invalid_act(self):
        with self.assertRaises(ValueError):
            ra.use_clip(self.studio, "foo", "clip")
        # Ensure no changes
        self.assertNotIn("foo", self.studio.recipe.get("acts", {}))
        self.assertNotIn("resolutions", self.studio.recipe)

    def test_empty_clip(self):
        with self.assertRaises(ValueError):
            ra.use_clip(self.studio, "enter", "")
        self.assertNotIn("enter", self.studio.recipe.get("acts", {}))
        self.assertNotIn("resolutions", self.studio.recipe)

    def test_undo_restores(self):
        act = "attack"
        clip = "attackClip"
        ra.use_clip(self.studio, act, clip)
        # Undo the two edits
        self.studio.undo()   # one action, one undo
        # After undoing both edits, acts source should be removed and resolutions entry cleared
        self.assertNotIn(act, self.studio.recipe.get("acts", {}))
        self.assertNotIn("resolutions", self.studio.recipe)

if __name__ == "__main__":
    unittest.main()
