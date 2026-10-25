"""Tests for the native camera transport client methods, with a fake socket."""

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


class CamTransportTest(unittest.TestCase):
    def test_preset(self):
        g = game("ok cam preset front")
        self.assertEqual(g.cam_preset("front"), "cam preset front")
        self.assertEqual(g.connection.sent, ["cam preset front\n"])

    def test_set(self):
        g = game("ok cam set")
        g.cam_set(0.0, 0.0, 1.0, 0.0)
        self.assertEqual(g.connection.sent, ["cam set 0.0 0.0 1.0 0.0\n"])

    def test_off(self):
        g = game("ok cam off")
        self.assertIsNone(g.cam_off())
        self.assertEqual(g.connection.sent, ["cam off\n"])

    def test_get_on(self):
        g = game("ok cam yaw=10.00 pitch=5.00 dist=1.20 height=0.00")
        self.assertEqual(g.cam_get(), {"yaw": 10.0, "pitch": 5.0, "dist": 1.2, "height": 0.0})
        self.assertEqual(g.connection.sent, ["cam get\n"])

    def test_get_off(self):
        g = game("ok cam off")
        self.assertIsNone(g.cam_get())
        self.assertEqual(g.connection.sent, ["cam get\n"])

    def test_error_raises(self):
        g = game("err unknown preset")
        with self.assertRaises(ControlError):
            g.cam_preset("unknown")

if __name__ == "__main__":
    unittest.main()
