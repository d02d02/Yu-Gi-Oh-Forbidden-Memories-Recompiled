"""Disassemble a RAM range of a disc's SLUS_014.11 (the mod's code caves).

    PYTHONPATH=tmp/kuriboh/pylib python tools/pc/kuriboh/cave_dis.py <disc> 0x801CEFEC 0x801D0000
"""
import struct
import sys
from pathlib import Path

import capstone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fm_editor import disc  # noqa: E402

s = disc.load(sys.argv[1]).slus
base = struct.unpack_from("<I", s, 0x18)[0]
a, b = int(sys.argv[2], 16), int(sys.argv[3], 16)
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata = True
off = a - base + 0x800
for i in md.disasm(s[off:off + (b - a)], a):
    print(f"{i.address:08X}  {i.bytes.hex()}  {i.mnemonic} {i.op_str}".rstrip())
