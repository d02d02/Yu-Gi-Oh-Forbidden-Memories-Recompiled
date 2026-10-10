# HD overhaul of the static assets (branch feat/hd-overhaul, based on upstream/master)

Goal: run every static image the Forbidden Memories HD mod does not cover yet (main menu, boot UI, Library, Password,
Options, effects, story pictures) through the HD mod's own method, to be offered upstream as more parts of that mod.
The HD mod (release `yfm-redecomp-hd-mod-v0.2.1-preview.1`, identical image for image to a local install, checked by hash)
holds card art, thumbnails, frames, Build Deck, duel, 65 portraits (1983 entries, all WA_MRG.MRG). Everything else is open.
Images are made from the game's own: never commit them (they live under `tmp/`, git-ignored).

## Tools added (all under tools/pc/)

| Tool | What it does | State |
|---|---|---|
| `extract_disc_data.py` | DATA/*.MRG out of the retail .bin, for the tools that take `--data` | works |
| `hd_auto_pack.py` | every extracted sheet/scene (manifest of `extract_images.py`) through hd_screen_pack's scalers, no recipe: xBR for <=24 colors (one whole-image run), Real-ESRGAN x4plus 60% + Lanczos + back-projection otherwise; story-picture columns joined; `--exclude` skips what another mod holds; `--cuts assets.txt` redoes the pieces the game cuts out alone | works; ~7 Kpx/s |
| `sprite_bank.py` | decodes a screen's one-sector sprite bank (frames and parts with dx, dy, cell, size) | works on the main menu (SU.MRG sector 114) |
| `hd_sprite_pack.py` | composes each frame from its parts (the FIRST part is on top), enlarges the canvas once, writes each part's area back (average over frames sharing a piece); `--labels` redraws grey button labels in a font | assembly works; label redraw UNFINISHED |
| `hd_shot.py` | headless A/B picture of a screen with/without a pack at Internal 4x (yfm_control.Game) | works, ~25 s |
| `hd_recipes/menu_labels.json` | frame offset -> word for the menu's grey labels | |

## Lessons

- **Sheets are not pictures.** The game draws a button from several pieces cut from one sheet (a frame piece plus opaque
  label patches, a word split over three patches: "2P DU"+"E"+"L"). Enlarging the sheet whole, or each cut alone
  (`--cuts`), leaves seams where pieces meet on screen. What fixes it: compose the frame as the game does
  (`DisplayObject_RenderSpriteSheet`: parts at (dx, dy), first part on top; 8-bit part `u` is 0-255 over two 128-px
  columns, the cell's page bits pick the pair), enlarge the composite once, cut it back. Proven on the menu (A/B in
  notes below): continuous grain, labels intact.
- A part is matched to its sheet by the rectangles a texture dump saw (`upscale_pack.read_cuts`); only 7 of the menu
  bank's frames resolved that way (the rest need palette/page resolution from the objects' creation code).
- **Redrawing labels in a font is much crisper than any enlargement** (offline A/B on LOAD) but fiddly: the word has to fit
  inside the label PATCH (the pack can only replace texels of the sheet; a letter that overhangs the patch is cut), the
  shared frame piece must not take a label's letters (it is averaged over four buttons: it smeared them), and the letter
  box must come from row/column profiles of a local top-hat mask, not percentiles (speckle inflated the height, the font
  came out too big, the words too wide). The last edit of this (profile-based box) is untested.
- The engine's HD text (hd_text.c) only covers font cells and a few hashed sprite labels in the duel; sprite labels like
  NEW GAME are pictures, so a pack must redraw them (hd_screen_pack `labels` recipe style, or the above).
- Speed: xBR per small region launched ffmpeg twice each (29 images in 22 min); one whole-image run fixed it.
- Scale before you commit hours: run a 20-image slice, look at it in the game, then widen.

## Testing recipe (headless, deterministic, ~25 s)

`python tools/pc/hd_shot.py --pack <mod folder> --screen title --press start,start --out tmp/pc/shots/x`
-> `x-off.png`, `x-on.png`, `x-both.png` (1280x960). Traps: the control channel's `shot` is 320x240 unless
`MEMORIES_DUMP_PICTURE=1` (hd_shot sets it) and `settings={"internal_scale": 4}`; `MEMORIES_WINDOW_SHOT`/`DUMP_FRAME`
paths gave white or 1x pictures; the title needs ~300 steps, then Start twice, for the menu; `mods_dir` isolates the
user's own mods. Texture dump for cuts: headless run with `MEMORIES_DUMP_TEXTURES=<dir>` (assets.txt).

## Toolchain (Windows)

No ffmpeg: `pip install imageio-ffmpeg`, copy its exe to `tmp/pc/tools/ffmpeg/ffmpeg.exe`, put the folder on PATH.
`tmp/pc/tools` (realesrgan) and `win32-deps` are junctions to the dev worktree's. `scipy` is needed by the label redraw.
Spaces in a path or in a JSON argument break PowerShell quoting: pass files.

## Next steps

1. Finish the menu: test the profile-based letter box (`hd_sprite_pack.py`, `redraw_label`), then A/B in the game;
   then the active (green neon) labels and the frames that did not resolve.
2. Decide per screen group which tier it gets: automatic (`hd_auto_pack`), assembled (`hd_sprite_pack`), redrawn labels.
   Story pictures and effects have no assembly problem: run them in slices (`--only scenes/m0`).
3. Make the bank decoding find frames from the stream grammar instead of scanning u16s, and resolve palettes/pages.
4. Package: extend `hd_assets_pack.py --merge` (or a sibling mod) so the maintainer builds these parts; PR carries tools only.
