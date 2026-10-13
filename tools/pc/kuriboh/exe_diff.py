"""Diff a modified game's SLUS_014.11 against retail and name what changed.

    python tools/pc/kuriboh/exe_diff.py <retail .bin> <modified .bin> [-o report.md]

Runs of changed bytes (gaps up to GAP bytes merged) are placed in the function
or symbol that owns them, using config/slus_01411/functions.csv and symbols.txt.
Reads the discs only. Writes the report where -o says (use tmp/kuriboh/).
"""
import argparse
import bisect
import csv
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "pc"))
from fm_editor import disc  # noqa: E402

GAP = 8
HEADER = 0x800


def owners():
    funcs = []
    for r in csv.DictReader(open(ROOT / "config/slus_01411/functions.csv", encoding="utf-8")):
        funcs.append((int(r["address"], 16), int(r["size"], 16), r["name"], r["status"]))
    funcs.sort()
    syms = []
    for line in open(ROOT / "config/slus_01411/symbols.txt", encoding="utf-8"):
        m = re.match(r"\s*(\S+)\s*=\s*(0x[0-9A-Fa-f]+)", line)
        if m:
            syms.append((int(m.group(2), 16), m.group(1)))
    syms.sort()
    return funcs, syms


def owner(addr, funcs, syms):
    starts = [f[0] for f in funcs]
    i = bisect.bisect_right(starts, addr) - 1
    if i >= 0 and addr < funcs[i][0] + funcs[i][1]:
        f = funcs[i]
        return f"fn {f[2]}+0x{addr - f[0]:X} [{f[3]}]"
    ss = [s[0] for s in syms]
    j = bisect.bisect_right(ss, addr) - 1
    if j >= 0:
        return f"data {syms[j][1]}+0x{addr - syms[j][0]:X}"
    return "unknown"


def runs(a, b, base):
    out, start, last = [], None, None
    for off in range(HEADER, min(len(a), len(b))):
        if a[off] != b[off]:
            if start is None:
                start = off
            elif off - last > GAP:
                out.append((start, last))
                start = off
            last = off
    if start is not None:
        out.append((start, last))
    return [(base + s - HEADER, base + e - HEADER) for s, e in out]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("retail")
    p.add_argument("modified")
    p.add_argument("-o")
    args = p.parse_args()
    r, m = disc.load(args.retail).slus, disc.load(args.modified).slus
    base = struct.unpack_from("<I", r, 0x18)[0]
    funcs, syms = owners()
    lines = [f"retail {len(r)} bytes, modified {len(m)} bytes, load 0x{base:08X}", ""]
    by_owner = {}
    for s, e in runs(r, m, base):
        key = owner(s, funcs, syms).split("+")[0]
        by_owner.setdefault(key, []).append((s, e))
    total = 0
    for key, rs in sorted(by_owner.items(), key=lambda kv: kv[1][0][0]):
        n = sum(e - s + 1 for s, e in rs)
        total += n
        lines.append(f"{key}: {n} bytes in {len(rs)} run(s), first 0x{rs[0][0]:08X}")
    lines.insert(2, f"{total} bytes changed in {len(by_owner)} functions/symbols")
    text = "\n".join(lines) + "\n"
    if args.o:
        Path(args.o).write_text(text, encoding="utf-8")
    print(text[:4000])


main()
