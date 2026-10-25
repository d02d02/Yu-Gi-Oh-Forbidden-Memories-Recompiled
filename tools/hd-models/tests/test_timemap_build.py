"""Tests for timemap inclusion in model_json_members (py stage)."""
import unittest

import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # add tools/hd-models
sys.path.insert(0, str(HERE))

import recipe as recipe_module


class TestTimemapBuild(unittest.TestCase):
    def _base(self):
        return {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5"},
        }

    def test_timemap_present(self):
        rec = self._base()
        rec["acts"] = {
            "attack": {"source": "Attack", "timemap": [[0, 0], [10, 5], [20, 10]]},
            "idle": {"source": "Idle"},
        }
        result = recipe_module.model_json_members(rec)
        self.assertIn("timemaps", result)
        self.assertEqual(result["timemaps"], [{"act": "attack", "points": [[0, 0], [10, 5], [20, 10]]}])

    def test_timemap_absent(self):
        rec = self._base()
        rec["acts"] = {"idle": {"source": "Idle"}}
        result = recipe_module.model_json_members(rec)
        self.assertNotIn("timemaps", result)

    def test_timemap_non_monotonic(self):
        rec = self._base()
        rec["acts"] = {"attack": {"source": "Attack", "timemap": [[0, 0], [5, 10], [3, 8]]}}
        with self.assertRaises(ValueError):
            recipe_module.model_json_members(rec)

if __name__ == "__main__":
    unittest.main()
