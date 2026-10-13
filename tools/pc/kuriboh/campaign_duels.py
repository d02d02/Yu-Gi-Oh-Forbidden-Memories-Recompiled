"""Every duel the campaign's dialogue scripts start (F8 0D: opponent, two bytes, terrain, music), in a retail
disc and a modified one, side by side.

    python tools/pc/kuriboh/campaign_duels.py <retail> <modified> [-o report]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "pc"))
from fm_editor import disc, gamedata as g  # noqa: E402
import text_listing as tl  # noqa: E402


def duels(path):
    image = g._image(disc.load(path).slus)
    names = g.plain_names(image, tl.glyph_characters(image))
    bank = next(b for b in tl.banks(image) if b.name == "dialog")
    text = tl.write_listing(image, [bank], names)
    out, current = [], None
    for line in text.splitlines():
        m = re.match(r"\[([0-9A-Fa-f]{4})\]", line)
        if m:
            current = m.group(1)
        for d in re.finditer(r"\{f8 0D ([0-9A-F]{2}) ([0-9A-F]{2}) ([0-9A-F]{2}) ([0-9A-F]{2}) ([0-9A-F]{2}) ([0-9A-F]{2})\}", line):
            o, b0, b2, ter, lo, hi = (int(x, 16) for x in d.groups())
            out.append((current, o, b0, b2, ter, hi << 8 | lo))
    return out


if __name__ == "__main__":
    r, m = duels(sys.argv[1]), duels(sys.argv[2])
    names = g.DUELIST_NAMES
    def nm(o):
        return names[o] if o < len(names) else f"extra {o} (mode {o - 39})"
    lines = [f"retail: {len(r)} duel starts, modified: {len(m)}", ""]
    seen = {(s, *x) for s, *x in r}
    lines.append("string  opponent               b370 b372 terrain bgm     (in retail?)")
    for s, o, b0, b2, ter, bgm in m:
        lines.append(f"[{s}]  {o:3d} {nm(o):28s} {b0:02X}   {b2:02X}   {ter:3d}   {bgm:04X}  {'yes' if (s, o, b0, b2, ter, bgm) in seen else 'NEW/CHANGED'}")
    text = "\n".join(lines)
    print(text)
    if len(sys.argv) > 3 and sys.argv[3] == "-o":
        Path(sys.argv[4]).write_text(text, encoding="utf-8")
