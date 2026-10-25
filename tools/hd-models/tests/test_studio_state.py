"""The Model Studio's stage state machine (studio/state.py): states, dependencies, acknowledgements, undo, saving."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from studio import state  # noqa: E402
from studio.state import Studio  # noqa: E402


def warn(check, value=1.0):
    return {"id": check, "level": "warn", "message": "m", "fix": "f", "value": value}


def fail(check):
    return {"id": check, "level": "fail", "message": "m", "fix": "f"}


def info(check):
    return {"id": check, "level": "info", "message": "m", "fix": ""}


def passed_studio():
    s = Studio({"schema": 1, "model": {"category": "C1"}})
    for stage in state.STAGES[:-1]:
        s.set_findings(stage, [info(f"{stage}.ok")], {"in": stage})
    s.save_state = "saved"
    return s


class TestStates(unittest.TestCase):
    def test_todo_until_run(self):
        self.assertEqual(set(Studio().states().values()), {"todo"})

    def test_pass_warn_fail(self):
        s = Studio()
        s.set_findings("S1", [info("S1.a")])
        s.set_findings("S2", [warn("S2.a")])
        s.set_findings("S3", [warn("S3.a"), fail("S3.b")])
        self.assertEqual((s.state("S1"), s.state("S2"), s.state("S3")), ("pass", "warn", "fail"))

    def test_bad_level_refused(self):
        with self.assertRaises(ValueError):
            Studio().set_findings("S1", [{"id": "S1.x", "level": "maybe"}])

    def test_stage_of_path(self):
        cases = {"source.path": "S0", "model.category": "S0", "meta.license": "S0", "audit.mirror": "S1", "rig.root": "S2",
                 "mat.atlas": "S3", "size.value": "S4", "acts.idle.source": "S5", "acts.attack.strike": "S6",
                 "acts.attack.timemap": "S6", "look.ambient": "S7", "shots": "S7", "runs": "S8", "pkg.name": "S9",
                 "acks": None, "schema": None}
        for path, stage in cases.items():
            self.assertEqual(state.stage_of_path(path), stage, path)


class TestStale(unittest.TestCase):
    def test_edit_marks_downstream_stale_only(self):
        s = passed_studio()
        marked = s.edit("rig.root", "pelvis")
        self.assertEqual(sorted(marked), ["S2", "S4", "S5", "S6", "S7", "S8"])
        self.assertEqual(s.state("S1"), "pass")      # upstream of the edit keeps its result
        self.assertEqual(s.state("S3"), "pass")      # S3 does not depend on S2
        self.assertEqual(s.state("S4"), "stale")
        self.assertEqual(s.state("S9"), "todo")      # never run: not stale, still todo

    def test_s3_edit_reaches_look_validate_package(self):
        s = passed_studio()
        self.assertEqual(sorted(s.edit("mat.atlas", 1024)), ["S3", "S7", "S8"])

    def test_category_change_marks_all_but_s0(self):
        s = passed_studio()
        marked = s.change_category("C5")
        self.assertNotIn("S0", marked)
        self.assertEqual(set(marked), {f"S{i}" for i in range(1, 9)})

    def test_stale_keeps_findings_and_reopens_silently_when_inputs_equal(self):
        s = passed_studio()
        s.edit("rig.root", "pelvis")
        self.assertEqual(s.state("S4"), "stale")
        self.assertFalse(s.reopen("S4", {"in": "S4"}))    # same inputs as the last run: no re-run
        self.assertEqual(s.state("S4"), "pass")
        s.edit("rig.root", "hips")
        self.assertTrue(s.reopen("S4", {"in": "changed"}))   # inputs differ: run again
        self.assertEqual(s.state("S4"), "stale")

    def test_rerun_clears_stale(self):
        s = passed_studio()
        s.edit("rig.root", "pelvis")
        s.set_findings("S2", [info("S2.ok")], {"in": "S2"})
        self.assertEqual(s.state("S2"), "pass")

    def test_downstream_graph(self):
        self.assertEqual(Studio.downstream("S5"), ["S6", "S7", "S8", "S9"])
        self.assertEqual(set(Studio.downstream("S0")), {f"S{i}" for i in (1, 2, 3, 4, 5, 6, 7, 8, 9)})


class TestAcknowledgements(unittest.TestCase):
    def test_ack_turns_warn_into_pass(self):
        s = Studio()
        s.set_findings("S1", [warn("S1.bind-vs-rest", 5.0)])
        s.acknowledge("S1.bind-vs-rest", 5.0)
        self.assertEqual(s.state("S1"), "pass")
        self.assertEqual(s.recipe["acks"], [{"check": "S1.bind-vs-rest", "value": 5.0}])

    def test_several_warnings_share_one_check_id(self):
        s = Studio()
        s.set_findings("S5", [warn("S5.missing-act", "win"), warn("S5.missing-act", "guard")])
        s.acknowledge("S5.missing-act", "win")
        s.acknowledge("S5.missing-act", "guard")
        self.assertEqual(s.state("S5"), "pass")
        self.assertEqual(len(s.recipe["acks"]), 2)
        s.set_findings("S5", [warn("S5.missing-act", "win"), warn("S5.missing-act", "hit")])
        self.assertEqual(s.recipe["acks"], [{"check": "S5.missing-act", "value": "win"}])

    def test_ack_needs_a_matching_warning(self):
        s = Studio()
        s.set_findings("S1", [warn("S1.bind-vs-rest", 5.0)])
        with self.assertRaises(ValueError):
            s.acknowledge("S1.bind-vs-rest", 6.0)
        with self.assertRaises(ValueError):
            s.acknowledge("S1.weights", 1.0)

    def test_fail_cannot_be_acknowledged_away(self):
        s = Studio()
        s.set_findings("S1", [fail("S1.bones")])
        with self.assertRaises(ValueError):
            s.acknowledge("S1.bones", None)
        self.assertEqual(s.state("S1"), "fail")

    def test_value_change_drops_the_ack(self):
        s = Studio()
        s.set_findings("S1", [warn("S1.bind-vs-rest", 5.0)])
        s.acknowledge("S1.bind-vs-rest", 5.0)
        dropped = s.set_findings("S1", [warn("S1.bind-vs-rest", 7.5)])
        self.assertEqual(dropped, [{"check": "S1.bind-vs-rest", "value": 5.0}])
        self.assertEqual(s.state("S1"), "warn")
        self.assertNotIn("acks", s.recipe)

    def test_ack_survives_a_rerun_with_the_same_value_and_other_stages_untouched(self):
        s = Studio()
        s.set_findings("S1", [warn("S1.a", 1.0)])
        s.acknowledge("S1.a", 1.0)
        s.set_findings("S2", [warn("S2.b", 2.0)])
        s.acknowledge("S2.b", 2.0)
        s.set_findings("S1", [warn("S1.a", 1.0)])
        self.assertEqual(len(s.recipe["acks"]), 2)

    def test_vanished_warning_drops_its_ack(self):
        s = Studio()
        s.set_findings("S1", [warn("S1.a", 1.0)])
        s.acknowledge("S1.a", 1.0)
        s.set_findings("S1", [info("S1.ok")])
        self.assertNotIn("acks", s.recipe)


class TestBuildGate(unittest.TestCase):
    def test_all_pass_builds(self):
        s = passed_studio()
        ok, reasons = s.can_build()
        self.assertEqual((ok, reasons), (True, []))

    def test_each_blocker_is_named(self):
        s = passed_studio()
        s.set_findings("S3", [warn("S3.memory", 9.0)])
        s.set_findings("S5", [fail("S5.x")])
        s.edit("size.value", 600)
        ok, reasons = s.can_build()
        self.assertFalse(ok)
        self.assertIn("S3 is warn", reasons)
        self.assertIn("S5 is fail", reasons)
        self.assertIn("S4 is stale", reasons)
        self.assertIn("the recipe is not saved", reasons)

    def test_acknowledged_warn_builds(self):
        s = passed_studio()
        s.set_findings("S3", [warn("S3.memory", 9.0)])
        s.acknowledge("S3.memory", 9.0)
        s.save_state = "saved"
        self.assertTrue(s.can_build()[0])

    def test_todo_blocks(self):
        s = Studio()
        self.assertIn("S1 is todo", s.can_build()[1])


class TestUndo(unittest.TestCase):
    def test_undo_redo_values_and_stale(self):
        s = passed_studio()
        s.edit("size.value", 600)
        s.edit("size.value", 700)
        self.assertEqual(s.recipe["size"]["value"], 700)
        s.undo()
        self.assertEqual(s.recipe["size"]["value"], 600)
        s.undo()
        self.assertNotIn("size", s.recipe)     # an object left empty goes with its last key
        s.redo()
        self.assertEqual(s.recipe["size"]["value"], 600)
        self.assertEqual(s.state("S4"), "stale")

    def test_new_edit_clears_redo(self):
        s = Studio()
        s.edit("rig.root", "a")
        s.undo()
        s.edit("rig.root", "b")
        self.assertEqual(s.redo(), [])

    def test_undo_marks_stages_stale(self):
        s = passed_studio()
        s.edit("rig.root", "pelvis")
        s.set_findings("S2", [info("S2.ok")], {"in": "S2"})
        self.assertEqual(s.state("S2"), "pass")
        s.undo()
        self.assertEqual(s.state("S2"), "stale")

    def test_noop_edit_is_not_recorded(self):
        s = Studio({"schema": 1, "rig": {"root": "pelvis"}})
        self.assertEqual(s.edit("rig.root", "pelvis"), [])
        self.assertEqual(s.undo_stack, [])

    def test_reset_stage_is_one_undo_entry(self):
        s = Studio({"schema": 1, "size": {"mode": "extent", "value": 600}, "rig": {"root": "x"}})
        s.reset_stage("S4")
        self.assertNotIn("size", s.recipe)
        self.assertIn("rig", s.recipe)
        s.undo()
        self.assertEqual(s.recipe["size"], {"mode": "extent", "value": 600})

    def test_reset_acts_by_stage(self):
        s = Studio({"schema": 1, "acts": {"attack": {"source": "Bite", "strike": [11]}}})
        s.reset_stage("S6")
        self.assertEqual(s.recipe["acts"], {"attack": {"source": "Bite"}})


class TestSave(unittest.TestCase):
    def test_save_canonical_and_backup(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "recipe.json"
            s = Studio({"schema": 1, "model": {"category": "C1"}})
            s.edit("size.value", 3.0)
            self.assertEqual(s.save_state, "unsaved")
            self.assertTrue(s.save(path))
            self.assertEqual(s.save_state, "saved")
            self.assertIn('"value": 3\n', path.read_text())      # whole numbers as ints, sorted keys
            s.edit("size.value", 4)
            s.save(path)
            self.assertEqual(json.loads((Path(d) / "recipe.json.bak").read_text())["size"]["value"], 3)

    def test_save_error_is_a_state_not_an_exception(self):
        s = Studio()
        self.assertFalse(s.save("/nonexistent-folder-for-test/recipe.json"))
        self.assertEqual(s.save_state, "error")
        self.assertTrue(s.save_error)


class TestReport(unittest.TestCase):
    def test_report_is_stable_json(self):
        s = passed_studio()
        a, b = s.report_json(), s.report_json()
        self.assertEqual(a, b)
        data = json.loads(a)
        self.assertEqual(data["states"]["S1"], "pass")
        self.assertEqual(data["states"]["S9"], "todo")
        self.assertTrue(data["build"]["ok"])


if __name__ == "__main__":
    unittest.main()
