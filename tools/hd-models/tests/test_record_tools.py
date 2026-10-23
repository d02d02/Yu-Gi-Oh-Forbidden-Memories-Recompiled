"""vendor/split_model.py and reassemble_model.py: a model record split into its phase files and put back is byte-identical."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vendor"))
import model_record  # noqa: E402
import reassemble_model  # noqa: E402
import split_model  # noqa: E402


class TestRoundTrip(unittest.TestCase):
    def test_split_then_reassemble_is_identical(self):
        record = bytes((i * 7 + 3) % 256 for i in range(model_record.RECORD_BYTES))
        with tempfile.TemporaryDirectory() as d:
            src, parts, out = Path(d) / "record.bin", Path(d) / "parts", Path(d) / "again.bin"
            src.write_bytes(record)
            split_model.split(src, parts)
            self.assertEqual(len(os.listdir(parts)), len(model_record.PHASES))
            reassemble_model.reassemble(parts, out)
            self.assertEqual(out.read_bytes(), record)

    def test_reassemble_refuses_a_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            record = bytes(model_record.RECORD_BYTES)
            src, parts = Path(d) / "record.bin", Path(d) / "parts"
            src.write_bytes(record)
            split_model.split(src, parts)
            first = parts / sorted(os.listdir(parts))[0]
            first.write_bytes(first.read_bytes() + b"x")
            with self.assertRaises(AssertionError):
                reassemble_model.reassemble(parts, Path(d) / "bad.bin")


if __name__ == "__main__":
    unittest.main()
