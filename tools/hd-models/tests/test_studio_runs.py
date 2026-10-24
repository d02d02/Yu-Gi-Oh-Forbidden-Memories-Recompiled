"""Tests for studio/runs.py (S8 run list, marks and checks)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from studio import audit, runs


class TestRows(unittest.TestCase):
    def test_run_rows_returns_ten_rows(self):
        rows = runs.run_rows(True)
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertEqual(set(r.keys()), {"id", "label", "needs_disc"})

    def test_run_rows_order_and_ids(self):
        ids = [r["id"] for r in runs.run_rows(True)]
        self.assertEqual(ids, [
            "library", "field", "arena",
            "act:idle", "act:enter", "act:attack", "act:hit",
            "act:destroyed", "act:win", "act:guard",
        ])

    def test_run_rows_labels(self):
        labels = [r["label"] for r in runs.run_rows(True)]
        self.assertEqual(labels[0], "Library turntable")
        self.assertEqual(labels[1], "Field attack")
        self.assertEqual(labels[2], "Arena attack")
        self.assertEqual(labels[3], "Act: idle")
        self.assertEqual(labels[9], "Act: guard")

    def test_run_rows_needs_disc(self):
        rows = runs.run_rows(True)
        self.assertFalse(rows[0]["needs_disc"])  # library
        self.assertTrue(rows[1]["needs_disc"])    # field
        self.assertTrue(rows[2]["needs_disc"])    # arena
        self.assertTrue(rows[3]["needs_disc"])    # act:idle
        for r in rows[3:]:
            self.assertTrue(r["needs_disc"])

    def test_run_rows_disc_available_does_not_change_list(self):
        self.assertEqual(runs.run_rows(True), runs.run_rows(False))


class TestMarks(unittest.TestCase):
    def test_owning_stage_known_problems(self):
        self.assertEqual(runs.owning_stage("wrong size"), "S4")
        self.assertEqual(runs.owning_stage("wrong timing"), "S6")
        self.assertEqual(runs.owning_stage("clipping"), "S5")
        self.assertEqual(runs.owning_stage("pose pop"), "S5")
        self.assertEqual(runs.owning_stage("wrong look"), "S7")

    def test_owning_stage_unknown_raises(self):
        with self.assertRaises(ValueError):
            runs.owning_stage("not a problem")

    def test_make_mark_seen_valid(self):
        mark = runs.make_mark("library", "seen", "abc123", 1234567890.0)
        self.assertEqual(mark["row"], "library")
        self.assertEqual(mark["result"], "seen")
        self.assertIsNone(mark["problem"])
        self.assertEqual(mark["package_hash"], "abc123")
        self.assertEqual(mark["time"], 1234567890.0)

    def test_make_mark_problem_valid(self):
        mark = runs.make_mark("act:attack", "problem", "abc123", 1234567890.0, "clipping")
        self.assertEqual(mark["row"], "act:attack")
        self.assertEqual(mark["result"], "problem")
        self.assertEqual(mark["problem"], "clipping")
        self.assertEqual(mark["package_hash"], "abc123")
        self.assertEqual(mark["time"], 1234567890.0)

    def test_make_mark_unknown_row_raises(self):
        with self.assertRaises(ValueError):
            runs.make_mark("unknown", "seen", "abc123", 1234567890.0)

    def test_make_mark_invalid_result_raises(self):
        with self.assertRaises(ValueError):
            runs.make_mark("library", "invalid", "abc123", 1234567890.0)

    def test_make_mark_problem_without_problem_raises(self):
        with self.assertRaises(ValueError):
            runs.make_mark("library", "problem", "abc123", 1234567890.0)

    def test_make_mark_problem_invalid_problem_raises(self):
        with self.assertRaises(ValueError):
            runs.make_mark("library", "problem", "abc123", 1234567890.0, "not a problem")

    def test_make_mark_seen_with_problem_raises(self):
        with self.assertRaises(ValueError):
            runs.make_mark("library", "seen", "abc123", 1234567890.0, "clipping")


class TestStatus(unittest.TestCase):
    def test_row_status_no_mark_returns_not_run(self):
        self.assertEqual(runs.row_status([], "library", "abc123"), "not run")

    def test_row_status_mark_with_same_package_hash(self):
        marks = [runs.make_mark("library", "seen", "abc123", 1234567890.0)]
        self.assertEqual(runs.row_status(marks, "library", "abc123"), "seen")

    def test_row_status_mark_with_different_package_hash(self):
        marks = [runs.make_mark("library", "seen", "abc123", 1234567890.0)]
        self.assertEqual(runs.row_status(marks, "library", "oldhash"), "not run")

    def test_row_status_latest_mark_wins(self):
        marks = [
            runs.make_mark("library", "seen", "abc123", 100.0),
            runs.make_mark("library", "problem", "abc123", 200.0, "clipping"),
        ]
        self.assertEqual(runs.row_status(marks, "library", "abc123"), "problem")

    def test_status_table_disc_absent_marks_not_run(self):
        marks_all = [runs.make_mark(r["id"], "seen", "old", 100.0) for r in runs.run_rows(True)]
        table = runs.status_table(marks_all, "abc123", False)
        self.assertEqual(table["library"], "not run")
        self.assertEqual(table["field"], "not run")
        self.assertEqual(table["act:idle"], "not run")

    def test_status_table_disc_present_mismatched_hash(self):
        marks_all = [runs.make_mark(r["id"], "seen", "old", 100.0) for r in runs.run_rows(True)]
        table = runs.status_table(marks_all, "abc123", True)
        for rid, status in table.items():
            self.assertEqual(status, "not run")

    def test_status_table_all_rows_present(self):
        table = runs.status_table([], "abc123", True)
        ids = [r["id"] for r in runs.run_rows(True)]
        self.assertEqual(set(table.keys()), set(ids))
        for rid in ids:
            self.assertEqual(table[rid], "not run")


class TestCoverage(unittest.TestCase):
    def test_check_coverage_all_seen_no_findings(self):
        marks = [runs.make_mark(r["id"], "seen", "abc123", 100.0) for r in runs.run_rows(True)]
        table = runs.status_table(marks, "abc123", True)
        findings = runs.check_coverage(table, True)
        self.assertEqual(findings, [])

    def test_check_coverage_some_not_run(self):
        marks = [
            runs.make_mark("library", "seen", "h", 1.0),
            runs.make_mark("field", "seen", "h", 1.0),
        ]
        table = runs.status_table(marks, "h", True)
        findings = runs.check_coverage(table, True)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S8.coverage")
        self.assertEqual(f["level"], "fail")
        self.assertIn("Not run yet:", f["message"])
        self.assertEqual(f["fix"], "Run the remaining rows.")

    def test_check_coverage_disc_absent_warns_not_passes(self):
        marks = [runs.make_mark("library", "seen", "h", 1.0)]
        table = runs.status_table(marks, "h", False)
        findings = runs.check_coverage(table, False)
        self.assertEqual([(f["id"], f["level"]) for f in findings], [("S8.coverage", "warn")])

    def test_check_coverage_disc_absent_library_not_run_reported(self):
        marks = []
        table = runs.status_table(marks, "h", False)
        findings = runs.check_coverage(table, False)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S8.coverage")
        self.assertIn("library", f["message"])
        self.assertNotIn("field", f["message"])
        self.assertNotIn("arena", f["message"])

    def test_check_coverage_empty_table_all_not_run(self):
        table = runs.status_table([], "h", True)
        findings = runs.check_coverage(table, True)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        for rid in [r["id"] for r in runs.run_rows(True)]:
            self.assertIn(rid, f["message"])



class TestProblem(unittest.TestCase):
    def test_check_problem_no_marks(self):
        findings = runs.check_problem([], "h")
        self.assertEqual(findings, [])

    def test_check_problem_all_seen(self):
        marks = [runs.make_mark(r["id"], "seen", "h", 1.0) for r in runs.run_rows(True)]
        findings = runs.check_problem(marks, "h")
        self.assertEqual(findings, [])

    def test_check_problem_one_problem(self):
        marks = [
            runs.make_mark("library", "seen", "h", 1.0),
            runs.make_mark("arena", "problem", "h", 2.0, problem="wrong size"),
        ]
        findings = runs.check_problem(marks, "h")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S8.problem")
        self.assertEqual(f["level"], "fail")
        self.assertEqual(f["message"], "arena: wrong size.")
        self.assertEqual(f["fix"], "Open the stage named on the row.")
        self.assertEqual(f["value"], "S4")

    def test_check_problem_latest_mark_counts(self):
        marks = [
            runs.make_mark("arena", "problem", "h", 2.0, problem="clipping"),
            runs.make_mark("arena", "seen", "h", 5.0),
        ]
        findings = runs.check_problem(marks, "h")
        self.assertEqual(findings, [])

    def test_check_problem_wrong_hash_no_findings(self):
        marks = [runs.make_mark("arena", "problem", "old", 2.0, problem="wrong look")]
        findings = runs.check_problem(marks, "h")
        self.assertEqual(findings, [])


class TestStaleDisc(unittest.TestCase):
    def test_check_stale_empty_stage_times(self):
        marks = [runs.make_mark("library", "seen", "h", 100.0)]
        findings = runs.check_stale(marks, {})
        self.assertEqual(findings, [])

    def test_check_stale_none_stage_times(self):
        marks = [runs.make_mark("library", "seen", "h", 100.0)]
        findings = runs.check_stale(marks, None)
        self.assertEqual(findings, [])

    def test_check_stale_no_marks(self):
        findings = runs.check_stale([], {"S4": 500.0, "S5": 400.0})
        self.assertEqual(findings, [])

    def test_check_stale_rows_older_than_latest_stage(self):
        marks = [
            runs.make_mark("library", "seen", "h", 100.0),
            runs.make_mark("arena", "seen", "h", 200.0),
            runs.make_mark("act:attack", "seen", "h", 300.0),
        ]
        # Latest stage change at 250.0
        findings = runs.check_stale(marks, {"S4": 250.0, "S6": 200.0})
        self.assertEqual(len(findings), 2)
        for f in findings:
            self.assertEqual(f["id"], "S8.stale-run")
            self.assertEqual(f["level"], "warn")
            self.assertEqual(f["fix"], "Run it again.")
        stale_rows = {f["message"].split()[0] for f in findings}
        self.assertEqual(stale_rows, {"library", "arena"})

    def test_check_stale_rows_newer_than_latest_stage(self):
        marks = [
            runs.make_mark("library", "seen", "h", 500.0),
            runs.make_mark("arena", "seen", "h", 600.0),
        ]
        # Latest stage change at 400.0
        findings = runs.check_stale(marks, {"S4": 400.0, "S5": 300.0})
        self.assertEqual(findings, [])

    def test_check_disc_available(self):
        findings = runs.check_disc(True)
        self.assertEqual(findings, [])

    def test_check_disc_unavailable(self):
        findings = runs.check_disc(False)
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f["id"], "S8.disc")
        self.assertEqual(f["level"], "info")
        self.assertEqual(f["message"], "Field and arena scenes need the disc.")
        self.assertEqual(f["fix"], "Library turntable only; set MEMORIES_DISC for field and arena.")


class TestRunS8(unittest.TestCase):
    def test_run_s8_returns_dict_with_keys(self):
        result = runs.run_s8({}, "h", True)
        self.assertEqual(set(result.keys()), {"rows", "status", "findings"})
        self.assertIsInstance(result["rows"], list)
        self.assertIsInstance(result["status"], dict)
        self.assertIsInstance(result["findings"], list)

    def test_run_s8_clean_recipe_no_findings(self):
        marks = [runs.make_mark(r["id"], "seen", "h", 100.0) for r in runs.run_rows(True)]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True, {"S4": 50.0})
        self.assertEqual(result["findings"], [])

    def test_run_s8_bad_recipe_coverage_finding(self):
        marks = [runs.make_mark("library", "seen", "h", 100.0)]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["id"], "S8.coverage")

    def test_run_s8_bad_recipe_problem_finding(self):
        marks = [
            runs.make_mark("library", "seen", "h", 100.0),
            runs.make_mark("arena", "problem", "h", 200.0, "wrong size"),
        ]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True)
        prob = [f for f in result["findings"] if f["id"] == "S8.problem"]
        self.assertEqual(len(prob), 1)
        self.assertEqual(prob[0]["message"], "arena: wrong size.")

    def test_run_s8_rows_present(self):
        result = runs.run_s8({}, "h", True)
        row_ids = [r["id"] for r in result["rows"]]
        expected = [r["id"] for r in runs.run_rows(True)]
        self.assertEqual(row_ids, expected)

    def test_run_s8_status_present(self):
        marks = [runs.make_mark(r["id"], "seen", "h", 100.0) for r in runs.run_rows(True)]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True)
        for rid in [r["id"] for r in runs.run_rows(True)]:
            self.assertIn(rid, result["status"])
            self.assertEqual(result["status"][rid], "seen")

    def test_run_s8_mark_without_hash_not_counted(self):
        marks = [runs.make_mark("library", "seen", "old", 100.0)]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True)
        self.assertEqual(result["status"]["library"], "not run")
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["id"], "S8.coverage")

    def test_run_s8_disc_unavailable(self):
        marks = []
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", False)
        finding_ids = [f["id"] for f in result["findings"]]
        self.assertIn("S8.disc", finding_ids)
        self.assertIn("S8.coverage", finding_ids)
        self.assertEqual(result["status"]["library"], "not run")
        self.assertEqual(result["status"]["field"], "not run")
        self.assertEqual(result["status"]["arena"], "not run")

    def test_run_s8_stale_findings(self):
        marks = [
            runs.make_mark("library", "seen", "h", 100.0),
            runs.make_mark("arena", "seen", "h", 200.0),
        ]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True, {"S4": 150.0})
        stale = [f for f in result["findings"] if f["id"] == "S8.stale-run"]
        self.assertEqual(len(stale), 1)
        self.assertIn("library", stale[0]["message"])

    def test_run_s8_empty_recipe(self):
        result = runs.run_s8({}, "h", True)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["id"], "S8.coverage")
        for rid in [r["id"] for r in runs.run_rows(True)]:
            self.assertIn(rid, result["findings"][0]["message"])

    def test_run_s8_problem_value_is_owning_stage(self):
        marks = [runs.make_mark("arena", "problem", "h", 100.0, "wrong look")]
        recipe = {"runs": marks}
        result = runs.run_s8(recipe, "h", True)
        prob = [f for f in result["findings"] if f["id"] == "S8.problem"][0]
        self.assertEqual(prob["value"], "S7")

    def test_run_s8_marks_default_empty(self):
        result = runs.run_s8({"other": "data"}, "h", True)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["id"], "S8.coverage")

if __name__ == "__main__":
    unittest.main()