#!/usr/bin/env python3
"""Tests for `use_library` in resolve_actions.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Ensure the hd-models directory is on sys.path
sys.path.insert(0, str(HERE.parent))

import unittest

import studio.state as state  # noqa: E402
import studio.resolve_actions as ra  # noqa: E402

class TestUseLibrary(unittest.TestCase):
    def setUp(self):
        self.studio = state.Studio()

    def test_successful_use_library(self):
        act = "enter"
        lib_path = __file__   # any file that exists
        clip = "myClip.glb"
        edits = ra.use_library(self.studio, lib_path, act, clip)
        self.assertEqual(edits, 3)
        # Verify library path set
        self.assertIn("library", self.studio.recipe)
        self.assertEqual(self.studio.recipe["library"]["path"], lib_path)
        # Verify act source set
        self.assertIn(act, self.studio.recipe.get("acts", {}))
        self.assertEqual(self.studio.recipe["acts"][act]["source"], clip)
        # Verify resolution entry
        res_entry = {
            "check": "S5.missing-act",
            "value": act,
            "kind": "provide.library",
            "data": {"act": act, "clip": clip, "path": lib_path},
        }
        self.assertIn(res_entry, self.studio.recipe.get("resolutions", []))

    def test_invalid_act(self):
        with self.assertRaises(ValueError):
            ra.use_library(self.studio, "lib.glb", "foo", "clip")
        self.assertNotIn("foo", self.studio.recipe.get("acts", {}))
        self.assertNotIn("library", self.studio.recipe)
        self.assertNotIn("resolutions", self.studio.recipe)

    def test_empty_clip(self):
        with self.assertRaises(ValueError):
            ra.use_library(self.studio, "lib.glb", "enter", "")
        self.assertNotIn("enter", self.studio.recipe.get("acts", {}))
        self.assertNotIn("library", self.studio.recipe)
        self.assertNotIn("resolutions", self.studio.recipe)

    def test_undo_restores(self):
        act = "attack"
        lib_path = __file__   # any file that exists
        clip = "attackClip"
        ra.use_library(self.studio, lib_path, act, clip)
        # Undo the three edits
        self.studio.undo()   # one action, one undo
        self.assertNotIn(act, self.studio.recipe.get("acts", {}))
        self.assertNotIn("library", self.studio.recipe)
        self.assertNotIn("resolutions", self.studio.recipe)

if __name__ == "__main__":
    unittest.main()
