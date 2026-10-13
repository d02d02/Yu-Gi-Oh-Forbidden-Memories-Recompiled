#!/usr/bin/env python3
"""Make the Duel Links PNGs look as good as the game can show them.

  python prepare_art.py <folder of original PNGs> [<output folder>]

The output folder defaults to artes_duel_links_fm in the mod folder (shipped-art).

The game stores a field cutout in a fixed 102x96 picture (the card art's
size) whatever size the PNG is, and its own conversion is crude: it takes the
middle of the PNG at that shape and drops the rest (a tall dragon lost its top
and bottom, a wide one its wingtips), averages colour with no regard to alpha
(the colour under a clear pixel leaks into the edge as a dark fringe) and
keeps a texel only when its alpha averages 128 or more (a faded wingtip
vanished). So this does the shrinking itself, once, at full quality, and hands
the game a picture it has nothing left to spoil:

  1. trim the empty border, then centre the picture on a transparent canvas of
     the card art's shape: nothing is cropped;
  2. shrink to 102x96 with a Lanczos filter on alpha-weighted colour, so a
     clear pixel's colour never reaches the edge;
  3. a texel is solid when at least THRESHOLD of it was covered, half
     transparent (the PS1's one blend, 50%, flagged in the palette) from
     FAINT up to that, and clear under it. A wingtip the artist faded out over
     a tenth of the picture stays, as the fade it is, instead of ending in a
     straight line; the game's own conversion has no such texel;
  4. a light sharpening of the colour, since shrinking softens it;
  5. the edge ring (solid but not interior) is repainted from the interior just
     inside it: cutouts carry a light matte in their half-transparent edge
     pixels, and sharpening adds a bright rim, which show as a white contour;
  6. the colour of clear texels is borrowed from their solid neighbours, so
     the game's own filtering of the picture on screen never pulls in black;
  7. saved as the mod's own texture file (255 colours and a clear index, 256
     wide at most), which the mod draws itself. The game's own field-art
     loader would squeeze it into 102x96, and its look is mostly that: this
     keeps six times the pixels;
  8. at four sizes (LEVELS), each shrunk from the original with the same
     steps: the renderer samples a texture point by point, so a picture drawn
     much smaller than it is turns to noise (at the usual 1x resolution the
     full size is drawn at about 40 pixels). The mod loads the size nearest
     the one on screen.

The originals are not changed. Needs Pillow and numpy."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

SHAPE = (102, 96)         # the card art's shape (src/pc/cards/art.h): what the quad is drawn at
LEVELS = [(256, 241), (128, 120), (64, 60), (32, 30)]  # sizes of the texture, largest first: the shape at the most a texture page holds, then halves (duel_links.c's level_heights)
THRESHOLD = 0.30          # coverage from which a texel is solid
FAINT = 0.08              # coverage from which a texel is drawn half transparent, under THRESHOLD
NO_FAINT = {62, 165, 283, 599} # Harpy Lady, Judgement Hand, Holograh, Violent Rain: their faint pixels are a flat matte band at the border, not a fade
FAINT_COLOURS = 40        # palette entries kept for the half transparent texels (when there are any)
SHARPEN = {241: 60, 120: 40, 60: 20, 30: 0}   # unsharp-mask percent by texture height: sharpening a small picture that is point-sampled only adds sparkle
BLEED = 3                 # how many texels outward a clear texel borrows colour
CORE = 0.90               # coverage from which a texel is interior, not edge
DEFRINGE = 2              # how many texels of edge are repainted from the interior
DEFRINGE_MIX = 0.85       # how much of the repaint replaces the edge's own colour


def squared(image):
    """Trimmed, then centred on a transparent canvas of the card art's shape."""
    box = image.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        image = image.crop(box)
    w, h = image.size
    if w * SHAPE[1] >= h * SHAPE[0]:
        cw, ch = w, -(-w * SHAPE[1] // SHAPE[0])
    else:
        cw, ch = -(-h * SHAPE[0] // SHAPE[1]), h
    canvas = Image.new("RGBA", (max(cw, w), max(ch, h)), (0, 0, 0, 0))
    canvas.paste(image, ((canvas.width - w) // 2, (canvas.height - h) // 2))
    return canvas


def shrink(channel, size):
    return np.array(Image.fromarray(channel.astype(np.float32), mode="F").resize(size, Image.LANCZOS))


def defringe(rgb, alpha, size):
    """The edge ring's colour replaced by the interior's, reaching DEFRINGE texels in."""
    WIDTH, HEIGHT = size
    core = alpha >= CORE
    ring = (alpha >= THRESHOLD) & ~core
    colour = rgb.astype(np.float32)
    known = core.copy()
    borrowed = np.zeros_like(colour)
    for _ in range(DEFRINGE):
        padded = np.pad(colour * known[:, :, None], ((1, 1), (1, 1), (0, 0)))
        have = np.pad(known.astype(np.float32), 1)
        total = sum(padded[dy:dy + HEIGHT, dx:dx + WIDTH] for dy in range(3) for dx in range(3))
        count = sum(have[dy:dy + HEIGHT, dx:dx + WIDTH] for dy in range(3) for dx in range(3))
        fill = ~known & (count > 0)
        colour[fill] = total[fill] / count[fill][:, None]
        known |= fill
    reached = ring & known
    out = rgb.astype(np.float32)
    out[reached] = colour[reached] * DEFRINGE_MIX + out[reached] * (1 - DEFRINGE_MIX)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def enhance(image, fades=True):
    """The whole file: every size of the card's texture, largest first."""
    rgba = np.array(squared(image.convert("RGBA"))).astype(np.float32) / 255
    levels = [level(rgba, size, fades) for size in LEVELS]
    return np.array([len(levels)], dtype="<u2").tobytes() + b"".join(levels)


def level(rgba, size, fades):
    WIDTH, HEIGHT = size
    alpha = np.clip(shrink(rgba[:, :, 3], size), 0, 1)
    weighted = [shrink(rgba[:, :, i] * rgba[:, :, 3], size) for i in range(3)]
    rgb = np.clip(np.stack([c / np.maximum(alpha, 0.02) for c in weighted], -1), 0, 1)
    solid = alpha >= THRESHOLD
    faint = ((alpha >= FAINT) & ~solid) if fades else np.zeros_like(solid)
    known = solid.copy()
    for _ in range(BLEED):
        colour = np.pad(rgb * known[:, :, None], ((1, 1), (1, 1), (0, 0)))
        have = np.pad(known.astype(np.float32), 1)
        total = sum(colour[dy:dy + HEIGHT, dx:dx + WIDTH] for dy in range(3) for dx in range(3))
        count = sum(have[dy:dy + HEIGHT, dx:dx + WIDTH] for dy in range(3) for dx in range(3))
        fill = ~known & (count > 0)
        rgb[fill] = total[fill] / count[fill][:, None]
        known |= fill
    picture = Image.fromarray((rgb * 255 + 0.5).astype(np.uint8))
    if SHARPEN[HEIGHT]:
        picture = picture.filter(ImageFilter.UnsharpMask(radius=0.8, percent=SHARPEN[HEIGHT], threshold=2))
    picture = Image.fromarray(defringe(np.array(picture), alpha, size))
    return texture(picture, solid, faint)


def quantize(pixels, colours):
    """Index (0-based) of each of `pixels` (n x 3) in a palette of at most `colours`, and the palette."""
    count = len(pixels)
    reduced = Image.fromarray(pixels.reshape(count, 1, 3).astype(np.uint8)).quantize(
        colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.array(reduced).reshape(count), np.array(reduced.getpalette(), dtype=np.uint16).reshape(-1, 3)


def word(colour, flag):
    value = (int(colour[0]) >> 3) | ((int(colour[1]) >> 3) << 5) | ((int(colour[2]) >> 3) << 10)
    return (value or 1) | flag   # 0 would be clear


def texture(picture, solid, faint):
    """One size of the mod's own file (duel_links.c, own_texture): u16 width, u16 height,
    256 CLUT words (BGR555, 0 is clear, bit 15 marks a half transparent
    colour) and one index byte per texel: index 0 for the clear ones, then
    the solid texels' colours, then the faint texels' own few."""
    rgb = np.array(picture)
    faint_count = int(faint.sum())
    reserved = min(FAINT_COLOURS, 255 // 4) if faint_count else 0
    words = np.zeros(256, dtype="<u2")
    indexes = np.zeros(rgb.shape[:2], dtype=np.uint8)
    solid_index, solid_palette = quantize(rgb[solid], 255 - reserved)
    indexes[solid] = solid_index + 1
    for i, colour in enumerate(solid_palette):
        words[i + 1] = word(colour, 0)
    if reserved:
        faint_index, faint_palette = quantize(rgb[faint], reserved)
        first = 255 - reserved + 1
        indexes[faint] = faint_index + first
        for i, colour in enumerate(faint_palette):
            words[first + i] = word(colour, 0x8000)
    height, width = indexes.shape
    return np.array([width, height], dtype="<u2").tobytes() + words.tobytes() + indexes.tobytes()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    source = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "shipped-art")
    os.makedirs(out, exist_ok=True)
    count = 0
    for name in sorted(os.listdir(source)):
        if name.lower().endswith(".png"):
            with open(os.path.join(out, name[:-4] + ".tex"), "wb") as handle:
                handle.write(enhance(Image.open(os.path.join(source, name)), int(name.split("_")[0]) not in NO_FAINT))
            count += 1
    print(count, "textures written to", out)
