#!/usr/bin/env python3
"""Tests for tools/hd-models/recipe.py (pure Python, stdlib only)."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys_path = str(HERE.parent)
import sys  # noqa: E402  (must be inserted before import recipe)
sys.path.insert(0, sys_path)

import recipe  # noqa: E402
import native_spec as spec  # noqa: E402

recipe_module = recipe


class TestLoad(unittest.TestCase):
    """load() reads dicts and JSON files, returns a deep copy, and rejects bad recipes."""

    def test_load_from_dict_returns_deep_copy(self):
        source = {"schema": 1, "source": {"path": "dragon.glb"}}
        result = recipe.load(source)
        self.assertEqual(result, source)
        self.assertIsNot(result, source)
        self.assertIsNot(result["source"], source["source"])

    def test_load_from_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "recipe.json")
            path.write_text(json.dumps({"schema": 1, "source": {"path": "x.glb"}}))
            result = recipe.load(str(path))
            self.assertEqual(result["schema"], 1)
            self.assertEqual(result["source"]["path"], "x.glb")

    def test_load_from_path_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "recipe.json")
            path.write_text(json.dumps({"schema": 1}))
            result = recipe.load(path)
            self.assertEqual(result, {"schema": 1})

    def test_load_returns_deep_copy(self):
        source = {"schema": 1, "source": {"path": "a.glb"}}
        result = recipe.load(source)
        source["source"]["path"] = "mutated"
        self.assertEqual(result["source"]["path"], "a.glb")

    def test_load_not_json_object_raises(self):
        with self.assertRaises(recipe.RecipeError):
            recipe.load("not an object")  # str: treated as path -> file missing
        # A JSON list is not an object
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "r.json")
            path.write_text(json.dumps([1, 2, 3]))
            with self.assertRaises(recipe.RecipeError):
                recipe.load(path)

    def test_load_schema_missing_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "r.json")
            path.write_text(json.dumps({"source": {"path": "a.glb"}}))
            with self.assertRaises(recipe.RecipeError):
                recipe.load(path)

    def test_load_schema_not_int_raises(self):
        with self.assertRaises(recipe.RecipeError):
            recipe.load({"schema": "1", "source": {"path": "a.glb"}})

    def test_load_schema_below_one_raises(self):
        with self.assertRaises(recipe.RecipeError):
            recipe.load({"schema": 0})

    def test_load_schema_above_one_raises(self):
        with self.assertRaises(recipe.RecipeError):
            recipe.load({"schema": 2})

    def test_load_newer_schema_message_contains_newer_studio(self):
        with self.assertRaisesRegex(recipe.RecipeError, "newer"):
            recipe.load({"schema": 3})

    def test_load_invalid_json_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "r.json")
            path.write_text("{not valid json")
            with self.assertRaises(recipe.RecipeError):
                recipe.load(path)

    def test_load_missing_file_raises(self):
        with self.assertRaises(recipe.RecipeError):
            recipe.load("/nonexistent/path/recipe.json")


class TestCanonicalJson(unittest.TestCase):
    """canonical_json writes sorted keys, whole floats as ints, with trailing newline."""

    def test_sorted_keys_and_indent(self):
        recipe_in = {"source": {"path": "b"}, "schema": 1, "a": 2}
        out = recipe.canonical_json(recipe_in)
        self.assertIn("  \"a\": 2,", out)
        self.assertIn("  \"schema\": 1,", out)

    def test_whole_float_becomes_int(self):
        # 3.0 becomes 3, but 3.5 stays
        source = {"schema": 1, "value": 3.0, "frac": 3.5, "zzz": 4}
        out = recipe.canonical_json(source)
        self.assertIn("\"value\": 3", out)
        self.assertIn("\"value\": 3,\n", out)  # not 3.0
        self.assertIn("\"frac\": 3.5", out)

    def test_trailing_newline(self):
        out = recipe.canonical_json({"schema": 1})
        self.assertTrue(out.endswith("\n"))


class TestValidateBasic(unittest.TestCase):
    """validate(): top level, source, model, meta rules."""

    def _find(self, path, findings):
        return [f for f in findings if f["path"] == path]

    def test_valid_recipe_clean(self):
        recipe = {
            "schema": 1,
            "source": {"path": "dragon.glb"},
            "model": {"category": "C5"},
            "meta": {"author": "me", "license": "CC-BY-4.0"},
        }
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_validate_clean(self):
        recipe = {
            "schema": 1,
            "source": {"path": "dragon.glb"},
            "model": {"category": "C5"},
            "meta": {"author": "me", "license": "CC-BY-4.0"},
        }
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_missing_source_error(self):
        recipe = {"schema": 1, "model": {"category": "C5"}}
        errs = self._find("source", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["level"], "error")

    def test_missing_model_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}}
        errs = self._find("model", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["level"], "error")

    def test_unknown_top_key_warn(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5"}, "bogus": 1}
        warns = self._find("bogus", recipe_module.validate(recipe))
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["level"], "warn")

    def test_source_path_empty_error(self):
        recipe = {"schema": 1, "source": {"path": ""}, "model": {"category": "C5"}}
        errs = self._find("source.path", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["level"], "error")

    def test_source_path_not_str_error(self):
        recipe = {"schema": 1, "source": {"path": 5}, "model": {"category": "C5"}}
        errs = self._find("source.path", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_source_path_missing_error(self):
        recipe = {"schema": 1, "source": {}, "model": {"category": "C5"}}
        errs = self._find("source.path", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_source_sha256_bad_hex_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb", "sha256": "nothex"}, "model": {"category": "C5"}}
        errs = self._find("source.sha256", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["level"], "error")

    def test_source_sha256_valid_ok(self):
        recipe = {"schema": 1, "source": {"path": "x.glb", "sha256": "a" * 64}, "model": {"category": "C5"}}
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_source_skin_not_str_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb", "skin": 5}, "model": {"category": "C5"}}
        errs = self._find("source.skin", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_source_meshes_not_list_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb", "meshes": "not a list"}, "model": {"category": "C5"}}
        errs = self._find("source.meshes", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_source_meshes_non_str_entry_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb", "meshes": [5]}, "model": {"category": "C5"}}
        errs = self._find("source.meshes", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_category_missing_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {}}
        errs = self._find("model.category", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0]["level"], "error")

    def test_model_category_invalid_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C9"}}
        errs = self._find("model.category", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_category_valid(self):
        for cat in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
            recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": cat}}
            self.assertEqual(recipe_module.validate(recipe), [], f"category {cat} should be valid")

    def test_model_name_empty_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "name": ""}}
        errs = self._find("model.name", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_name_valid(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "name": "Dragon"}}
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_model_cards_negative_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "cards": [0]}}
        errs = self._find("model.cards", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_cards_duplicate_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "cards": [1, 1]}}
        errs = self._find("model.cards", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_cards_too_many_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "cards": list(range(1, spec.REGISTRY_CARDS + 2))}}
        errs = self._find("model.cards", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_model_cards_valid(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5", "cards": [1, 5, 10]}}
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_meta_license_empty_warn(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5"}, "meta": {"license": ""}}
        warns = self._find("meta.license", recipe_module.validate(recipe))
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["level"], "warn")
        self.assertIn("licence is empty", warns[0]["message"])

    def test_meta_license_missing_warn(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5"}, "meta": {}}
        warns = self._find("meta.license", recipe_module.validate(recipe))
        self.assertEqual(len(warns), 1)

    def test_meta_fields_str_ok(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5"},
                  "meta": {"author": "me", "license": "CC-BY-4.0", "url": "http://x"}}
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_meta_author_not_str_error(self):
        recipe = {"schema": 1, "source": {"path": "x.glb"}, "model": {"category": "C5"}, "meta": {"author": 5}}
        errs = self._find("meta.author", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)


class TestValidateStages(unittest.TestCase):
    """validate(): size, rig, mat rules."""

    def _find(self, path, findings):
        return [f for f in findings if f["path"] == path]

    def _valid(self, **overrides):
        """Base recipe with valid size, rig, and mat sections."""
        recipe = {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5"},
        }
        recipe.update(overrides)
        return recipe

    # --- size ---

    def test_size_clean(self):
        recipe = self._valid(size={"mode": "extent", "value": 600, "origin_height": 159,
                                   "scale_pct": 85, "offset": [0, 0, 0], "center": False})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_size_mode_invalid_error(self):
        recipe = self._valid(size={"mode": "bogus", "value": 1})
        errs = self._find("size.mode", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_mode_without_value_error(self):
        recipe = self._valid(size={"mode": "extent"})
        errs = self._find("size.value", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_value_without_mode_error(self):
        recipe = self._valid(size={"value": 600})
        errs = self._find("size.mode", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_value_not_positive_error(self):
        recipe = self._valid(size={"mode": "extent", "value": -1})
        errs = self._find("size.value", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_value_zero_error(self):
        recipe = self._valid(size={"mode": "extent", "value": 0})
        errs = self._find("size.value", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_origin_height_negative_error(self):
        recipe = self._valid(size={"mode": "extent", "value": 600, "origin_height": -1})
        errs = self._find("size.origin_height", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_origin_height_zero_ok(self):
        recipe = self._valid(size={"mode": "extent", "value": 600, "origin_height": 0})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_size_scale_pct_below_range_error(self):
        recipe = self._valid(size={"scale_pct": 5})
        errs = self._find("size.scale_pct", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_scale_pct_above_range_error(self):
        recipe = self._valid(size={"scale_pct": 501})
        errs = self._find("size.scale_pct", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_scale_pct_not_int_error(self):
        recipe = self._valid(size={"scale_pct": 85.5})
        errs = self._find("size.scale_pct", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_offset_wrong_count_error(self):
        recipe = self._valid(size={"offset": [0, 0]})
        errs = self._find("size.offset", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_offset_non_int_error(self):
        recipe = self._valid(size={"offset": [0, "x", 0]})
        errs = self._find("size.offset", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_size_center_not_bool_error(self):
        recipe = self._valid(size={"center": "yes"})
        errs = self._find("size.center", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    # --- rig ---

    def test_rig_clean(self):
        recipe = self._valid(rig={"profile": "auto", "root": "Hips",
                                  "follow": ["Head=head"], "feet": ["L_Foot", "R_Foot"]})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_rig_profile_invalid_error(self):
        recipe = self._valid(rig={"profile": "alien"})
        errs = self._find("rig.profile", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_root_empty_error(self):
        recipe = self._valid(rig={"root": ""})
        errs = self._find("rig.root", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_root_not_str_error(self):
        recipe = self._valid(rig={"root": 5})
        errs = self._find("rig.root", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_follow_bad_pattern_error(self):
        recipe = self._valid(rig={"follow": ["head=head"]})  # lowercase, still pattern ok actually
        # pattern is case-agnostic; use a clearly bad one
        recipe = self._valid(rig={"follow": ["nope"]})
        errs = self._find("rig.follow", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_follow_with_fraction_ok(self):
        recipe = self._valid(rig={"follow": ["Hand=Arm@0.5"]})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_rig_follow_not_list_error(self):
        recipe = self._valid(rig={"follow": "Head=head"})
        errs = self._find("rig.follow", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_feet_not_list_error(self):
        recipe = self._valid(rig={"feet": "L_Foot"})
        errs = self._find("rig.feet", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_rig_feet_non_str_entry_error(self):
        recipe = self._valid(rig={"feet": ["L_Foot", 5]})
        errs = self._find("rig.feet", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    # --- mat ---

    def test_mat_clean(self):
        recipe = self._valid(mat={"atlas": 1024, "no_pbr": False})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_mat_atlas_not_power_of_two_error(self):
        recipe = self._valid(mat={"atlas": 1000})
        errs = self._find("mat.atlas", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_mat_atlas_below_64_error(self):
        recipe = self._valid(mat={"atlas": 32})
        errs = self._find("mat.atlas", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_mat_atlas_above_max_side_error(self):
        recipe = self._valid(mat={"atlas": spec.MAX_SIDE + 1})
        errs = self._find("mat.atlas", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_mat_atlas_above_texture_max_warn(self):
        recipe = self._valid(mat={"atlas": 4096})
        warns = self._find("mat.atlas", recipe_module.validate(recipe))
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["level"], "warn")

    def test_mat_no_pbr_not_bool_error(self):
        recipe = self._valid(mat={"no_pbr": "yes"})
        errs = self._find("mat.no_pbr", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)


class TestValidateActs(unittest.TestCase):
    """validate(): acts, look, shots, acks rules."""

    def _find(self, path, findings):
        return [f for f in findings if f["path"] == path]

    def _valid(self, **overrides):
        """Base recipe with valid sections."""
        recipe = {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5"},
        }
        recipe.update(overrides)
        return recipe

    # --- acts ---

    def test_acts_clean(self):
        recipe = self._valid(acts={
            "idle": {"source": "Idle", "loop": True},
            "attack": {"source": "Attack", "strike": [10, 20]}
        })
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_acts_unknown_act_error(self):
        recipe = self._valid(acts={"unknown": {"source": "Clip"}})
        errs = self._find("acts.unknown", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_source_str_ok(self):
        recipe = self._valid(acts={"idle": {"source": "Idle"}})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_acts_source_procedural_ok(self):
        recipe = self._valid(acts={"hit": {"source": {"procedural": "recoil"}}})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_acts_source_bad_object_error(self):
        recipe = self._valid(acts={"hit": {"source": {"procedural": 123}}})
        errs = self._find("acts.hit.source.procedural", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_source_not_str_or_dict_error(self):
        recipe = self._valid(acts={"idle": {"source": 123}})
        errs = self._find("acts.idle.source", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_strike_not_list_error(self):
        recipe = self._valid(acts={"attack": {"strike": "bad"}})
        errs = self._find("acts.attack.strike", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_strike_negative_error(self):
        recipe = self._valid(acts={"attack": {"strike": [-1]}})
        errs = self._find("acts.attack.strike", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_strike_too_many_error(self):
        recipe = self._valid(acts={"attack": {"strike": list(range(spec.MAX_STRIKES + 1))}})
        errs = self._find("acts.attack.strike", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_strike_on_non_attack_warn(self):
        recipe = self._valid(acts={"idle": {"strike": [10]}})
        warns = self._find("acts.idle.strike", recipe_module.validate(recipe))
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0]["level"], "warn")

    def test_acts_root_motion_invalid_error(self):
        recipe = self._valid(acts={"idle": {"root_motion": "bad"}})
        errs = self._find("acts.idle.root_motion", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acts_speed_not_positive_error(self):
        recipe = self._valid(acts={"idle": {"speed": -1}})
        errs = self._find("acts.idle.speed", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    # --- look ---

    def test_look_clean(self):
        recipe = self._valid(look={"ambient": 20, "light_gain": 100})
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_look_unknown_key_error(self):
        recipe = self._valid(look={"unknown_key": 10})
        errs = self._find("look.unknown_key", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_look_non_number_error(self):
        recipe = self._valid(look={"ambient": "high"})
        errs = self._find("look.ambient", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    # --- shots ---

    def test_shots_clean(self):
        recipe = self._valid(shots=[{"act": "idle", "from": 0, "to": 10, "yaw": 45, "pitch": 0, "distance": 100, "height": 0, "ease": 30}])
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_shots_too_many_error(self):
        too_many = [{"act": "idle", "from": 0, "to": 10}] * (spec.MAX_SHOTS + 1)
        recipe = self._valid(shots=too_many)
        errs = self._find("shots", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_shots_act_invalid_error(self):
        recipe = self._valid(shots=[{"act": "unknown", "from": 0, "to": 10}])
        errs = self._find("shots[0].act", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_shots_from_to_valid(self):
        recipe = self._valid(shots=[{"from": 0, "to": 10, "act": "idle"}])
        errs = self._find("shots[0].from", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 0)

    def test_shots_from_not_int_error(self):
        recipe = self._valid(shots=[{"from": 0.5, "to": 10, "act": "idle"}])
        errs = self._find("shots[0].from", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)
        # to is fine (int), so only from should error

    def test_shots_range_error(self):
        recipe = self._valid(shots=[{"act": "idle", "from": 0, "to": 10, "yaw": 200}])
        errs = self._find("shots[0].yaw", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_shots_other_not_bool_error(self):
        recipe = self._valid(shots=[{"act": "idle", "from": 0, "to": 10, "other": "yes"}])
        errs = self._find("shots[0].other", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    # --- acks ---

    def test_acks_clean(self):
        recipe = self._valid(acks=[{"check": "S4.footprint", "value": 1.9}])
        self.assertEqual(recipe_module.validate(recipe), [])

    def test_acks_check_missing_error(self):
        recipe = self._valid(acks=[{}])
        errs = self._find("acks[0].check", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acks_check_empty_error(self):
        recipe = self._valid(acks=[{"check": "", "value": 1}])
        errs = self._find("acks[0].check", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)

    def test_acks_check_not_str_error(self):
        recipe = self._valid(acks=[{"check": 123}])
        errs = self._find("acks[0].check", recipe_module.validate(recipe))
        self.assertEqual(len(errs), 1)


class TestConvertArgs(unittest.TestCase):
    """convert_args(): mapping to native_convert's options."""

    def _valid_base(self):
        return {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5"},
        }

    def test_procedural_sources_become_rules(self):
        r = self._valid_base()
        r["acts"] = {"hit": {"source": {"procedural": "recoil"}}, "destroyed": {"source": {"procedural": "collapse"}},
                     "idle": {"source": "Idle"}}
        out = recipe.convert_args(r)
        self.assertEqual(out["procedural"], ["hit=recoil", "destroyed=collapse"])
        self.assertEqual(out["clips"], "Idle")

    def test_convert_args_empty_returns_empty(self):
        recipe = self._valid_base()
        self.assertEqual(recipe_module.convert_args(recipe), {})

    def test_size_mode_scale(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "scale", "value": 2.5}
        self.assertEqual(recipe_module.convert_args(recipe), {"scale": 2.5})

    def test_size_mode_extent(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "extent", "value": 600}
        self.assertEqual(recipe_module.convert_args(recipe), {"extent": 600})

    def test_size_mode_root_height(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "root_height", "value": 180}
        self.assertEqual(recipe_module.convert_args(recipe), {"root_height": 180})

    def test_size_mode_height(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "height", "value": 373}
        self.assertEqual(recipe_module.convert_args(recipe), {"height": 373})

    def test_size_origin_height(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "scale", "value": 1, "origin_height": 159}
        self.assertEqual(recipe_module.convert_args(recipe), {"scale": 1, "origin_height": 159})

    def test_size_center_false_sets_no_center_true(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "scale", "value": 1, "center": False}
        self.assertEqual(recipe_module.convert_args(recipe), {"scale": 1, "no_center": True})

    def test_size_center_true_omits_no_center(self):
        recipe = self._valid_base()
        recipe["size"] = {"mode": "scale", "value": 1, "center": True}
        self.assertEqual(recipe_module.convert_args(recipe), {"scale": 1})

    def test_rig_profile(self):
        recipe = self._valid_base()
        recipe["rig"] = {"profile": "ue"}
        self.assertEqual(recipe_module.convert_args(recipe), {"rig": "ue"})

    def test_rig_root(self):
        recipe = self._valid_base()
        recipe["rig"] = {"root": "Hips"}
        self.assertEqual(recipe_module.convert_args(recipe), {"root": "Hips"})

    def test_rig_follow(self):
        recipe = self._valid_base()
        recipe["rig"] = {"follow": ["Head=head@0.5", "Hand=Arm"]}
        self.assertEqual(recipe_module.convert_args(recipe), {"follow": ["Head=head@0.5", "Hand=Arm"]})

    def test_mat_atlas(self):
        recipe = self._valid_base()
        recipe["mat"] = {"atlas": 1024}
        self.assertEqual(recipe_module.convert_args(recipe), {"texture_max": 1024})

    def test_mat_no_pbr_true(self):
        recipe = self._valid_base()
        recipe["mat"] = {"no_pbr": True}
        self.assertEqual(recipe_module.convert_args(recipe), {"no_pbr": True})

    def test_mat_no_pbr_false_omits(self):
        recipe = self._valid_base()
        recipe["mat"] = {"no_pbr": False}
        self.assertEqual(recipe_module.convert_args(recipe), {})

    def test_meta_author(self):
        recipe = self._valid_base()
        recipe["meta"] = {"author": "Me"}
        self.assertEqual(recipe_module.convert_args(recipe), {"author": "Me"})

    def test_meta_license(self):
        recipe = self._valid_base()
        recipe["meta"] = {"license": "CC-BY-4.0"}
        self.assertEqual(recipe_module.convert_args(recipe), {"license": "CC-BY-4.0"})

    def test_model_name(self):
        recipe = self._valid_base()
        recipe["model"] = {"category": "C5", "name": "Dragon"}
        self.assertEqual(recipe_module.convert_args(recipe), {"name": "Dragon"})

    def test_keep_root_motion_from_any_act(self):
        recipe = self._valid_base()
        recipe["acts"] = {"idle": {"root_motion": "keep"}}
        self.assertEqual(recipe_module.convert_args(recipe), {"keep_root_motion": True})

    def test_keep_root_motion_false_omits(self):
        recipe = self._valid_base()
        recipe["acts"] = {"idle": {"root_motion": "remove"}}
        self.assertEqual(recipe_module.convert_args(recipe), {})

    def test_clips_from_acts_source_str_in_acts_order(self):
        recipe = self._valid_base()
        recipe["acts"] = {
            "idle": {"source": "Idle_Clip"},
            "attack": {"source": "Attack_Clip"},
            "enter": {"source": "Enter_Clip"},
        }
        # clips in ACTS order: idle, enter, attack, hit, destroyed, win, guard
        # so order should be: Idle_Clip, Enter_Clip, Attack_Clip
        self.assertEqual(recipe_module.convert_args(recipe)["clips"], "Idle_Clip,Enter_Clip,Attack_Clip")

    def test_clips_deduplicated(self):
        recipe = self._valid_base()
        recipe["acts"] = {
            "idle": {"source": "Same_Clip"},
            "attack": {"source": "Same_Clip"},
        }
        self.assertEqual(recipe_module.convert_args(recipe)["clips"], "Same_Clip")

    def test_clips_only_acts_with_str_source(self):
        recipe = self._valid_base()
        recipe["acts"] = {
            "idle": {"source": "Idle_Clip"},
            "hit": {"source": {"procedural": "recoil"}},  # procedural, not str
            "attack": {"source": "Attack_Clip"},
        }
        self.assertEqual(recipe_module.convert_args(recipe)["clips"], "Idle_Clip,Attack_Clip")

    def test_all_keys_in_valid_dests(self):
        """All returned keys must be in the valid dest set."""
        recipe = {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5", "name": "Test"},
            "meta": {"author": "A", "license": "L"},
            "size": {"mode": "height", "value": 100, "origin_height": 50, "center": False},
            "rig": {"profile": "auto", "root": "Hips", "follow": ["Head=head"]},
            "mat": {"atlas": 1024, "no_pbr": True},
            "acts": {"idle": {"source": "Idle", "root_motion": "keep"}},
        }
        result = recipe_module.convert_args(recipe)
        valid_dests = {
            "clips", "clips_from", "rig", "root", "root_height", "origin_height",
            "height", "extent", "scale", "texture_max", "follow", "no_center",
            "keep_root_motion", "no_pbr", "name", "author", "license"
        }
        for key in result:
            self.assertIn(key, valid_dests, f"key {key} not in valid dests")


class TestModelJson(unittest.TestCase):
    """model_json_members(): mapping to model.json members."""

    def _valid_base(self):
        return {
            "schema": 1,
            "source": {"path": "x.glb"},
            "model": {"category": "C5"},
        }

    def test_model_json_members_empty(self):
        recipe = self._valid_base()
        self.assertEqual(recipe_module.model_json_members(recipe), {})

    def test_model_json_members_clips_str_source(self):
        recipe = self._valid_base()
        recipe["acts"] = {
            "idle": {"source": "Idle_Clip"},
            "attack": {"source": "Attack_Clip"},
            "hit": {"source": {"procedural": "recoil"}},  # procedural, should not appear
        }
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["clips"], {"idle": "Idle_Clip", "attack": "Attack_Clip"})

    def test_model_json_members_strike_from_attack(self):
        recipe = self._valid_base()
        recipe["acts"] = {"attack": {"source": "Attack", "strike": [10, 20]}}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["strike"], {"attack": [10, 20]})

    def test_model_json_members_strike_empty_omitted(self):
        recipe = self._valid_base()
        recipe["acts"] = {"attack": {"source": "Attack", "strike": []}}
        result = recipe_module.model_json_members(recipe)
        self.assertNotIn("strike", result)

    def test_model_json_members_scale_from_size_scale_pct(self):
        recipe = self._valid_base()
        recipe["size"] = {"scale_pct": 85}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["scale"], 85)

    def test_model_json_members_offset_from_size(self):
        recipe = self._valid_base()
        recipe["size"] = {"offset": [10, -5, 20]}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["offset"], [10, -5, 20])

    def test_model_json_members_look(self):
        recipe = self._valid_base()
        recipe["look"] = {"ambient": 20, "light_gain": 100}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["look"], {"ambient": 20, "light_gain": 100})

    def test_model_json_members_look_empty_omitted(self):
        recipe = self._valid_base()
        recipe["look"] = {}
        result = recipe_module.model_json_members(recipe)
        self.assertNotIn("look", result)

    def test_model_json_members_shots(self):
        recipe = self._valid_base()
        recipe["shots"] = [{"act": "idle", "from": 0, "to": 10}]
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["shots"], [{"act": "idle", "from": 0, "to": 10}])

    def test_model_json_members_shots_empty_omitted(self):
        recipe = self._valid_base()
        recipe["shots"] = []
        result = recipe_module.model_json_members(recipe)
        self.assertNotIn("shots", result)

    def test_model_json_members_author_license_from_meta(self):
        recipe = self._valid_base()
        recipe["meta"] = {"author": "Me", "license": "CC-BY-4.0"}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["author"], "Me")
        self.assertEqual(result["license"], "CC-BY-4.0")

    def test_model_json_members_source_from_meta_url(self):
        recipe = self._valid_base()
        recipe["meta"] = {"url": "http://example.com/model"}
        result = recipe_module.model_json_members(recipe)
        self.assertEqual(result["source"], "http://example.com/model")

    def test_model_json_members_fixture_dragon(self):
        # Load the fixture
        import json
        from pathlib import Path
        fixture_path = Path(__file__).parent / "fixtures" / "recipe_dragon.json"
        with open(fixture_path) as f:
            recipe = json.load(f)
        result = recipe_module.model_json_members(recipe)
        # Check all expected keys are present
        self.assertIn("clips", result)
        self.assertIn("strike", result)
        self.assertIn("scale", result)
        self.assertIn("offset", result)
        self.assertIn("look", result)
        self.assertIn("shots", result)
        self.assertIn("author", result)
        self.assertIn("license", result)
        self.assertIn("source", result)
        # Check clips have 6 str source acts (hit has procedural source)
        self.assertEqual(len(result["clips"]), 6)
        self.assertNotIn("hit", result["clips"], "clips should not include hit (procedural source)")
        # Check strike
        self.assertEqual(result["strike"], {"attack": [11, 15]})
        # Check scale
        self.assertEqual(result["scale"], 85)
        # Check offset
        self.assertEqual(result["offset"], [0, 0, 0])
        # Check look
        self.assertEqual(result["look"], {"ambient": 20, "light_gain": 100})
        # Check shots
        self.assertEqual(len(result["shots"]), 1)
        self.assertEqual(result["shots"][0]["act"], "attack")
        # Check meta
        self.assertEqual(result["author"], "Artist")
        self.assertEqual(result["license"], "CC-BY-4.0")
        self.assertEqual(result["source"], "http://example.com/dragon")


if __name__ == "__main__":
    unittest.main()
