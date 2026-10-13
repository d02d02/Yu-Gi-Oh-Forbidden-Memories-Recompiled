"""A string that starts inside another string's op (Kuriboh's dialog bank)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import text_listing as tl  # noqa: E402


class FakeImage:
    def __init__(self, data: bytes):
        self.data = data

    def bytes(self, address: int, count: int) -> bytes:
        at = address - 0x801B0000
        return (self.data + bytes(0x10000))[at:at + count]


class OverlapTest(unittest.TestCase):
    def test_string_inside_an_op_drops_the_tail_not_the_bank(self):
        # string A at 1: glyph, then fx (3 bytes) at 2..4; string B starts at 3 (inside the fx).
        data = bytes([0x00, 0x10, 0xF6, 0x01, 0x08, 0x11, 0xFF])
        bank = tl.Bank("dialog", 0x801B0000)
        bank.ids = {1: 1, 2: 3}
        tl.OVERLAPS.clear()
        ops, _ = tl.decode_bank(FakeImage(data), bank, {})
        self.assertEqual(1, len(tl.OVERLAPS))
        self.assertIn(1, ops)
        self.assertNotIn(2, ops)     # the op that ran over B was dropped
        self.assertIn(3, ops)        # B itself is read
        tl.OVERLAPS.clear()


if __name__ == "__main__":
    unittest.main()
