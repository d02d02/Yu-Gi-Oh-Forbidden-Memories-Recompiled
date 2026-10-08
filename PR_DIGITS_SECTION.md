# PR text: ATK/DFD digits from a font (working-branch file, not for the PR itself)

Paste into the PR description.

## The anime frame's ATK/DFD digits

With the anime frame on, the two stat numbers are drawn from a mod's own digit
strip, sized to the stat boxes and centred on them (one to four digits; a
stat past 9999, a mod's cap, is squeezed to the width of four). Without a strip
the retail digits are drawn, as before.

### Is the font compiled?

Not by the game. The engine never reads a font file. The digits are drawn
**once, when the HD mod is built**, by `tools/pc/card_digits.py` (called from
`hd_assets_pack.py --digit-font <file.ttf>`), into one 256x210 PNG
(`textures/anime_digits.png`: ten digits, 64x70 texels each, one texture page).
That PNG ships inside the mod zip like the frame art. The engine loads it
through the same path as the frame (`card_layout_art.c`), and
`func_80028B08.c` draws each digit as one quad at the size in the manifest's
`card_layout.digits` (`width`, `height`, `step`).

### What the maintainer does to ship it

1. Merge: the engine change is compiled into `memories-pc.exe` and ships with
   the next regular engine release; nothing extra.
2. Rebuild the HD mod zip with the font: the usual `hd_assets_pack.py`
   command plus `--digit-font <path to the .ttf>` (the full command is in
   `notes/image-remaster.md`, "Building the Forbidden Memories HD mod")
   The font used for the shipped look is Yu-Gi-Oh! Matrix Regular Small Caps
   (the second of the two files), stretched 1.4x wide; digits are centred on
   the stat boxes. (`--digit-stretch` changes how wide the digits are drawn; default 1.4).
   The `.ttf` is read from the maintainer's machine and is never committed.
   Without `--digit-font` the build is as before and the digits stay retail's.
3. Upload the new zip, as for any HD mod rebuild.

Licence: the pack contains the digits as pictures, not the font. Whether
those pictures may be redistributed is the font's licence, to check before
shipping.

### What the player does

Nothing new: update the engine, install or update the Forbidden Memories HD
mod, and turn on **Anime card frame** in the Mods window. No font is needed on
their machine. With the option off, or an older HD mod without the strip,
the card view is unchanged.

### Limits

- One colour: a raised or lowered stat keeps retail's tinted digits.
- The strip has one transparent index, no partial alpha: the soft edges are
  blended into the stat box's colour.
- Not run in the game from this environment (no disc data): checked by the
  card layout tests, a compile of the changed files and renders of the strip.
