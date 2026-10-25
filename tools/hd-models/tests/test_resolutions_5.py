#!/usr/bin/env python3
"""Tests for round‑trip JSON handling and distinct choices for same id.

The job requires at least two independent assertions.
"""

import unittest
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(HERE.parent))

import studio
from studio import resolutions

class TestRoundTripAndSeparateChoices(unittest.TestCase):
    def setUp(self):
        # Base empty recipe
        self.base_recipe = {}
        # Two findings with same id but different values
        self.finding1 = {"id": "S5.missing-act", "level": "warn", "value": "v1"}
        self.finding2 = {"id": "S5.missing-act", "level": "warn", "value": "v2"}

    def test_round_trip_keeps_chosen(self):
        # Choose a resolution for finding1
        recipe1 = resolutions.choose(self.base_recipe, self.finding1, "provide.glb")
        # Round‑trip through JSON
        loaded = json.loads(json.dumps(recipe1))
        # The chosen resolution should be preserved
        chosen = resolutions.chosen(loaded, self.finding1)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.get("kind"), "provide.glb")

    def test_separate_choices_same_id(self):
        # Choose for both findings, sequentially (non‑mutating)
        recipe1 = resolutions.choose(self.base_recipe, self.finding1, "provide.glb")
        recipe2 = resolutions.choose(recipe1, self.finding2, "provide.library")
        # Both choices should be stored separately
        chosen1 = resolutions.chosen(recipe2, self.finding1)
        chosen2 = resolutions.chosen(recipe2, self.finding2)
        self.assertIsNotNone(chosen1)
        self.assertIsNotNone(chosen2)
        # Ensure the two stored choices are distinct objects
        self.assertNotEqual(chosen1, chosen2)
        self.assertEqual(chosen1.get("kind"), "provide.glb")
        self.assertEqual(chosen2.get("kind"), "provide.library")

if __name__ == "__main__":
    unittest.main()
