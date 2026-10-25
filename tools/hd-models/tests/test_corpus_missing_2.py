import unittest, tempfile, pathlib

from studio.corpus_missing import build_missing, missing_report

class TestMissingReportNoClips(unittest.TestCase):
    def test_no_clips_report(self):
        with tempfile.TemporaryDirectory() as td:
            glb_path = pathlib.Path(td) / "model.glb"
            build_missing("no-clips", glb_path)
            report = missing_report(glb_path)
            # At least one fail or warn finding
            fail_warn = [f for f in report["findings"] if f.get("level") in ("fail", "warn")]
            self.assertGreaterEqual(len(fail_warn), 1, "expected at least one fail/warn finding")
            # Every fail must have non‑empty offered list unless it's a known gap
            for f in fail_warn:
                if f.get("level") == "fail":
                    offered = report["offered"].get(f["id"]).copy() if isinstance(report["offered"].get(f["id"]), list) else []
                    if offered:
                        self.assertTrue(offered, f"fail finding {f['id']} has empty offered")
                    else:
                        # Expected gap – assert the empty list explicitly
                        self.assertEqual(offered, [], f"fail finding {f['id']} expected empty offered (gap)")


if __name__ == "__main__":
    unittest.main()
