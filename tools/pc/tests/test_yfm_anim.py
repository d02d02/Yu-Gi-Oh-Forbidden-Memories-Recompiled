"""Tests for the native animation transport client methods, with a fake socket."""

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


class AnimTransportTest(unittest.TestCase):
    def test_clip(self):
        g = game("ok clip=dragon_attack")
        self.assertEqual(g.anim_clip("dragon_attack"), "dragon_attack")
        self.assertEqual(g.connection.sent, ["anim clip dragon_attack\n"])

    def test_clip_auto(self):
        g = game("ok clip=auto")
        self.assertEqual(g.anim_clip(None), "auto")
        self.assertEqual(g.connection.sent, ["anim clip auto\n"])

    def test_pause_resume(self):
        g = game("ok paused", "ok resumed")
        self.assertIsNone(g.anim_pause())
        self.assertIsNone(g.anim_resume())
        self.assertEqual(g.connection.sent, ["anim pause\n", "anim resume\n"])

    def test_speed(self):
        g = game("ok speed=2.500")
        self.assertEqual(g.anim_speed(2.5), 2.5)
        self.assertEqual(g.connection.sent, ["anim speed 2.5\n"])

    def test_phase(self):
        g = game("ok phase=0.250")
        self.assertEqual(g.anim_phase(0.25), 0.25)
        self.assertEqual(g.connection.sent, ["anim phase 0.25\n"])

    def test_phase_cleared(self):
        g = game("ok phase=cleared")
        self.assertIsNone(g.anim_phase(-1))
        self.assertEqual(g.connection.sent, ["anim phase -1\n"])

    def test_frame(self):
        g = game("ok frame=12")
        self.assertEqual(g.anim_frame(12), 12)
        self.assertEqual(g.connection.sent, ["anim frame 12\n"])

    def test_frame_cleared(self):
        g = game("ok frame=cleared")
        self.assertIsNone(g.anim_frame(-1))
        self.assertEqual(g.connection.sent, ["anim frame -1\n"])

    def test_get(self):
        g = game("ok active=1 clip=dragon_attack paused=0 speed=0.500 phase=set frame=none")
        self.assertEqual(g.anim_get(), {
            "active": 1,
            "clip": "dragon_attack",
            "paused": 0,
            "speed": 0.5,
            "phase": "set",
            "frame": "none",
        })
        self.assertEqual(g.connection.sent, ["anim get\n"])

    def test_error_raises(self):
        g = game("err clip needs a name")
        with self.assertRaises(ControlError):
            g.anim_clip("")


if __name__ == "__main__":
    unittest.main()
