# WIP notes — feat/anime-standalone-v030 (worktree `...\Yu-Gi-Oh-Forbidden-Memories-Recompiled-anime`)

**Goal:** a brand-new anime card-frame mod, started from the v0.3.0 tag (`663626b1d`), fully **independent of the Forbidden Memories HD
(assets-hd) mod** — its own `mods/<id>/` with its own `mod.json`, `full_bleed` setting, `card_layout` and textures. No engine change needed.
Started 2026-10-12. Nothing built yet.

## Why standalone is possible (v0.3.0 already has the engine side)
- `feat/anime-frame-standalone` (`fd0abd82c`) is an ancestor of v0.3.0: `card_layout`, frame styles/rules, ATK/DEF digits are in the engine.
- A layout mod is pure data (`notes/modding.md` "Frame styles and the rules that pick them", ~line 1000-1110): `full_bleed` bool setting,
  `card_layout` {frame_styles, frame_for, default_style, art, atk, def, stars, attribute, digits, spell}, textures. Old standalone attempt for
  reference: `git show feat/anime-card-frame-mod:mods/anime-card-frame/mod.json` (old form, pre frame_styles).
- Working reference of the current form: HD pack v0.3.0 `mods/assets-hd/mod.json` `card_layout` block (frame_styles gold/green/pink/orange,
  frame_for rules, art 3,3 134x139, atk 38,179, def 102,179, stars 59,153, attribute 114,149, digits 10x12 step 10).

## Traps (learned the hard way, see shared notes `anime-frame-4x-bug.md`)
1. **Only ONE mod's `card_layout` is read** (last applied wins, not merged). With HD also installed, test with HD's `full_bleed` OFF or HD absent.
2. **Frame PNGs must be power-of-two sizes** (e.g. 1024x2048, 1024x1024; digits 256x256) until the engine fix lands upstream: v0.3.0's
   `bank_halve` (texture_pack.c) builds an incomplete mip chain for non-power-of-two PNGs -> frame invisible at Internal 2x/4x (fine at 1x).
   Engine fix: branch `debug/v0.3.0-frame` commit `490bb49ef` (fork d02d02). Test on the official v0.3.0 exe.
3. **Frame art: light vs dark.** Light = original art (git `ff79f7dd0`, pre-boost). Dark = contrast-boosted (git `4654ebb9b`), made for the old
   177x254 texture, obsolete since the 3x3 tile grid (531x762) and the direct-PNG path. Light POT frames: `...\hacking\yfm-v0.3.0-lightlab\variants\light\`
   (also mid, dark). Light pack release `hd-pack-v0.3.0-original-frame` is UNTESTED in game.
4. The frame texture is stretched into a 3x3 tile grid (`card_layout_art.c`: 177x254 tiles, 531x762); the PNG is cropped in proportion, so
   a non-uniform stretch to power-of-two sizes is harmless. `notes/modding.md` still says single 177x254 / 27x downsample (outdated).

## Next steps
1. Scaffold `mods/anime-card-frame/` (new id, e.g. `anime-card-frame`): `mod.json` (setting `full_bleed`, default off or on, `card_layout` copied from
   the HD one), `textures/` (power-of-two frames + digits). Settings key will be `mod.<id>.full_bleed`.
2. Build/run: `python tools\pc\build.py --target windows` (toolchain already junctioned from the main checkout's `tmp\pc\tools`, `win32-deps`),
   or use the official v0.3.0 release folder and drop `mods\<id>` in. Test recipe: `C:\YFM-original-test\...\run.bat` pattern (clean profile via
   `MEMORIES_USER_DIR`, `MEMORIES_DEBUG_DECK=374,380,332,683,364,670`), Free Duel, TRIANGLE on a card, 4x and 1x screenshots.
3. Decide the frame art (light/mid/dark) from in-game screenshots; keep any generation script **in the repo** (the old contrast script was never committed).
4. Later: upstream the `bank_halve` fix as a small PR; update `notes/modding.md` for the 531x762 grid.

## Pointers
Shared notes: `C:\Users\mdahh\.claude\shared\yfm-notes\anime-frame-4x-bug.md` (+ `INDEX.md`). Old anime branches (history only):
`feat/assets-hd-anime-frame`, `feat/anime-frame-styles-and-digits`, `anime-style-mod` (stale, upstream issue #296 era, nothing built).
