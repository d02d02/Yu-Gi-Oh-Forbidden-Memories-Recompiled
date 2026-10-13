"""A pool stored as one byte a card (Kuriboh's first fifteen duelists)."""
import struct
import unittest
from types import SimpleNamespace

from fm_editor import gamedata as g, importer


class BytePoolTest(unittest.TestCase):
    def test_bytes_adding_up_to_2048_replace_halfwords_that_do_not(self):
        wa = bytearray(g.DUELIST_BASE + 2 * g.DUELIST_STRIDE + 0x2000)
        at = g.DUELIST_BASE + 1 * g.DUELIST_STRIDE + g.POOL_OFFSETS["deck"]
        weights = {5: 200, 6: 48}
        weights.update({c: 100 for c in range(10, 28)})        # 18 x 100
        assert sum(weights.values()) == g.POOL_TOTAL
        for cid, w in weights.items():
            wa[at + cid - 1] = w
        pools = [{n: {1: g.POOL_TOTAL} for n in g.POOLS} for _ in range(2)]
        pools[1]["deck"] = {1: 12345}                          # what the halfwords read as
        modded = SimpleNamespace(pools=pools)
        notes = importer.read_byte_pools(modded, SimpleNamespace(wa=bytes(wa)))
        self.assertEqual(weights, modded.pools[1]["deck"])
        self.assertEqual({1: g.POOL_TOTAL}, modded.pools[0]["deck"])     # already right: untouched
        self.assertEqual(1, len(notes))


if __name__ == "__main__":
    unittest.main()
