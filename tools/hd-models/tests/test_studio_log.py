import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio import log


class LogTest(unittest.TestCase):
    def tearDown(self):
        log.detach()

    def test_size_is_capped_and_errors_are_kept(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(log.attach(d), Path(d) / "studio.log")
            for _ in range(8000):
                log.event("S5", "audit", "x" * 300)
            log.error("build", ValueError("boom\nline2"))
            sizes = [f.stat().st_size for f in Path(d).iterdir()]
            self.assertLessEqual(len(sizes), log.BACKUPS + 1)
            self.assertLessEqual(sum(sizes), (log.BACKUPS + 1) * log.MAX_BYTES)
            self.assertEqual(log.last_error, "build: boom\nline2")
            self.assertIn("ERROR", (Path(d) / "studio.log").read_text(encoding="utf-8"))

    def test_long_message_is_cut(self):
        self.assertLess(len(log.clip("a" * 50000)), log.MAX_LINE + 60)

    def test_unwritable_folder_gives_no_log_not_a_crash(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertIsNone(log.attach(Path(f.name) / "sub"))
            log.event("S0", "x")


if __name__ == "__main__":
    unittest.main()
