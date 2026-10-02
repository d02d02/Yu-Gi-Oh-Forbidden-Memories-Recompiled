# WIP notes: feat/custom-card-art

Scratch status file for the current feature branch. Tracked and pushed so
work can resume in a fresh session, but **not meant to reach upstream** --
cherry-pick real code commits onto a clean PR branch and leave the
commit(s) touching this file behind.

Kept short on purpose: resolved items get rolled out of here once they're
committed (git log + the commit message + code comments are the history;
this file is only what's still in flight). Replace wholesale when a new
feature branch starts.

## Goal

Duel-Links-style full-bleed card presentation (hide frame/title/
description, enlarge art, reposition stats) behind `SET_CARD_LAYOUT`
(off by default), additive via `#ifdef MEMORIES_PC` -- retail's
byte-matched path untouched. Tip as of 2026-10-02: `44e4d0145` (origin).

Architecture, resolved findings, and the mechanism used throughout
(`DisplayObject_SubmitPacket`'s case-4/5 dispatch for projected quads) are
documented in `src/pc/cards/card_layout.c`/`.h` and `src/game/
func_80028B08.c`'s own comments, and in the commit messages for `93f5032dc`
/ `f781688e0` -- read those rather than expecting a duplicate here.

## Resolved 2026-10-02: art/backdrop alignment, both axes

The art (`CARD_LAYOUT_ART`, `card_layout.c`) used to be sized only against
win's own frame, with no relationship to the card-viewer's separate
backdrop object (`func_800283F4.c`'s `D_8009B240`, the description
TextBox's own panel -- created unconditionally, never gated by
`CARD_LAYOUT_DESCRIPTION`, so it's on screen in full-bleed mode too, just
empty). That caused two visible mismatches: a horizontal gap on the right
(old, since-disproven note below) and the art poking above the backdrop's
own top edge (user observation).

Root cause and fix are now documented in `card_layout.c` itself (the
comment above `CARD_LAYOUT_WIN_ORIGIN_X`): the backdrop's anchor sits at
an exact, source-derived offset from win's own origin
(`CARD_LAYOUT_BACKDROP_DX`/`DY`), and its own *visible* art starts some
bezel margin past that anchor (`CARD_LAYOUT_BACKDROP_INSET_X`/`_Y`),
measured live rather than guessed. Method: a headless run of the real
save state (`MEMORIES_LOAD_STATE=1` against `tmp/pc/game32dbg-user/states/
slot1.state`), a scripted Triangle press to open the viewer
(`MEMORIES_INPUT="40:1000,46:0000"`), and a native 320x240 frame dump
(`MEMORIES_DUMP_FRAME=200`, `MEMORIES_DUMP_PATH=...ppm`) read back pixel
by pixel. Found: horizontal was already exact (zero gap, `ART_W`
unchanged) -- the old "~15-20px" note came from `game/pixels.png`, which
turned out to be cropped before ever reaching the backdrop's edge, so
that number was never real. Vertical had a real 2px gap, now closed:
`ART_Y`/`ART_H` are derived from `BACKDROP_DY`/`INSET_Y` instead of the
old flat `0`. Verified live post-fix: art top and backdrop top both at
native y=26, exact match.

## Known, left alone on purpose: backdrop's own left edge isn't straight

Confirmed live (2026-10-02, same headless method as above, row-by-row
scan): the backdrop's own left edge sits at win-relative x=140 for its
full height *except* the bottom (biggest) of its three stacked
text-line rows, which is 2px wider on the left (x=138), stepping in
starting the exact row the art's own last pixel row ends. No frame ever
has both the art and that wider row drawn on the same row -- it's a seam
in the backdrop's own texture (retail's own, shared with Library/Build
Deck), not a pixel collision -- but scanning down the edge by eye it
reads as the panel cutting into the art's own corner, which is exactly
what prompted this investigation. Full derivation and the decision are in
`card_layout.c`'s comment above `CARD_LAYOUT_BACKDROP_DX`. **User's call
(2026-10-02): leave it, document it** -- not a bug this branch
introduced; retail's own layout never exposed it (description text
covered that row); the parked real-texture plan below is the right place
to actually mask it, if that's ever wanted.

## Next steps

1. Build a gold/olive backdrop bar for the icon/ATK-DEF row (Duel Links
   reference) -- stars/attribute/ATK/DEF still float with no backdrop.

## Parked: real textures for the plaque and row backdrop (2026-10-02)

User has captured PNGs for the ATK/DEF numbers plaque and (probably) the
icon/ATK-DEF row's own backdrop -- real art to replace `CardLayout_DrawPlaque`'s
flat parchment-beige `POLY_G4` fill, and to use for next-step 1 above (and
possibly to mask the edge seam noted above). Plan, worked out and
grounded in two existing precedents in this codebase
(`src/pc/cards/star_icons.c`,
`src/pc/text/glyphs.c` -- both already put a PNG with no disc counterpart
onto a real texture the duel's own pipeline samples):

1. **Packaging**: not a mod asset (this whole feature isn't a mod -- see
   below) -- embed like `src/pc/assets/ps1-controller.png` /
   `ps1_controller_png.h` (`tools/pc/embed_controls_art.py`'s pattern,
   generalized or copied): PNG image chunks only, stripped of incidental
   metadata, compiled in as a C byte array under `src/pc/assets/`. No
   runtime file dependency.
2. **Decode**: `src/pc/cards/art.c`'s existing `CardArt_IndexedImage(path,
   w, h, indices, clut, ...)` -- "any size... one byte a texel, entry 0
   clear" -- already built for exactly this (title screen's own
   port-authored PNGs); a better fit than the 16-colour icon decoder.
3. **Texture storage**: reserve a `SoftGpu_Bank` (`soft_gpu.h`). Allocated
   today: 1-12 the 3D Monsters mod, 14 star icons, 15 glyphs, 0 is real
   VRAM itself -- **13 is the one still free**. Decode-once-and-cache
   (`made` flag) + store-into-bank, following `star_icons.c`'s
   `make()`/`store()`/`Stars_IconCell()` trio as the template.
4. **Draw**: upgrade `CardLayout_DrawPlaque` (and a sibling for the row
   backdrop) from its current flat `POLY_G4` to a textured `POLY_GT4`,
   through the same case-5 `DisplayObject_SubmitPacket` dispatch
   `CardLayout_DrawArt` already uses (so it keeps rotating/projecting with
   the card during the reveal, which is why the plaque goes through that
   dispatch at all -- see its own comment), sourcing clut/tpage/UV from the
   new bank/cell instead of an existing retail `SpritePrim`.

Why not a mod: this modifies retail's own byte-matched draw routine
(`func_80028B08.c`) and object setup (`duel_effect_resource_setup.c`,
`func_800283F4.c`) directly -- outside the mod system's hook surface (code
mods hook specific named extension points, e.g. the title screen's
`MainMenu_*` functions, not arbitrary mid-render internals of a decompiled
retail function). Same category as Internal 2x/4x resolution: a
`Settings_Get(SET_CARD_LAYOUT)`-gated, `#ifdef MEMORIES_PC`-additive core
port feature, not a `mods/` directory.

## Workflow notes

- Build: `python tools/pc/build_game32.py --build tmp/pc/game32dbg`. Exe
  locks if still running -- ask the user to close it first.
- Test: `MEMORIES_USER_DIR=../game32dbg-user`, `MEMORIES_CARD_LAYOUT=1`,
  `MEMORIES_TRACE=card_layout MEMORIES_LOG=card_layout.log`.
- **Headless pixel-measurement repro** (no window needed; add
  `MEMORIES_INTERNAL_SCALE=4 MEMORIES_DUMP_PICTURE=1` for a true 4x dump
  matching what the player sees -- without `MEMORIES_DUMP_PICTURE`,
  `Memories_DumpFrame` ignores the internal scale and dumps the raw
  native 320x240 buffer regardless, which is fine for exact-pixel
  measuring but not what a human should eyeball): from
  `tmp/pc/game32dbg/`, `MEMORIES_USER_DIR=../game32dbg-user
  MEMORIES_HEADLESS=1 MEMORIES_CARD_LAYOUT=1 MEMORIES_LOAD_STATE=1
  MEMORIES_INPUT="40:1000,46:0000" MEMORIES_DUMP_FRAME=200
  MEMORIES_DUMP_PATH=<path>.ppm ./memories-pc.exe` -- loads
  `states/slot1.state` (a duel with a card viewable, user-provided,
  2026-10-02), scripts a Triangle press (pad bit 0x1000) to open the card
  viewer, and dumps a frame once it's settled. Re-run after any
  `card_layout.c` change touching the art rect to verify against real
  pixels instead of re-guessing.
- Reference images used so far: `maxresdefault.png` (repo root, untracked)
  and `game/pixels.png` (untracked/ignored) -- both local-only, not in git.
