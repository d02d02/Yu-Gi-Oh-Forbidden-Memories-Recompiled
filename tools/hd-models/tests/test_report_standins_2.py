import unittest
from studio import report

class TestRenderStandIns(unittest.TestCase):
    def test_default_none(self):
        # No stand_ins provided, should show default line
        text = report.render({}, [], {}, None, [])
        self.assertIn("## Stand-ins", text)
        self.assertIn("None: every part is authentic.", text)

    def test_given_stand_ins(self):
        stand_ins = [{
            "check": "S5.test",
            "value": "val",
            "kind": "fallback",
            "data": {"source": "proc:val"}
        }]
        text = report.render({}, [], {}, None, [], stand_ins=stand_ins)
        self.assertIn("## Stand-ins", text)
        self.assertIn("- S5.test (val) : tool-made stand-in, source proc:val", text)

if __name__ == "__main__":
    unittest.main()
