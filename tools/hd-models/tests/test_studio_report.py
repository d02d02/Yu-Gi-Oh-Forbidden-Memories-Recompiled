import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import report


class TestStageStatus(unittest.TestCase):
    def test_not_run(self):
        self.assertEqual(report.stage_status(None, []), "not run")

    def test_pass(self):
        findings = [{"id": "S4.ok", "level": "info", "message": "ok", "fix": ""}]
        self.assertEqual(report.stage_status(findings, []), "pass")

    def test_empty_list_passes(self):
        self.assertEqual(report.stage_status([], []), "pass")

    def test_fail(self):
        findings = [{"id": "S4.bad", "level": "fail", "message": "bad", "fix": "fix"}]
        self.assertEqual(report.stage_status(findings, []), "fail")

    def test_acked_fail_still_fails(self):
        # A fail is never hidden by acknowledgement.
        findings = [{"id": "S4.bad", "level": "fail", "message": "bad", "fix": "fix"}]
        self.assertEqual(report.stage_status(findings, ["S4.bad"]), "fail")

    def test_warn(self):
        findings = [{"id": "S4.meh", "level": "warn", "message": "meh", "fix": "fix"}]
        self.assertEqual(report.stage_status(findings, []), "warn")

    def test_warn_acked_is_warn(self):
        findings = [{"id": "S4.meh", "level": "warn", "message": "meh", "fix": "fix"}]
        self.assertEqual(report.stage_status(findings, ["S4.meh"]), "warn")

    def test_fail_takes_precedence_over_warn(self):
        findings = [
            {"id": "S4.meh", "level": "warn", "message": "meh", "fix": "fix"},
            {"id": "S4.bad", "level": "fail", "message": "bad", "fix": "fix"},
        ]
        self.assertEqual(report.stage_status(findings, []), "fail")


class TestStageLines(unittest.TestCase):
    def test_not_run(self):
        self.assertEqual(report.stage_lines("S4", None, []), ["Not run."])

    def test_no_findings(self):
        self.assertEqual(report.stage_lines("S4", [], []), ["No findings."])

    def test_with_fail(self):
        findings = [{"id": "S4.bad", "level": "fail", "message": "bad", "fix": "fix it"}]
        lines = report.stage_lines("S4", findings, [])
        self.assertEqual(lines[0], "### S4 Size - fail")
        self.assertEqual(lines[1], "- **fail** S4.bad: bad (fix it)")

    def test_with_warn(self):
        findings = [{"id": "S4.meh", "level": "warn", "message": "meh", "fix": ""}]
        lines = report.stage_lines("S4", findings, [])
        self.assertEqual(lines[0], "### S4 Size - warn")
        self.assertEqual(lines[1], "- **warn** S4.meh: meh")

    def test_acked_warn_shows_acknowledged(self):
        findings = [{"id": "S4.meh", "level": "warn", "message": "meh", "fix": "fix"}]
        lines = report.stage_lines("S4", findings, ["S4.meh"])
        self.assertEqual(lines[1], "- **warn** S4.meh: meh (fix) [acknowledged]")

    def test_multiple_findings(self):
        findings = [
            {"id": "S4.a", "level": "fail", "message": "a", "fix": ""},
            {"id": "S4.b", "level": "warn", "message": "b", "fix": "fixb"},
        ]
        lines = report.stage_lines("S4", findings, ["S4.b"])
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[1], "- **fail** S4.a: a")
        self.assertEqual(lines[2], "- **warn** S4.b: b (fixb) [acknowledged]")


def _row(lines, stage):
    for row in lines[2:]:
        parts = row.split("|")
        if parts[2].strip() == stage:
            return parts
    raise AssertionError(f"no row for {stage}")


class TestSummaryTable(unittest.TestCase):
    def test_header_and_separator(self):
        lines = report.summary_table({}, [])
        self.assertEqual(lines[0], "| Group | Stage | Name | Status |")
        self.assertEqual(lines[1], "| --- | --- | --- | --- |")

    def test_ten_rows_in_order(self):
        lines = report.summary_table({}, [])
        self.assertEqual(len(lines), 12)
        stages = [row.split("|")[2].strip() for row in lines[2:]]
        self.assertEqual(stages, [s for s, _ in report.STAGES])

    def test_empty_findings_all_not_run(self):
        lines = report.summary_table({}, [])
        for stage, _ in report.STAGES:
            self.assertEqual(_row(lines, stage)[4].strip(), "not run")

    def test_groups(self):
        groups = {"S0": "Prepare", "S1": "Prepare", "S2": "Prepare", "S3": "Prepare",
                  "S4": "Fit", "S5": "Fit", "S6": "Fit",
                  "S7": "Judge", "S8": "Judge", "S9": "Ship"}
        lines = report.summary_table({}, [])
        for stage, group in groups.items():
            self.assertEqual(_row(lines, stage)[1].strip(), group)

    def test_status_from_findings(self):
        findings = {"S4": [{"id": "S4.bad", "level": "fail", "message": "bad", "fix": "fix"}]}
        lines = report.summary_table(findings, [])
        self.assertEqual(_row(lines, "S4")[4].strip(), "fail")
        self.assertEqual(_row(lines, "S0")[4].strip(), "not run")
        self.assertEqual(_row(lines, "S9")[4].strip(), "not run")

    def test_acked_warn_is_warn(self):
        findings = {"S7": [{"id": "S7.meh", "level": "warn", "message": "meh", "fix": "fix"}]}
        lines = report.summary_table(findings, ["S7.meh"])
        self.assertEqual(_row(lines, "S7")[4].strip(), "warn")


class TestBuildLines(unittest.TestCase):
    def test_none_is_not_built(self):
        self.assertEqual(report.build_lines(None), ["Not built."])

    def test_ok_with_files(self):
        build = {"ok": True, "files": [("a.stl", "0123456789abcdef")], "text": "ok"}
        lines = report.build_lines(build)
        self.assertEqual(lines[0], "Build: ok")
        self.assertEqual(lines[1], "Files: 1")
        self.assertEqual(lines[2], "- a.stl 0123456789ab")

    def test_failed(self):
        build = {"ok": False, "files": [], "text": "nope"}
        lines = report.build_lines(build)
        self.assertEqual(lines[0], "Build: failed")
        self.assertEqual(lines[1], "Files: 0")
        self.assertEqual(len(lines), 2)

    def test_shorthand_sha(self):
        sha = "deadbeefcafebabe1234567890abcdef"
        build = {"ok": True, "files": [("p", sha)], "text": "ok"}
        self.assertEqual(report.build_lines(build)[2], f"- p {sha[:12]}")

    def test_truncates_to_twenty(self):
        files = [("f%d.stl" % i, "0" * 32) for i in range(25)]
        build = {"ok": True, "files": files, "text": "ok"}
        lines = report.build_lines(build)
        # header + 20 bullets + 1 more line
        self.assertEqual(len(lines), 2 + 20 + 1)
        self.assertEqual(lines[1], "Files: 25")
        self.assertEqual(lines[2], "- f0.stl 000000000000")
        self.assertEqual(lines[22], "- ... 5 more")

    def test_exactly_twenty_no_more(self):
        files = [("f%d.stl" % i, "0" * 32) for i in range(20)]
        build = {"ok": True, "files": files, "text": "ok"}
        lines = report.build_lines(build)
        self.assertEqual(len(lines), 2 + 20)
        self.assertEqual(lines[1], "Files: 20")


class TestRunsLines(unittest.TestCase):
    def test_none_is_no_runs(self):
        self.assertEqual(report.runs_lines(None), ["No scene runs recorded."])

    def test_empty_is_no_runs(self):
        self.assertEqual(report.runs_lines([]), ["No scene runs recorded."])

    def test_seen(self):
        runs = [{"row": "R1", "result": "seen", "problem": None, "time": 1.0}]
        self.assertEqual(report.runs_lines(runs), ["- R1: seen"])

    def test_problem(self):
        runs = [{"row": "R1", "result": "problem", "problem": "x", "time": 1.0}]
        self.assertEqual(report.runs_lines(runs), ["- R1: problem (x)"])

    def test_latest_mark_per_row(self):
        runs = [
            {"row": "R1", "result": "seen", "problem": None, "time": 1.0},
            {"row": "R1", "result": "problem", "problem": "fail", "time": 2.0},
            {"row": "R1", "result": "seen", "problem": None, "time": 1.5},
        ]
        self.assertEqual(report.runs_lines(runs), ["- R1: problem (fail)"])

    def test_first_seen_row_order(self):
        runs = [
            {"row": "B", "result": "problem", "problem": "y", "time": 3.0},
            {"row": "A", "result": "seen", "problem": None, "time": 1.0},
            {"row": "A", "result": "problem", "problem": "z", "time": 2.0},
        ]
        self.assertEqual(report.runs_lines(runs), ["- B: problem (y)", "- A: problem (z)"])

class TestRender(unittest.TestCase):
    def test_clean_model_full_report(self):
        findings = {}
        acks = []
        meta = {"name": "Clean", "author": "A", "license": "MIT", "url": "https://x"}
        build = {"ok": True, "files": [("out/a.txt", "abc123def45678901234567890")], "text": "ok"}
        runs = [{"row": "A", "result": "seen", "problem": None, "time": 1.0}]
        text = report.render(findings, acks, meta, build, runs)
        self.assertTrue(text.startswith("# Model report: Clean\n"))
        self.assertIn("Author: A, License: MIT, URL: https://x", text)
        self.assertIn("## Summary", text)
        self.assertIn("| Prepare | S0 | Intake | not run |", text)
        self.assertIn("## Stages", text)
        self.assertIn("## Build", text)
        self.assertIn("## Scene runs", text)
        self.assertTrue(text.endswith("\n"))

    def test_model_with_fail_warn_build_problem(self):
        findings = {
            "S4": [{"id": "S4.footprint", "level": "fail", "message": "big", "fix": "trim"}],
            "S7": [{"id": "S7.light", "level": "warn", "message": "dim", "fix": "brighten"}],
        }
        acks = ["S7.light"]
        meta = {"name": "Bad"}
        build = {"ok": False, "files": [("out/b.bin", "deadbeef")], "text": "err"}
        runs = [{"row": "A", "result": "problem", "problem": "crash", "time": 1.0}]
        text = report.render(findings, acks, meta, build, runs)
        self.assertIn("Provenance missing.", text)
        self.assertIn("### S4 Size - fail", text)
        self.assertIn("- **fail** S4.footprint: big (trim)", text)
        self.assertIn("### S7 Look - warn", text)
        self.assertIn("- **warn** S7.light: dim (brighten) [acknowledged]", text)
        self.assertIn("Build: failed", text)
        self.assertIn("- out/b.bin deadbeef", text)
        self.assertIn("- A: problem (crash)", text)

    def test_unnamed_and_provenance_missing_and_empty(self):
        findings = {}
        acks = []
        meta = {}
        build = None
        runs = []
        text = report.render(findings, acks, meta, build, runs)
        self.assertTrue(text.startswith("# Model report: unnamed\n"))
        self.assertIn("Provenance missing.", text)
        self.assertIn("Not built.", text)
        self.assertIn("No scene runs recorded.", text)


if __name__ == "__main__":
    unittest.main()
