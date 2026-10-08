# PR text: ATK/DFD digits from a font (working-branch file, not for the PR itself)

Paste into the PR description.

## The anime frame's ATK/DFD digits

With the anime frame on, the two stat numbers are drawn from a mod's own digit
strip, sized to the stat boxes and centred on them (one to four digits; a
stat past 9999, a mod's cap, is squeezed to the width of four). Without a strip
the retail digits are drawn, as before.

### Is the font compiled?

No, and it is not needed to build either. The engine never reads a font. The
digits are one picture, `tools/pc/hd_recipes/anime_digits.png` (ten digits,
256x210), drawn once from the card game's ATK/DFD font by
`tools/pc/card_digits.py` and committed like the frame PNGs. `hd_assets_pack.py`
copies it into the mod (`textures/anime_digits.png`) and writes the manifest's
`card_layout.digits`. The engine loads it through the same path as the frame
(`card_layout_art.c`), and `func_80028B08.c` draws each digit as one quad at
the size in `digits` (`width`, `height`, `step`).

### What the maintainer does to ship it

1. Merge: the engine change is compiled into `memories-pc.exe` and ships with
   the next regular engine release; nothing extra.
2. Rebuild the HD mod zip with the usual `hd_assets_pack.py` command (in
   `notes/image-remaster.md`): the digits and frames are picked up, no new flag.
   To change the look, `--digit-font <file.ttf>` draws a new picture
   (`--digit-stretch` for the width), or replace `anime_digits.png`.
3. Upload the new zip, as for any HD mod rebuild.

Licence: the repository holds the digits as a picture, not the font. Whether
that picture may be redistributed is the font's licence, to check.

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
