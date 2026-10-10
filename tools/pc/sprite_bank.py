#!/usr/bin/env python3
"""Read a screen's sprite bank (the one-sector display resource every package loads) and assemble its frames.

A bank is a 2 KB sector: a three-level tree of little-endian u16 offsets leads to command streams, whose entries
are (duration, u16 offset of a frame). A frame is a 4-byte header (count, flags, tpage, clut) and `count` 6-byte
parts (dx, dy, cell, size), exactly as DisplayObject_RenderSpriteSheet draws them (src/game/
display_object_render_sprite_sheet.c): a part is the (u, v) cell of the page, (w, h) big, drawn at (dx, dy) from the
object's origin. This module only decodes; hd_sprite_pack.py assembles frames from the sheets and enlarges them whole.
"""
import struct


def parts_of(bank: bytes, offset: int):
    """(count, flags, tpage, clut, [(dx, dy, u, v, w, h, cell, size)]) of the frame at `offset`, or None."""
    if offset + 4 > len(bank):
        return None
    count, flags, tpage, clut = bank[offset:offset + 4]
    if not 1 <= count <= 64 or offset + 4 + 6 * count > len(bank):
        return None
    parts = []
    for i in range(count):
        dx, dy, cell, size = struct.unpack_from("<bbHH", bank, offset + 4 + 6 * i)
        if flags & 0x10:
            dx = (dx & 0xFF) | ((cell & 0xC000) >> 6)
            dy = (dy & 0xFF) | ((size & 0xC000) >> 6)
            dx -= 0x400 if dx & 0x200 else 0
            dy -= 0x400 if dy & 0x200 else 0
        u, v = (cell & 0x1F) * 8, ((cell >> 5) & 0x1F) * 8
        w, h = ((size >> 5) & 0xF) * 8 + 8, ((size >> 9) & 0xF) * 8 + 8
        parts.append((dx, dy, u, v, w, h, cell, size))
    return count, flags, tpage, clut, parts


def candidate_frames(bank: bytes):
    """Every offset a u16 anywhere in the bank points at that holds a frame header that fits."""
    seen = {}
    for at in range(0, len(bank) - 1):
        target = struct.unpack_from("<H", bank, at)[0]
        if target in seen or target < 0x40 or target >= len(bank):
            continue
        frame = parts_of(bank, target)
        if frame:
            seen[target] = frame
    return seen


if __name__ == "__main__":
    import sys
    data = open(sys.argv[1], "rb").read()
    sector = int(sys.argv[2])
    bank = data[sector * 2048:(sector + 1) * 2048]
    for offset, (count, flags, tpage, clut, parts) in sorted(candidate_frames(bank).items()):
        print(f"{offset:04x} n={count} flags={flags:02x} tpage={tpage} clut={clut:02x}", parts[:4])
