"""Per changed function: the retail and modified MIPS, only the lines that differ.

    PYTHONPATH=tmp/kuriboh/pylib python tools/pc/kuriboh/exe_dis.py <retail .bin> <modified .bin> -o tmp/kuriboh/code_diff.txt

Needs capstone (pip install --target tmp/kuriboh/pylib capstone; not a project dependency).
"""
import argparse
import csv
import struct
import sys
from pathlib import Path

import capstone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "pc"))
from fm_editor import disc  # noqa: E402

HEADER = 0x800
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)


def dis(code, addr):
    return {i.address: f"{i.mnemonic} {i.op_str}".strip() for i in md.disasm(code, addr)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("retail")
    p.add_argument("modified")
    p.add_argument("-o")
    a = p.parse_args()
    r, m = disc.load(a.retail).slus, disc.load(a.modified).slus
    base = struct.unpack_from("<I", r, 0x18)[0]
    out = []
    for row in csv.DictReader(open(ROOT / "config/slus_01411/functions.csv", encoding="utf-8")):
        start, size = int(row["address"], 16), int(row["size"], 16)
        if not size or start < base:
            continue
        off = start - base + HEADER
        if r[off:off + size] == m[off:off + size]:
            continue
        old, new = dis(r[off:off + size], start), dis(m[off:off + size], start)
        out.append(f"== {row['name']} 0x{start:08X} size 0x{size:X} ({row['status']})")
        for addr in sorted(set(old) | set(new)):
            if old.get(addr) != new.get(addr):
                out.append(f"  {addr:08X}  - {old.get(addr, '')}\n            + {new.get(addr, '')}")
    text = "\n".join(out) + "\n"
    if a.o:
        Path(a.o).write_text(text, encoding="utf-8")
    print(text[:300])


main()
