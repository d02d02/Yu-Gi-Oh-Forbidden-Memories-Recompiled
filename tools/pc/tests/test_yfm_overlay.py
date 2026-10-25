"""Tests for overlay client methods, with a fake socket."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from yfm_control import ControlError, Game  # noqa: E402


class FakeSocket:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def sendall(self, data):
        self.sent.append(data.decode())

    def recv(self, _size):
        if not self.replies:
            return b""
        reply = self.replies.pop(0)
        return (reply if reply.endswith("\n") else reply + "\n").encode()


def game(*replies):
    g = object.__new__(Game)
    g.connection = FakeSocket(replies)
    g._buffer = b""
    g.log_path = "fake"
    return g


class OverlayTransportTest(unittest.TestCase):
    def test_bbox_on(self):
        g = game("ok bbox on")
        g.ov_bbox(True)
        self.assertEqual(g.connection.sent, ["ov bbox on\n"])

    def test_grid_off(self):
        g = game("ok grid off")
        g.ov_grid(False)
        self.assertEqual(g.connection.sent, ["ov grid off\n"])

    def test_get(self):
        g = game("ok ov bbox=0 grid=1 bones=0")
        self.assertEqual(g.ov_get(), {"bbox": 0, "grid": 1, "bones": 0})
        self.assertEqual(g.connection.sent, ["ov get\n"])

    def test_bounds(self):
        g = game("ok ov min=1,2,3 max=4,5,6 lowest=2")
        self.assertEqual(g.ov_bounds(), {"min": [1.0, 2.0, 3.0], "max": [4.0, 5.0, 6.0], "lowest": 2.0})
        self.assertEqual(g.connection.sent, ["ov bounds\n"])

    def test_bounds_error(self):
        g = game("err ov: nothing drawn")
        with self.assertRaises(ControlError):
            g.ov_bounds()
        self.assertEqual(g.connection.sent, ["ov bounds\n"])


if __name__ == "__main__":
    unittest.main()
