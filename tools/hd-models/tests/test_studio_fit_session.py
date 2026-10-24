"""S6 and S7 through the Session: knobs, inputs, findings from the recipe and the reference pack."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from studio import knobs, session, state


def make(recipe):
    return session.Session(__file__, state.Studio(recipe), None, None)


def ids(findings):
    return [f["id"] for f in findings]


class TestFitKnobs(unittest.TestCase):
    def test_knobs_by_stage(self):
        self.assertEqual(len(knobs.knobs("S7")), 9)
        self.assertEqual(len(knobs.knobs("S6")), 3)
        for k in knobs.knobs("S6") + knobs.knobs("S7"):
            self.assertEqual(state.stage_of_path(k["path"]), k["stage"], k["path"])


class TestLaterStages(unittest.TestCase):
    def test_knob_counts_and_paths(self):
        for stage in ("S4", "S9"):
            for k in knobs.knobs(stage):
                self.assertEqual(state.stage_of_path(k["path"]), stage, k["path"])

    def test_s8_s9_findings(self):
        s = make({"meta": {"author": "a", "license": "MIT", "url": "u"}})
        self.assertEqual(ids(s.run_stage("S9")), [])
        self.assertIn("S8.coverage", ids(s.run_stage("S8")))
        s = make({})
        self.assertIn("S9.provenance", ids(s.run_stage("S9")))

    def test_s4_bad_glb_is_a_finding_not_a_crash(self):
        s = make({"size": {"mode": "scale", "value": 100}})
        self.assertEqual(ids(s.run_stage("S4"))[0][:3], "S4.")   # this test file is not a glb


class TestRunMarks(unittest.TestCase):
    def test_add_run_mark(self):
        s = make({})
        m = s.add_run_mark("library", "seen", now=5.0)
        self.assertEqual(s.studio.recipe["runs"], [m])
        s.add_run_mark("field", "problem", "clipping", now=6.0)
        self.assertEqual(len(s.studio.recipe["runs"]), 2)
        self.assertEqual(s.studio.recipe["runs"][1]["problem"], "clipping")
        with self.assertRaises(ValueError):
            s.add_run_mark("field", "problem")


class TestS5(unittest.TestCase):
    def test_no_model_is_a_finding(self):
        self.assertEqual(ids(make({}).run_stage("S5")), ["S5.model"])


class TestParseText(unittest.TestCase):
    def test_round_trip(self):
        for control, text, value in (("ints", "10, 20", [10, 20]), ("floats", "0.6, 1.8", [0.6, 1.8]),
                                     ("pairs", "0:0, 30:60", [[0, 0], [30, 60]]), ("json", '[{"act": "attack"}]', [{"act": "attack"}])):
            self.assertEqual(knobs.parse_text(control, text), value)
            self.assertEqual(knobs.parse_text(control, knobs.show_text(control, value)), value)

    def test_bad_text_raises(self):
        for control, text in (("ints", "a"), ("pairs", "1-2"), ("json", "{}"), ("json", "[")):
            with self.assertRaises(ValueError):
                knobs.parse_text(control, text)


class TestFitSession(unittest.TestCase):
    def test_s7_clean_and_bad(self):
        s = make({"model": {"cards": [1]}})
        self.assertEqual(s.run_stage("S7"), [])
        move = {"act": "attack", "from": 0, "to": 9999, "yaw": 0, "pitch": 0, "distance": 100, "height": 0,
                "ease": "linear", "other": False}
        s = make({"model": {"cards": [1]}, "shots": [move]})
        self.assertIn("S7.move-range", ids(s.run_stage("S7")))   # card 1 attack row is 270 frames

    def test_s6_runs_and_stores(self):
        s = make({"model": {"cards": [1]}, "acts": {"attack": {"strike": [10]}}})
        s.run_stage("S6")
        self.assertIn("S6", s.studio.findings)
        self.assertIn("acts", s.stage_inputs("S6"))

    def test_edit_marks_s7_stale(self):
        s = make({"model": {"cards": [1]}})
        s.run_stage("S7")
        s.edit("look.ambient", 30)
        self.assertEqual(s.studio.recipe["look"]["ambient"], 30)
        self.assertEqual(s.studio.state("S7"), "stale")


class TestBuildS9(unittest.TestCase):
    def test_build_sets_pkg_path(self):
        import tempfile
        s = make({"model": {"cards": [364]}, "pkg": {"name": "demo"}, "meta": {"author": "a", "license": "MIT", "url": "u"}})
        def runner(argv):
            out = Path(argv[argv.index("--out") + 1]); out.mkdir(parents=True, exist_ok=True)
            (out / "mod.json").write_text("{}")
            return 0, "ok"
        with tempfile.TemporaryDirectory() as d:
            r = s.build_s9(d, runner)
            self.assertTrue(r["build"]["ok"])
            self.assertEqual(s.studio.recipe["pkg"]["path"], str(Path(d) / "a"))

    def test_failed_build_keeps_path_unset(self):
        import tempfile
        s = make({"model": {"cards": [364]}, "pkg": {"name": "demo"}})
        with tempfile.TemporaryDirectory() as d:
            r = s.build_s9(d, lambda argv: (1, "boom"))
            self.assertEqual(ids(r["findings"]), ["S9.build"])
            self.assertNotIn("path", s.studio.recipe["pkg"])


if __name__ == "__main__":
    unittest.main()
