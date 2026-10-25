import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from studio import corpus_missing   # noqa: E402


class MissingKindsOfferResolutions(unittest.TestCase):
    def report(self, kind):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.glb"
            corpus_missing.build_missing(kind, path)
            return corpus_missing.missing_report(path)

    def test_every_fail_offers_a_resolution(self):
        for kind in corpus_missing.MISSING_KINDS:
            report = self.report(kind)
            fails = [f for f in report["findings"] if f["level"] == "fail"]
            self.assertTrue(fails, kind)
            for f in fails:
                self.assertTrue(report["offered"][f["id"]], f"{kind}: {f['id']} offers no resolution")

    def test_no_fail_offers_accept(self):
        for kind in corpus_missing.MISSING_KINDS:
            report = self.report(kind)
            for f in report["findings"]:
                if f["level"] == "fail":
                    self.assertNotIn("accept", report["offered"][f["id"]])

    def test_every_warn_offers_a_resolution(self):
        for kind in corpus_missing.MISSING_KINDS:
            report = self.report(kind)
            for f in report["findings"]:
                if f["level"] == "warn":
                    self.assertTrue(report["offered"][f["id"]], f"{kind}: {f['id']}")


if __name__ == "__main__":
    unittest.main()
