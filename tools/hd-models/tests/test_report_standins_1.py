import sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from studio import report

class TestStandInLines(unittest.TestCase):
    def test_none(self):
        self.assertEqual(report.stand_in_lines(None), ["None: every part is authentic."])

    def test_empty(self):
        self.assertEqual(report.stand_in_lines([]), ["None: every part is authentic."])

    def test_fallback_with_value_and_source(self):
        entry = {"check": "S5.missing-act", "value": "idle", "kind": "fallback", "data": {"source": "procedural:idle"}}
        self.assertEqual(report.stand_in_lines([entry]), ["- S5.missing-act (idle) : tool-made stand-in, source procedural:idle"])

    def test_accept_without_value(self):
        entry = {"check": "S5.ok", "kind": "accept"}
        self.assertEqual(report.stand_in_lines([entry]), ["- S5.ok : accepted without it"])

    def test_fallback_without_value(self):
        entry = {"check": "S5.none", "value": None, "kind": "fallback", "data": {}}
        self.assertEqual(report.stand_in_lines([entry]), ["- S5.none : tool-made stand-in"])

if __name__ == "__main__":
    unittest.main()
