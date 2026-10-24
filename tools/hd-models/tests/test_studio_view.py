"""Tests for the Studio view layer: rail, knobs, checkrows, session."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import state, audit
import synthetic_gltf


def _make_studio_with_audit(recipe=None):
    """Create a Studio, run S0-S3 audit on the synthetic glb, apply findings."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        glb_path = tmp / "model.glb"
        synthetic_gltf.write(str(glb_path))
        results = audit.audit_all(glb_path, recipe)
        studio = state.Studio(recipe)
        audit.apply_to_studio(studio, results)
        return studio


class TestRail(unittest.TestCase):
    def test_rail_returns_four_groups_and_nine_entries(self):
        studio = _make_studio_with_audit()
        # Import here so the test fails if rail.py doesn't exist
        from studio import rail
        items = rail.rail(studio)
        # Count groups and stage entries
        groups = [item for item in items if item.get("kind") == "group"]
        stages = [item for item in items if item.get("kind") == "stage"]
        self.assertEqual(len(groups), 4)
        self.assertEqual(len(stages), 9)


class TestKnobs(unittest.TestCase):
    def test_knob_stage_matches_state_stage_of_path(self):
        from studio import knobs
        for stage in ("S0", "S1", "S2", "S3"):
            for k in knobs.knobs(stage):
                path = k["path"]
                expected_stage = k["stage"]
                actual_stage = state.stage_of_path(path)
                self.assertEqual(actual_stage, expected_stage,
                                 f"knob {path}: stage_of_path returns {actual_stage!r}, expected {expected_stage!r}")

    def test_sample_values_pass_validation(self):
        from studio import knobs
        import recipe
        # One valid sample value per knob path
        samples = {
            "model.category": "C1",
            "source.path": "model.glb",
            "meta.author": "Test Author",
            "meta.license": "CC-BY-4.0",
            "meta.url": "https://example.com",
            "meta.attribution": True,
            "source.skin": "skin0",
            "source.meshes": ["mesh1", "mesh2"],
            "model.cards": [1, 2],
            "audit.fix_axes": True,
            "audit.bone_limit": "merge",
            "audit.merge": ["bone1", "bone2"],
            "audit.smooth_passes": 2,
            "audit.normalise": True,
            "audit.drop_parts": ["part1"],
            "audit.mirror": "x",
            "rig.profile": "ue",
            "rig.root": "pelvis",
            "rig.humanoid": {"hips": "pelvis", "spine": "spine_01"},
            "rig.feet": ["foot_r", "foot_l"],
            "rig.strike": "hand_r",
            "rig.extras": ["extra1"],
            "rig.follow": ["bone1=source1@0.5"],
            "mat.atlas": 1024,
            "mat.items": [{"name": "mat1"}],
            "mat.normal_strength": 1.5,
            "mat.no_pbr": False,
        }
        for path, val in samples.items():
            k = knobs.knob(path)
            self.assertIsNotNone(k, f"unknown knob path: {path}")
            # Build a minimal recipe with this value
            rec = {"schema": 1, "source": {"path": "model.glb", "sha256": "a" * 64}, "model": {"category": "C1"}}
            state.set_path(rec, path, val)
            findings = recipe.validate(rec)
            errors = [f for f in findings if f["level"] == "error"]
            self.assertEqual(errors, [], f"knob {path} sample {val!r} produced errors: {errors}")


class TestCheckRows(unittest.TestCase):
    def test_s0_check_rows_order_and_fix_targets(self):
        # Synthetic glb has no license, no author, no category, one skin
        studio = _make_studio_with_audit()
        from studio import checkrows
        result = checkrows.check_rows(studio, "S0")
        rows = result["rows"]
        summary = result["summary"]
        # Licence is info only; fail (category) and warn (category-confidence)
        self.assertEqual(summary["fail"], 1, f"expected 1 fail, got {summary}")
        self.assertEqual(summary["warn"], 1, f"expected 1 warn, got {summary}")
        self.assertEqual(summary["info"], 1, f"expected 1 info, got {summary}")
        # Order: fail, warn, acked, info
        chips = [r["chip"] for r in rows]
        self.assertEqual(chips, ["fail", "warn", "info"])
        # Check fix_targets
        fix_targets = {r["id"]: r["fix_target"] for r in rows}
        self.assertEqual(fix_targets.get("S0.licence"), "meta.license")
        self.assertEqual(fix_targets.get("S0.category"), "model.category")
        self.assertEqual(fix_targets.get("S0.category-confidence"), "model.category")

    def test_s1_check_rows_fix_targets(self):
        studio = _make_studio_with_audit()
        from studio import checkrows
        result = checkrows.check_rows(studio, "S1")
        rows = result["rows"]
        fix_targets = {r["id"]: r["fix_target"] for r in rows}
        # S1 has only info findings in synthetic glb
        self.assertEqual(fix_targets.get("S1.ok"), None)
        self.assertEqual(fix_targets.get("S1.merge"), "audit.merge")

    def test_s2_check_rows_fix_targets(self):
        studio = _make_studio_with_audit()
        from studio import checkrows
        result = checkrows.check_rows(studio, "S2")
        rows = result["rows"]
        fix_targets = {r["id"]: r["fix_target"] for r in rows}
        self.assertEqual(fix_targets.get("S2.root-side"), "rig.root")
        self.assertEqual(fix_targets.get("S2.ok"), None)

    def test_s3_check_rows_fix_targets(self):
        studio = _make_studio_with_audit()
        from studio import checkrows
        result = checkrows.check_rows(studio, "S3")
        rows = result["rows"]
        fix_targets = {r["id"]: r["fix_target"] for r in rows}
        self.assertEqual(fix_targets.get("S3.ok"), None)

    def test_acknowledged_warn_shows_as_acked(self):
        studio = _make_studio_with_audit()
        # Acknowledge S0.category-confidence warning
        warn_val = studio.findings["S0"][2].get("value")  # S0.category-confidence
        studio.acknowledge("S0.category-confidence", warn_val)
        from studio import checkrows
        result = checkrows.check_rows(studio, "S0")
        rows = result["rows"]
        summary = result["summary"]
        self.assertEqual(summary["warn"], 0)
        self.assertEqual(summary["acked"], 1)
        # Find the acked row
        acked_rows = [r for r in rows if r["chip"] == "acked"]
        self.assertEqual(len(acked_rows), 1)
        self.assertEqual(acked_rows[0]["id"], "S0.category-confidence")
        self.assertTrue(acked_rows[0]["acknowledged"])

    def test_info_collapse_beyond_four(self):
        # Create a studio with many info findings by patching S0 (which has 0 info originally)
        studio = _make_studio_with_audit()
        from studio import checkrows
        # Add 5 extra info findings to S0
        extra = [
            {"id": f"S0.extra{i}", "level": "info", "message": f"Extra {i}", "fix": "", "value": None}
            for i in range(5)
        ]
        studio.findings["S0"].extend(extra)
        result = checkrows.check_rows(studio, "S0")
        rows = result["rows"]
        info_rows = [r for r in rows if r["chip"] == "info"]
        # Should collapse to one row with id "info*"
        self.assertEqual(len(info_rows), 1)
        self.assertEqual(info_rows[0]["id"], "info*")
        self.assertEqual(info_rows[0]["message"], "6 checks passed")  # licence info + 5 extra
        self.assertTrue("collapsed" in info_rows[0])
        self.assertEqual(len(info_rows[0]["collapsed"]), 6)


class TestSessionOpen(unittest.TestCase):
    def test_session_open_new_recipe(self):
        import tempfile
        from studio import session
        import recipe
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            self.assertIsInstance(sess, session.Session)
            self.assertEqual(sess.glb, glb_path)
            self.assertIsNone(sess.recipe_path)
            self.assertIsNotNone(sess.studio)
            self.assertEqual(sess.studio.recipe["schema"], recipe.SCHEMA)
            self.assertIn("source", sess.studio.recipe)
            self.assertIn("sha256", sess.studio.recipe["source"])
            self.assertEqual(sess.studio.recipe["model"]["category"], "C1")
            # Model should be loaded
            self.assertIsNotNone(sess._model)

    def test_session_open_existing_recipe(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            recipe_path = tmp / "recipe.json"
            # First create a recipe
            sess1 = session.Session.open(glb_path, recipe_path)
            sess1.studio.save(recipe_path)
            # Now open with existing recipe
            sess2 = session.Session.open(glb_path, recipe_path)
            self.assertEqual(sess2.recipe_path, recipe_path)
            self.assertEqual(sess2.studio.recipe["source"]["sha256"], sess1.studio.recipe["source"]["sha256"])

    def test_session_open_bad_glb_gives_s0_load_fail(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "bad.glb"
            glb_path.write_bytes(b"not a glb")
            sess = session.Session.open(glb_path)
            self.assertIsNone(sess._model)
            # S0 should have a load fail finding
            findings = sess.studio.findings.get("S0", [])
            self.assertTrue(any(f["id"] == "S0.load" and f["level"] == "fail" for f in findings))

    def test_stage_inputs_s0_includes_expected_sections(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            inputs = sess.stage_inputs("S0")
            self.assertIn("sha256", inputs)
            self.assertIn("source", inputs)
            self.assertIn("model", inputs)
            self.assertIn("meta", inputs)
            self.assertNotIn("audit", inputs)
            self.assertNotIn("rig", inputs)
            self.assertNotIn("mat", inputs)

    def test_stage_inputs_s1_includes_audit(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            inputs = sess.stage_inputs("S1")
            self.assertIn("audit", inputs)

    def test_stage_inputs_s2_includes_rig_and_category(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            inputs = sess.stage_inputs("S2")
            self.assertIn("rig", inputs)
            self.assertIn("model", inputs)
            self.assertEqual(inputs["model"].get("category"), "C1")

    def test_stage_inputs_s3_includes_mat(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            inputs = sess.stage_inputs("S3")
            self.assertIn("mat", inputs)

    def test_stage_inputs_equal_when_unchanged(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            inputs1 = sess.stage_inputs("S0")
            inputs2 = sess.stage_inputs("S0")
            self.assertEqual(inputs1, inputs2)

    def test_run_stage_returns_findings_and_stores_them(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            findings = sess.run_stage("S0")
            self.assertIsInstance(findings, list)
            self.assertTrue(len(findings) > 0)
            # Findings should be stored in studio
            self.assertEqual(sess.studio.findings["S0"], findings)

    def test_open_stage_runs_when_todo(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            # S0 is todo initially
            self.assertEqual(sess.studio.state("S0"), "todo")
            ran = sess.open_stage("S0")
            self.assertTrue(ran)
            self.assertEqual(sess.studio.state("S0"), "pass")  # licence is info only

    def test_open_stage_silent_when_unchanged(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            sess.run_stage("S0")
            self.assertEqual(sess.studio.state("S0"), "pass")
            # Reopen with same inputs should not run
            ran = sess.open_stage("S0")
            self.assertFalse(ran)
            self.assertEqual(sess.studio.state("S0"), "pass")

    def test_open_stage_runs_when_stale_and_inputs_changed(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb_path = tmp / "model.glb"
            synthetic_gltf.write(str(glb_path))
            sess = session.Session.open(glb_path)
            sess.run_stage("S0")
            # Change a knob that S0 reads
            sess.edit("meta.license", "CC-BY-4.0")
            # Now open_stage should run again
            ran = sess.open_stage("S0")
            self.assertTrue(ran)


class TestSessionEdit(unittest.TestCase):
    def setUp(self):
        import tempfile
        from studio import session
        self.td = tempfile.TemporaryDirectory()
        tmp = Path(self.td.name)
        self.glb_path = tmp / "model.glb"
        synthetic_gltf.write(str(self.glb_path))
        self.sess = session.Session.open(self.glb_path)
        self.sess.run_stage("S0")

    def tearDown(self):
        self.td.cleanup()

    def test_edit_records_pending_and_marks_stale(self):
        # edit() should mark S0 stale and record pending time
        marked = self.sess.edit("meta.license", "CC-BY-4.0")
        self.assertIn("S0", marked)
        self.assertIn("S0", self.sess._pending)

    def test_due_returns_stages_after_300ms(self):
        import time
        now = time.monotonic()
        self.sess.edit("meta.license", "CC-BY-4.0", now=now)
        # Immediately: not due
        self.assertEqual(self.sess.due(now=now), [])
        # After 300ms: due
        later = now + 0.31
        self.assertEqual(self.sess.due(now=later), ["S0"])

    def test_run_due_clears_pending_and_runs_stage(self):
        import time
        now = time.monotonic()
        self.sess.edit("meta.license", "CC-BY-4.0", now=now)
        later = now + 0.31
        ran = self.sess.run_due(now=later)
        self.assertEqual(ran, ["S0"])
        self.assertNotIn("S0", self.sess._pending)

    def test_debounce_moves_time_on_second_edit(self):
        import time
        now = time.monotonic()
        self.sess.edit("meta.license", "CC-BY-4.0", now=now)
        # Second edit before 300ms moves the time
        self.sess.edit("meta.author", "Author", now=now + 0.1)
        # At 0.3s from first edit, not due (second edit reset it)
        self.assertEqual(self.sess.due(now=now + 0.3), [])
        # At 0.4s from first edit (0.3s from second), due
        self.assertEqual(self.sess.due(now=now + 0.4), ["S0"])

    def test_autosave_writes_when_unsaved_and_path_exists(self):
        import tempfile
        from studio import session
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            glb = tmp / "model.glb"
            synthetic_gltf.write(str(glb))
            recipe_path = tmp / "recipe.json"
            sess = session.Session.open(glb, recipe_path)
            # Initially saved (new recipe)
            self.assertEqual(sess.studio.save_state, "saved")
            # Make an edit
            sess.edit("meta.license", "CC-BY-4.0")
            self.assertEqual(sess.studio.save_state, "unsaved")
            # autosave should write
            wrote = sess.autosave()
            self.assertTrue(wrote)
            self.assertEqual(sess.studio.save_state, "saved")

    def test_autosave_noop_when_saved_or_no_path(self):
        # No recipe path
        self.assertEqual(self.sess.recipe_path, None)
        self.assertFalse(self.sess.autosave())
        # Already saved
        self.sess.studio.save_state = "saved"
        self.assertFalse(self.sess.autosave())

    def test_undo_redo_record_pending(self):
        import time
        now = time.monotonic()
        self.sess.edit("meta.license", "CC-BY-4.0", now=now)
        marked = self.sess.undo()
        self.assertIn("S0", marked)
        self.assertIn("S0", self.sess._pending)
        marked = self.sess.redo()
        self.assertIn("S0", marked)
        self.assertIn("S0", self.sess._pending)

    def test_change_category_records_pending(self):
        # change_category marks downstream stages (S1+) that have findings, not S0 itself
        self.sess.run_stage("S1")
        marked = self.sess.change_category("C3")
        self.assertIn("S1", marked)
        self.assertIn("S1", self.sess._pending)

    def test_acknowledge_marks_unsaved(self):
        # Need a warning finding; remove category so S0.category-confidence appears
        self.sess.studio.edit("model.category", None)
        self.sess.run_stage("S0")
        warns = [f for f in self.sess.studio.findings.get("S0", [])
                 if f["level"] == "warn" and f["id"] == "S0.category-confidence"]
        self.assertTrue(warns, "expected S0.category-confidence warning")
        self.sess.studio.acknowledge("S0.category-confidence", warns[0].get("value"))
        self.assertEqual(self.sess.studio.save_state, "unsaved")

    def test_run_audit_cli_prints_json(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parent.parent / "studio" / "run_audit.py"
        result = subprocess.run([sys.executable, str(script), str(self.glb_path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        # Should be valid JSON with S0-S3
        import json
        data = json.loads(result.stdout)
        for s in ("S0", "S1", "S2", "S3"):
            self.assertIn(s, data)
            self.assertIn("findings", data[s])

    def test_run_audit_cli_single_stage(self):
        import subprocess
        import sys
        import json
        script = Path(__file__).resolve().parent.parent / "studio" / "run_audit.py"
        result = subprocess.run([sys.executable, str(script), str(self.glb_path), "--stage", "S1"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("findings", data)
        # Should have S1 findings
        self.assertTrue(any(f["id"].startswith("S1.") for f in data["findings"]))

    def test_run_audit_cli_missing_glb_exits_2(self):
        import subprocess
        import sys
        script = Path(__file__).resolve().parent.parent / "studio" / "run_audit.py"
        result = subprocess.run([sys.executable, str(script), "/nonexistent.glb"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("glb not found", result.stderr)


class TestWalk(unittest.TestCase):
    def setUp(self):
        import tempfile
        from studio import session
        self.td = tempfile.TemporaryDirectory()
        tmp = Path(self.td.name)
        self.glb_path = tmp / "model.glb"
        synthetic_gltf.write(str(self.glb_path))
        self.sess = session.Session.open(self.glb_path)
        self.sess.run_stage("S0")

    def tearDown(self):
        self.td.cleanup()

    def test_walk(self):
        sess = self.sess
        self.assertEqual(sess.studio.state("S0"), "pass")  # an empty licence does not fail S0
        sess.edit("meta.license", "CC-BY-4.0"); sess.edit("meta.author", "Tester")
        sess.change_category("C1")
        sess.run_stage("S0")
        self.assertEqual(sess.studio.state("S0"), "pass")
        sess.open_stage("S1")
        from studio import checkrows, rail
        for row in checkrows.check_rows(sess.studio, "S1")["rows"]:
            if row["level"] == "warn" and not row["acknowledged"]:
                sess.acknowledge(row["id"], row.get("value"))
        self.assertTrue(rail.footer(sess.studio, "S1")["next_enabled"])
        # Undo back until the licence edit is undone: S0 still passes
        while sess.studio.undo_stack:
            sess.undo()
            if sess.studio.recipe.get("meta", {}).get("license") is None:
                break
        sess.open_stage("S0")
        self.assertEqual(sess.studio.state("S0"), "pass")


if __name__ == "__main__":
    unittest.main()