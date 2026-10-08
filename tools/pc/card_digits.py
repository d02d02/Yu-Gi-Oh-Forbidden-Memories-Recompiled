"""The anime frame's ATK/DFD digits, drawn from a font.

One PNG for the engine (src/pc/cards/card_layout_art.h's digit strip):
5 x 2 cells of 40 x 44 texels, digit d in column d % 5, row d / 5, in the
same 10 x 11 unit proportion the layout draws a digit at ("digits" in
card_layout). The font is the maker's own file (a Yu-Gi-Oh. Matrix Regular
Small Caps .ttf, the card game's ATK/DEF font): it is read from --digit-font
and never committed.
"""
from PIL import Image, ImageDraw, ImageFont

COLS, ROWS = 5, 2
CELL_W, CELL_H = 40, 44
GLYPH_H = 34          # the digits' height in texels: 8.5 of the box's 17 units
INK = (22, 14, 6)
PAPER = (242, 226, 169)   # what the stat box is, for the edge pixels
SUPER = 8
STRETCH = 1.4         # the game draws these digits wide: a zero is about as wide as it is tall


def render(font_path, out_path):
    probe = ImageFont.truetype(font_path, 200)
    boxes = [probe.getbbox(str(d), anchor="ls") for d in range(10)]
    top, bottom = min(b[1] for b in boxes), max(b[3] for b in boxes)
    size = 200 * GLYPH_H * SUPER / (bottom - top)
    font = ImageFont.truetype(font_path, round(size))
    sheet = Image.new("RGBA", (COLS * CELL_W, ROWS * CELL_H), (0, 0, 0, 0))
    for d in range(10):
        mask = Image.new("L", (CELL_W * SUPER, CELL_H * SUPER), 0)
        draw = ImageDraw.Draw(mask)
        box = font.getbbox(str(d), anchor="ls")
        x = (CELL_W * SUPER - (box[2] - box[0])) // 2 - box[0]
        base = (CELL_H * SUPER - GLYPH_H * SUPER) // 2 - round(top * size / 200)
        draw.text((x, base), str(d), font=font, fill=255, anchor="ls")
        wide = mask.resize((round(mask.width * STRETCH), mask.height), Image.LANCZOS)
        left = (wide.width - mask.width) // 2
        alpha = wide.crop((left, 0, left + mask.width, mask.height)).resize((CELL_W, CELL_H), Image.BOX)
        cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        px, src = cell.load(), alpha.load()
        for yy in range(CELL_H):
            for xx in range(CELL_W):
                a = src[xx, yy] / 255
                if a >= 0.35:   # the game's texture has one transparent index, no partial alpha
                    px[xx, yy] = tuple(round(INK[i] * a + PAPER[i] * (1 - a)) for i in range(3)) + (255,)
        sheet.paste(cell, (d % COLS * CELL_W, d // COLS * CELL_H))
    sheet.save(out_path)
    return sheet


if __name__ == "__main__":
    import sys
    render(sys.argv[1], sys.argv[2])
