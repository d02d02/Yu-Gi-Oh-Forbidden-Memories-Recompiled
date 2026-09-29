# Progress

What is current: decisions, state, what's left. Tracked, so it travels between the
Windows and Linux machines (see "Switching machines"). Finished and superseded work,
with the full investigation write-ups, is in **`history.md`**; each section here
points there where it has more. Research files live in `tmp/pc/todo-research/` (not
committed). Update in place as work continues instead of re-deriving it next session.

## Start of every session: sync first (Windows or Linux)

The user works on two machines (Windows, native Linux) through the fork
(`origin` = `d02d02/...`), and upstream (`upstream` = `Unchiga/...`) moves daily.
**At the start of every session, before any work, Claude checks and *asks*;
nothing is pulled, reset or rebased without the user's yes:**

1. `git status` — uncommitted work here? Say so first; never overwrite it.
2. `git fetch origin` and `git fetch upstream` (read-only, safe to just do).
3. Report, per working branch (`feat/precise-geometry`, `feat/test-scenes`,
   ...): behind/ahead of `origin/<branch>` (the other machine pushed?), and how
   many commits `upstream/master` has that the branch lacks.
4. **Ask** before each change:
   - behind `origin` only → fast-forward (`git merge --ff-only origin/<branch>`);
   - `origin` was force-pushed (a rebase from the other machine: local and
     `origin` both "ahead") → `git reset --hard origin/<branch>`, only if
     nothing local is unpushed;
   - upstream moved → rebase the branches onto `upstream/master`, rebuild,
     rerun `tools/pc/scene_measure.py state` + `controls`, force-push with
     `--force-with-lease`, fast-forward the fork's `master`.
5. After any rebuild: a save state from the old build may not load (or crash
   on the title jump, item 6); `scene_measure.py state` must be redone.

**Before preparing any PR:** fetch upstream and `git log upstream/master --
<files touched>` — on 2026-09-28 a 3D Monsters fix we made was already
upstream the same day.

`play.bat` / `play.sh` rebuild the checked-out branch on every launch, so the
user's play build follows whatever branch is checked out.

## Switching machines

Everything needed to resume is committed and pushed to `origin` (the fork), except
the disc image (`game/*.bin`, gitignored; supply it locally): this file,
`history.md`, `notes/*.md`, and a copy of the real memory card
(`memcards/slot01.sav`, `memcards/README.md`: not a save state, see that README).
Working branch: **`feat/test-scenes`** (precise geometry work, the test scenes mod,
the measuring tools); the PR branch is `feat/precise-geometry-menu`. On the other
machine, after the sync check above: `git checkout feat/test-scenes` and, if the
branch was rebased, `git reset --hard origin/feat/test-scenes` (only with nothing
unpushed there).

## How to test things

- My debug build: `tmp/pc/game32dbg`, with its own user folder `tmp/pc/game32dbg-user`
  (saves, states and settings kept apart from the real game).
- Run it (PowerShell, repo root):
  `$env:MEMORIES_USER_DIR = "tmp\pc\game32dbg-user"; tmp\pc\game32dbg\memories-pc.exe`
  (add `$env:MEMORIES_LOAD_STATE = "N"` to start from state slot N).
- Reach a screen with no save needed: the options smoke input plus `MEMORIES_MODE_AT=1000:<mode>`
  (modes in `src/game/main_modes.h`: 4 Library, 7 Build Deck, 9 Name entry, 10 Password, ...):
  `MEMORIES_INPUT="910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,1040:0040,1046:0000,1060:0040,1066:0000,1100:4000,1106:0000" MEMORIES_MODE_AT=1000:9`
- Dump a frame: `MEMORIES_DUMP_FRAME=1500 MEMORIES_DUMP_PICTURE=1 MEMORIES_DUMP_PATH=out.ppm`
  (add `MEMORIES_DUMP_VRAM=1` for VRAM; it drops bit 15 of each word).
  **Needs a real window to show anything GL-only (PGXP, HD text): with `MEMORIES_HEADLESS=1`,
  `Platform_Open` never creates a GL context at all, so the dump is the software GPU's picture
  and is byte-identical regardless of any GL-only setting.** Drop `MEMORIES_HEADLESS` (a real,
  visible window pops up) or add `MEMORIES_DETERMINISTIC=1` alongside it (same fast
  frame-stepping as headless, but a real window/GL context still gets created) to actually
  see a GL-pass effect in a dump. `MEMORIES_DUMP_FRAME`'s frame count is *this run's own*,
  starting from 0 at boot — after `MEMORIES_LOAD_STATE`, it does **not** jump to the frame
  number the state was originally saved at; the state resumes around frame 30 and the count
  keeps going from there.
- PPM to PNG, or a zoomed crop: `python tmp/pc/hd-text-split/crop.py in.ppm out.png [x y w h zoom]`.
- **`MEMORIES_INPUT`'s hex bits are the raw PSX controller (SIO) layout, *not*
  `src/game/input.h`'s `PAD_BUTTON_*` enum** — those are two different encodings in this
  codebase and it's easy to grab the wrong one (cost real time this session):
  `0001` Select, `0002` L3, `0004` R3, `0008` **Start**, `0010` Up, `0020` Right, `0040` Down,
  `0080` Left, `0100` L2, `0200` R2, `0400` L1, `0800` R1, `1000` Triangle, `2000` Circle,
  `4000` **Cross**, `8000` Square. Confirmed against `mods/hand-camera`'s own hard-coded
  defaults (`turn_right`=R1=`0x0800`, `turn_left`=L1=`0x0400`, `zoom_in`=L3=`0x0002`,
  `zoom_out`=R3=`0x0004`). A known-good deterministic path from cold boot into a real
  campaign duel with a 3D-Monsters model on the field: replay
  `tests/pc/smoke/duel-3d-monsters.json`'s own `input` field verbatim (reaches frame 6760,
  a card-placement reticle screen) with `mod.3d-monsters`/`mod.hand-camera` on; from there,
  `<frame>:4000,<frame+6>:0000` (Cross) places the highlighted card face-up in its default
  (Attack) position, `<frame>:0008,<frame+6>:0000` (Start) ends the turn.
- The same path with **2D Monsters** instead (item 8 below): replay
  `tests/pc/smoke/duel-2d-monsters.json`'s own `input` field verbatim (same
  recording, same frame 6760) with `mod.2d-monsters` on and `mod.3d-monsters`
  **off** — they conflict, same software-GPU texture-bank range.
- **A save state made by the user's real `game32` build will not load in the debug
  `game32dbg` build**, even when both report the identical `buildid` — cross-build state
  loading fails outright (`state load failed`, likely the mods' own compiled checksums
  differing between a release and a debug build). Don't try to copy the user's states over.
  Instead, **build a state from inside `game32dbg` itself**: script the input above (or drive
  it live, windowed, no `MEMORIES_DUMP_FRAME`/`MEMORIES_HEADLESS`, and press F5 by hand) with
  `MEMORIES_SAVE_STATE="<frame>:<path>"`, then reload that state as many times as needed with
  `MEMORIES_LOAD_STATE=<same path or slot>` — each reload only needs ~60 frames to resume and
  is fast, so do the slow scripted/live part once, then iterate cheaply from the saved state.
- `MEMORIES_MOD_3D_MONSTERS_TEST=<card id>` (undeclared, not in the Mods window) fills *every*
  field zone with a different monster at once (`id + zone*2 + side`), bypassing the
  face-up/occupied check entirely — good for a forced-visible stress test, bad for realism:
  with only `CACHE 8` model slots in `mods/3d-monsters/field_models.c` but up to 10 zones
  requested, it thrashes reloading models every frame and runs very slowly. Fine for a single
  frame dump; don't run it live/windowed for long, and don't read anything into the slowdown
  itself — it's a separate, pre-existing, unrelated limitation of this test tool, not of
  whatever is actually being tested.
- **The repo lives on OneDrive and both machines' checkouts, plus a Claude Code (WSL) session,
  can all resolve to the *same physical files* — not just the same commits.** The user's Windows
  checkout at `C:\Users\mdahh\OneDrive\...\Yu-Gi-Oh-Forbidden-Memories-Recompiled` and a WSL
  session's `/mnt/c/Users/mdahh/OneDrive/...` are one and the same directory on disk. Both
  `play.bat` and `tools/pc/build_game32.py`'s default `--build` resolve to `tmp/pc/game32` on
  either OS, so a Linux-side build (gcc, ELF objects) and a Windows-side build (clang/MSVC, PE/COFF
  objects) share one `obj/` cache and stomp each other's object files — surfaces as link errors
  (`undefined reference`, a relocation against a COFF-style underscore-prefixed symbol) or the
  other direction (`the string table does not end the file` when Windows tries to parse a leftover
  ELF `.o`). **Fix when hit:** delete the stale object(s), or the whole `tmp/pc/game32/obj`
  (or, to be sure, all of `tmp/pc/game32`), then rebuild on the OS you're actually testing on.
  **To avoid causing it:** when testing from a WSL/Linux session on a checkout the user also
  builds on Windows, build into a directory the Windows side never touches, e.g.
  `python3 tools/pc/build_game32.py --build tmp/pc/game32-wsl`, instead of the shared default.

---

## Status board (2026-09-29)

| # | Item | Status | Branch | Next step |
|---|---|---|---|---|
| **P** | **Precise geometry, level 1 (Textures)** | Three fixes done and measured, cross-OS confirmed on Linux; PR branch pushed to the fork, **PR not opened** | `feat/precise-geometry-menu` (PR), `feat/test-scenes` (work + tools) | User's visual check; then open the PR |
| P2 | Precise geometry, level 2 (positions) | Designed (`draw_id`), an early version was built and tested on since-deleted branches | — | After the PR: see "Level 2" below |
| 1 | Name entry: slots guard | Main work merged upstream (#110); follow-up left | — | Identify the cells by checksum, not position |
| 2 | Duel results letters HD | Not started, plan ready | — | Extend the digit `Sheet` to the alphabet |
| 3 | Lettering follow-ups (PR #107 review) | Not started, latent | — | Word-width clamp; sibling redraw |
| 4 | Tests for HD text | Not started | — | One smoke case, name entry at 4x |
| 5b | Trade: browse cards Up/Down | Done, branch pushed, **no PR open** (checked 2026-09-29), needs a live test | `feat/card-viewer-browse-trade` | Live session with an owned deck, when it is a priority |
| 5c | Library: browse cards Up/Down | Not started, assessed (big) | — | Start with "replay retail steps" |
| 6 | Crash: title jump after a cross-build state load | Cause likely found | — | Verify `state_remap.c` remaps `D_800E9DC0` |
| 7c | HD model textures (`MODEL.MRG`) | Blocked: tags lost before the pack lookup | — | Trace `model_texture_transfer.c` / `model_apply_texture_tint.c` |
| 7d | Duel field tile: bright diagonal sliver | Not started, confirmed not PGXP | — | See 7d below |
| 8 | 2D Monsters mod (flat card-art cutout, alt. to 3D Monsters) | Fixed and **confirmed live** (three bugs; `history.md`) | `feat/2d-monsters-mod` (clean, off `origin/master`), here (for testing) | Record smoke `sha256`, cherry-pick fix to `feat/2d-monsters-mod` |
| — | Game > Restart | Parked | — | — |
| — | Test scenes: boot straight into the duel | Parked (later) | `feat/test-scenes` | See "Parked" below |

---

## P. Precise geometry (PGXP)

**Goal.** Get level 1 (perspective-correct textures) accepted upstream with evidence
Unchiga can check, then level 2 (exact positions, no wobble), measured the same way.
The user's wider aim is HD model textures and higher-poly models (7c); HD textures
make level 1 matter more, since warping shows more on detailed art.

**Background.** Upstream history: #49 `pgxp`, #67 `pgxp-textures`, #71 `pgxp-native`
(MaChInEgUn3, merged); #83 `fix/disable-precise-geometry` (Unchiga: level 2 opened
gaps in small monsters, disabled everything); **#139** (ours, level 1 option, closed
by Unchiga: *"visible distortion when you enable it"*; his video shows it on the
**edge of the duel field**, on Nvidia RTX 4090 + XWayland). Our Intel machines
(Windows, Linux) never showed distortion by eye. Full story: `history.md`.

### The PR: `feat/precise-geometry-menu` (pushed to the fork, not opened)

Off `upstream/master` `6ad201fbf`, code only (no `progress.md`, `memcards/`, tools,
test scenes or measure code; keep it that way: cherry-pick, never PR a working
branch). Four commits:

1. **Video: re-enable precise geometry (Textures).** Video > Precise geometry,
   Off / Textures; `SET_PGXP` max 1 (level 2 not offered); greyed below 2x or
   without OpenGL 3. Default Off.
2. **PGXP: widen rtp's window by the truncation it allows** (`gte.c`). Up close the
   GTE's truncated IR1/IR2 and SZ3 move the word up to ~3.6 px from the true
   position, so rtp dropped precise positions; the window now widens by
   `(H + distance from the centre) / SZ3`. Near camera: 2437 rejected → 0, mixed
   927 → 4. Duel distance unchanged.
3. **PGXP: GsSortPoly hands on the precise vertices it copies** (`libgs.c`, `pgxp.c`).
   The 3D duel cards (`func_80015EF4`) go through LIBGS `GsSortPoly`, which never
   tagged them: found only by value, one corner per card collided with another
   vertex on the same pixel. `Pgxp_AddPrimMoved`. Mixed 24 → 0 (duel distance),
   18 → 0 (turned 90°, field edge in view), 4 → 0 (near).
4. **PGXP: keep a full duel field at full speed** (`pgxp.c`, `libgpu.c`). The
   lookup tables (32768 slots) held ~32000 live entries with 10 monsters and every
   miss walked all probes: 30 fps. Per-frame tables (this frame's and the last's,
   65536 slots, a slot empty unless stamped with its frame), and `DrawOTag` skips
   words outside ±2048. Found by the user live.

With Off, the picture is upstream's: every change is behind `Pgxp_Active`; the six
smoke screenshots are byte-identical. Tests: `tests/pc/pgxp_test.c` (window case
fails on the old code; `GsSortPoly` copy). CTests not run on Windows (no CMake
configure here); CI runs them.

**Description:** drafted, to be rediscussed with the user (structure each fix as
observed problem → fix → observed result, and mark what was seen by eye vs only
measured). Naming: Unchiga's style, `Area: what the player sees`; avoid used names
(`pgxp`, `pgxp-textures`, `pgxp-native`, `fix/disable-precise-geometry`,
`feat/pgxp-video-option`). Ask Unchiga to retry at Textures and, if it still shows,
send Off vs Textures of the same frame and his internal resolution.

**Upstream branches that may conflict** (checked 2026-09-29, none merged, none
touch the PGXP code): `feat/copy-system-info`, `hd-options-dimmed`,
`debug-title-jump`, `windows-mods-3d` (menu.c, settings.c, libgpu.c); many touch
`notes/pc-build.md`.

### Measuring: `tools/pc/scene_measure.py` (on `feat/test-scenes`)

The **Test scenes mod** (`mods/test-scenes/`): hold **L1 + Cross on Option** on the
title menu → a duel with Simon Muran, the ten monster zones filled from
`field.json` (player 1-5, opponent 6-10), face up. Hand: the player's cards 1-5,
cursor on Blue-Eyes. Design and research: `history.md`.

```
python tools/pc/scene_measure.py state      # boot → scene → save state (redo after every rebuild)
python tools/pc/scene_measure.py controls   # must print "controls: pass"
python tools/pc/scene_measure.py compare [--scales 2,4]          # Off vs Textures image diff
python tools/pc/scene_measure.py trace [--camera turn:<deg>|near|near-half] [--scales 2]
python tools/pc/scene_measure.py bench --pgxp 0,1 --scale 4 --speed -1 --repeat 5 --build <label>
```

- **trace** (needs the fork-only `MEMORIES_PGXP_MEASURE` code): per textured
  triangle, the texel shift level 1 makes (M1), mixed triangles (M2), each vertex's
  offset from its console pixel (M4), why projections lost their precise position
  (`rejects.csv`), why frame words got none (`misses.csv`), and an overlay PNG.
- **bench**: the benchmark turn from the state (checked with the user): Cross picks
  Blue-Eyes, Right turns it face up, Cross, Right to the second zone, Cross, Cross
  takes Sun, Start as soon as the field phase takes input (540), the opponent's
  whole turn, end at 2520 as the player's turn returns. Game and draw ms per frame,
  fps, wall time, and a hash of the state saved at the end; rows to `bench.csv`.
- **Gotchas:** internal resolution is `MEMORIES_INTERNAL_SCALE` (not
  `MEMORIES_SCALE`, the window). Deterministic only uncapped: the tool sets
  `MEMORIES_SPEED=-1` (at 100, Textures runs drifted by a VBlank). **Time only on
  mains power, with `--out` outside OneDrive** (it syncs the 7.5 MB states; on
  battery the numbers were twice as noisy). End states always differ in the sound
  regions (the sound driver's RAM near `0x801E1650` and the SPU's voices; the mixer
  is real-time, `MEMORIES_NO_AUDIO` does not stop it): compare outside those.

### Results so far (Windows, Intel Iris Xe, 4x unless said)

**Level 1 is visible on the floor, not on the monsters.** Off vs Textures, default
camera, 2x: 8.06% of pixels change, almost all the field floor and its edges; the
largest texel shifts are the big near floor triangles (up to 4.6 px at 2x, 15-25 px
close up). Monsters: median shift ~0.01 px. No monster seam breaks seen at any
camera, before or after the fixes.

**Mixed triangles (some corners corrected, others not):**

| Camera (2x) | Before the fixes | After |
|---|---|---|
| Duel distance | 24 | 0 |
| Turned 90° (field edge in view) | 18 | 0 |
| Close up (Hand camera, 300) | 927 | 0 |

**Cost** (benchmark turn, uncapped, 5 alternating runs, medians, game / draw ms per frame):

| Build | Off | Textures | Extra |
|---|---|---|---|
| Before the speed fix | 2.59 / 1.04 | 5.40 / 1.29 | +2.81 / +0.25 |
| With all fixes | 2.68 / 1.09 | 3.35 / 1.26 | **+0.67 / +0.17** |
| Without fixes 2-3 (A/B) | 2.62 / 1.05 | 3.24 / 1.24 | +0.62 / +0.19 |

The mixed-triangle fixes cost ~0.05 ms; the rest is precise geometry itself. At real
speed both settings hold 60 fps (user's live session with a full field too).

**Confirmed on Linux, 2026-09-29** (native X11, Mesa, same laptop/GPU as the Windows
numbers above, mains power, `feat/test-scenes` at `aa6653172`): Off 3.17 / 1.31,
Textures 3.83 / 1.49, extra **+0.66 / +0.18** — matches Windows' +0.67 / +0.17 almost
exactly. Baseline is higher on Linux (driver/CPU overhead, not precise geometry); the
*added* cost of the setting is what was being checked, and it holds across OS and
driver. At real speed (capped, `--speed 100`): both settings 59.94 fps avg, matching
Windows. `bench_linux_pgxp1_4x_uncapped_r0.png` checked: expected end-of-turn scene
(two Blue-Eyes among the ten monsters). Raw rows: `tmp/pc/measure/bench.csv`.

**Where the +0.8 ms goes** (sampling profiler, 3 runs each, shares of the extra):
`rtp`'s precise math 18% (0.14 ms), every projection into the by-value table
`Pgxp_Project` 16% (0.13), `Pgxp_StoreAt`/`AddPrim` 25% (0.20), `Pgxp_FindAt`/
`DrawOTag` 9% (0.07), OpenGL `polygon` (binary search per vertex, perspective
setup) 19% (0.15), indirect (cache pressure, likely) 13% (0.11).

**Behaviour: precise geometry changes nothing in the game.** End states of the
benchmark turn, 10 runs per build (both settings): 0 bytes differ outside the sound
regions.

### Open question: Unchiga's distortion

Not reproduced. The best match found is fix 3 (half-corrected 3D cards, the part of
the field his video shows), but on Intel it was not visible by eye. Nothing we tested
has his two variables: the Nvidia driver and XWayland.

| Component | Unchiga | Ours (Linux) | Ours (Windows) |
|---|---|---|---|
| GPU | Nvidia RTX 4090 (discrete) | Intel Iris Xe (integrated) | Intel Iris Xe (integrated) |
| Driver | Nvidia proprietary 610.57.04, OpenGL 4.6.0 | Mesa 26.1.6 | Intel 32.0.101.7088, OpenGL 4.6.0 |
| Game's log line (`MEMORIES_TRACE=window`) | — | `OpenGL renderer Mesa Intel(R) Iris(R) Xe Graphics (RPL-U), version 4.6 (Compatibility Profile) Mesa 26.1.6-1, video x11` | — |
| Display | KDE Plasma on Wayland, game through XWayland | XFCE on native X11 | Windows (no X11) |
| SDL video driver | x11 | x11 | windows |

Our machines in full:

| Component | Windows | Linux |
|---|---|---|
| OS | Windows 11 Pro 24H2, build 10.0.26100 | Kali GNU/Linux Rolling, kernel 6.12.25-amd64, X11 XFCE |
| CPU | 13th Gen Intel Core i5-1345U | same laptop (dual boot) |
| GPU / driver | Intel Iris Xe, OpenGL 4.6.0 Build 32.0.101.7088 | Intel Iris Xe (Raptor Lake-P), Mesa 26.1.6 (amd64 + i386) |
| SDL | 3.4.16 | 3.4.16 (built into `tmp/pc/sdl-m32-portable`) |
| Compiler | clang 23.1.2, `i686-w64-mingw32` (llvm-mingw 20260922, ucrt) | clang 19.1.7 / gcc 14.2.0; links against Debian 11's i386 sysroot |

Linux setup: the 32-bit build needs `dpkg --add-architecture i386` and
`libgl1:i386 libgl1-mesa-dri:i386 libpulse0:i386`. The memory card goes to
`~/.local/share/YFM Re-Decomp/saves/slot01.sav`.

### Level 2 (after the PR)

- **Seams without gluing:** `snap_seams` (`libgpu.c`) pairs vertices only by their
  rounded screen word, so on small models unrelated vertices get snapped (the #83
  gaps). Design: a `draw_id` per `GsSortUnit` call, threaded through `PgxpVertex`
  and the tables; `snap_seams` only pairs vertices of the same draw. Built and
  tested once on since-deleted branches (no gaps with ten small monsters); redo it
  on the current code. **`PGXP_VERTEX_WORDS`:** `gl_picture.c` records and replays
  `PgxpVertex` as a word count; growing the struct without updating both caused
  the arena corruption found then. Full design, the bug hunt and its lessons:
  `history.md` (7b, 7b-bug).
- **Optimisations, decided with the user against level 2 and HD models:** drop the
  by-value table (serves ~10 of ~8737 vertex words a frame, costs 0.13 ms, and is
  what glues unrelated vertices), after giving those words an address path; a
  direct index instead of the OpenGL binary search. **Not** `rtp`'s math in floats:
  level 2 draws those positions, and float rounding is the wobble it removes.
  HD meshes drawn natively would not need PGXP at all; pushed through the GTE
  path, the per-vertex cost would scale with them (decision pending on how HD
  models will be drawn).
- **M4 bias:** precise positions average +0.77 console px right and down of the
  console's floored pixel (at 2x: +1.52, +1.57 px). Level 2 would move every model
  by that against the 2D elements; decide whether to compare against the pixel + 0.5.
- **Measure before and after:** a measurement build with the clamp at 2 gives the
  gaps' "before"; then the `draw_id` commit and "after" (M5), and a blind A/B of a
  slow pan for the wobble (M6; needs a frame-range dump).

**Thresholds (fixed before measuring, 2026-09-28):** level 1, a triangle is visibly
changed at a texture shift ≥ 1 screen px, clearly at ≥ 2 px, invisible below 0.5;
level 2, a vertex's rounding is noticeable in motion at ≥ 1 px; a crack is any seam
spread > 0; a scene "shows level 1" only if clearly visible pixels are ≥ 1% of the
frame or the blind A/B picks it ≥ 8 of 10. Change a threshold only in writing here,
with the reason.

### Next steps (in order)

1. The user's visual check on the PR branch; rediscuss the description; open the PR.
2. Scenes `model` (a monster filling the screen), `battle`, `small`, `control`.
3. Level 2 (above), then the runner packaged for Unchiga (M7).
4. Reuse the tools for the model work (7c).

---

## 1. Name entry: guard the picture slots

The name entry's <-, -> and END (pictures in unused Shift-JIS slots of the large font)
are HD, and the large font's `: ; < = > ?` column typo is fixed: merged upstream
(PR #110; full write-up in `history.md`).

**Left to do:** the same Shift-JIS slots may hold other pictures on other screens or
fonts. Identify the cells by their pixels (a checksum of the retail cell, as the card
view's panel does with `PANEL_SUM`), not just by position. Check after: the name
entry screen (mode 9), Password (mode 10), save names, the campaign dialogue.

---

## 2. Duel results: "You" and "Simon" are not HD

**Seen:** duel results screen, the "You" / "Simon" headers (and probably "VICTORY
CONDITIONS", "OFFENSE STATISTICS", ...) are blocky retail pixels; the bars cut their feet,
as in retail. A save state was in `tmp/pc/game32dbg-user/states/slot2.state` (may have been
overwritten since).

**Cause (verified):** not the text font. `{f8 04 01}` in the results strings (0x40-0x45)
draws a separate tiny 8x8 alphabet from the menus' sheet, page 704,0, palette 656,250, as
plain 8x8 sprites (no glyph mark):

| v | row |
|---|---|
| 80 | A-P (u 128, 136, ... 248) |
| 88 | Q-Z |
| 96 | a-p |
| 104 | q-z |
| 112 | 0-9 (already HD: `sheets[1]` in `hd_text.c`) |

"You" / "Simon" are the port's own swap for YOU / COM (`translation.c`, with Video >
Opponent's name for COM), set in that alphabet; "OFFENSE / DEFENSE STATISTICS" too. HD
numbers and labels redraws that sheet's digits but not its letters, so the letters stay
blocky and uneven.

**Decided, not started:** extend the digit `Sheet` (`hd_text.c`) to that sheet's letters:
measure the alphabet's lines together (baseline, capitals, x-height, as `measure_retail` does
for the font pages: the `Lettering` principle) and set each letter with `render_at` in the
sheet's ramp, as the digits are. Only where the retail sheet is (checksum), like the digits.
Check: results pages (all three), and wherever else the menus use that alphabet.

---

## 3. Lettering follow-ups (from the review of PR #107)

Not bugs today, latent:
1. **Word width can overflow:** a label in a lettering is set in the font's proportions
   (`sx = sv` in `set_text`) with no check against its sprite's width. ATK/DFD fit; a longer
   word (a translation) would be clipped. Fix: `sx = min(sv, what fits)`.
2. **Siblings are not redrawn:** a label is only remade when its own texels change; if one
   member of a lettering changes and another does not, the other keeps the old ink/height.
   Fix: each label remembers the lettering measurement it was drawn from and is redrawn when
   that changes.

---

## 4. Tests for HD text

No automated check covers HD text; everything was checked by eye from save states. A smoke
case (`tests/pc/smoke/*.json`: input, frame, SHA-256) with HD text on at 4x on the name
entry screen (reachable with `MEMORIES_MODE_AT`, no save needed) would catch regressions.

---

## 5. Browse cards from the card view (Up / Down): Trade and Library

Build Deck is done and merged upstream (#111): setting `card_browse`, Game > Browse
cards, `src/pc/cards/card_browse.c` with a `screens[]` table per main mode; stops at
the ends, skips empty rows. How it works and the decisions: `history.md`.

**Left to do:**
- **Trade needs a live session with an owned deck** (ideally two pads) to confirm Up/Down
  actually works, same as Build Deck needed. **Deprioritized by the user, 2026-09-27** — not
  worth a test session right now. Manual route to a save with cards, whenever it does become
  a priority: after escaping Simon's duel to the shop, save, Circle back to the title, then
  into Trade.
- **Library: not started, assessed.** Its own card display (`library_runtime.c`,
  `func_8002ACA4`, opened with Cross from `library_grid_cursor.c`), not the shared viewer.
  Its own state machine, much more involved than Build Deck's:
  1. loads the card into slot 0 and sets up a 3D camera;
  2. the card flies out of its grid cell to the centre while spinning, the description
     panel slides in;
  3. the grid fades out, the card fades in;
  4. in parallel, once the card has loaded, and if it's a monster: loads its 3D model
     (`Model_LoadMonsterMerge`), then shows a "view model" icon;
  5. **showing**: Circle closes; Triangle/Cross on a monster goes to stage 4's 3D model
     view (camera, lights, animation) — a still bigger state, not investigated;
  6. the grid fades back, the card **flies back into its grid cell**, then everything is
     released.
  Extra problems past Build Deck's: releasing/loading a 3D model mid-swap without a crash
  or leak; the card's fly-back animation targets *the cell it came from*, so browsing to
  another card must retarget it; the grid scrolls, so the next card may be off-page; locked
  ("?") cards must be skipped like Build Deck's empty rows.

  **Two approaches, recommendation: start with 1:**
  1. **Replay the retail steps (safe, slower):** Up/Down triggers the normal close (card
     flies back), then, once the grid is back, moves the grid cursor and opens the next
     card automatically (flies out again). Every animation, the model load and the grid
     scroll are the game's own code — the same principle that already worked for Build Deck
     and Trade. Cost: ~1-2s of fly-back/fly-out animation per card.
  2. **Swap in place (nicer, much more work):** stay in stage 5, release/reload the card and
     its model, retarget the fly-back cell, keep the panel. Needs the 3D model loading and
     stage-4 view understood first. Move to this only if approach 1's animation feels too
     slow once tried.

**Check after (once live-tested):** chest pane and deck pane, empty rows, sorted lists, the
last and first card, Trade with an owned deck, and that the duel's card view (same viewer)
is unchanged.

---

## 6. Crash: jump to title after loading a state from another build

**Seen:** crash reports `tmp/pc/crash-26952.txt`, `crash-26680.txt` (and reproduced):
load a save state made by a different build ("state from build X carried over to Y: N code
addresses moved"), then Debug > Jump to > Title Screen: access violation in `Main_Init`
(+0x144 / +0x166).

**Verified (2026-09-27):** not caused by our branches. No state, or a state made by the same
build: fine, in every build. A state converted from another build, then the title jump:
crashes in the `play.bat` build too, which has no card browsing. Upstream master built fresh
passed the one test tried, but its conversion moved only 7 addresses (vs ~190).

**Likely cause, not yet verified:** the title jump longjmps to the resume point `Main_Init`
saves at boot (`D_800E9DC0`, `TitleJump_Execute` in `src/pc/overrides/title_jump.c`). The
state carries that buffer; the carry-over (`src/pc/guest/state_remap.c`) seems not to remap
the native addresses in it, so the jump lands on a stale address.

**Left to do:** confirm `state_remap.c` doesn't touch `D_800E9DC0`'s buffer, then remap it
like the ~190 other addresses the conversion already moves.

**Repro:** `MEMORIES_LOAD_STATE=<state from another build> MEMORIES_TITLE_AT=120` with the
other build's symbol table in `symbols/`.

---

## 7. Model looks: HD textures, and a field tile artefact

(7a and 7b, precise geometry, are section P above; their history is in `history.md`.)

### 7c. Low-res, blurry model textures (the HD pack) — blocked, no path yet

**Cause (traced, not fixed):** the HD texture pack mechanism (`texture_pack.c`) replaces
disc pixels by *provenance*: every VRAM upload is tagged with the disc byte offset it came
from (`texture_dump.c`), and a pack image is matched to that tag plus the palette. Tested
directly: ran the `duel-3d-monsters` smoke case with `MEMORIES_DUMP_TEXTURES` on — **zero**
of the model's own textures were tagged (623 tagged from `WA_MRG.MRG`, 32 from `SU.MRG`, 0
from `MODEL.MRG`, out of the archive's 351 MB). `notes/image-remaster.md` lists `MODEL.MRG`
under "Not done" for the same reason. So an HD pack **cannot** replace model textures today,
even with redrawn art in hand — this is a separate, independent axis from PGXP (7a/7b): PGXP
never touches pixel content, only how existing textures get mapped and where vertices land.

**Leads for why the tags are lost** (not yet followed): `model_texture_transfer.c` copies
textures through work buffers (`D_801DD000` etc.) rather than a straight disc-read-to-VRAM
copy, which may be where the tag drops; `model_apply_texture_tint.c` recomputes palette
entries for a model's tint/lighting, and the pack also requires the *palette* to match the
one the image was captured through, which a computed tint palette never will.

**Once textures are taggable**, the existing pipeline (`tools/pc/extract_images.py`,
`upscale_pack.py`) applies unchanged: extract, redraw or upscale, pack. A sensible next step
after 7a/7b: pick a handful of common monsters as a pilot before committing to all ~700+.
Worth doing 7b (perspective-correct mapping) first or alongside — upscaled detail makes
affine texture warp *more* visible, not less, so shipping HD model textures without it would
look worse in places than the low-res original.

**Manual test routes the user gave me, for later sessions (not yet used):**
- After escaping Simon's duel to the shop: save, Circle back to the title, Library, click a
  card, press Right — a quick way back into a state with cards and a model to inspect.
- L1/R1 during the battle animation rotates the camera around the model (see 7b above).

### 7d. Duel field tile: a thin bright diagonal sliver, intermittent — new, not started

**Seen, 2026-09-27** (three screenshots from the user, same duel, same camera area, a few
seconds apart): a tile just past the field-card slot is clean in two of the three shots, but
in the third a thin bright yellow-white diagonal sliver cuts across its corner — a small chunk
of the tile's normal shading replaced by this streak. Comes and goes with small camera moves.

**Confirmed NOT PGXP**: the user toggled Precise geometry Textures/Off at the same spot —
"did not change much". This is on `fix/pgxp-snap-seams-identity` before any of this session's
`draw_id`/arena changes exist in the tree (only commit 1, the menu option, was applied), so it
can't be the arena-corruption class of bug either. Likely a pre-existing seam/z-fighting
artifact between the tile and the card-slot decal, or something in the base (non-PGXP)
rendering — not yet traced.

**Left to do:** get a few more repro screenshots (ideally with Precise geometry Off, to rule
out PGXP definitively rather than "did not change much"), and find what two overlapping pieces
of geometry are fighting at that seam.

---

## 8. 2D Monsters mod

**What it is:** `mods/2d-monsters/` — an alternative to 3D Monsters: an enlarged,
camera-facing cutout of a card's own art floats over it instead of a loaded
battle model. Cherry-picked here from `claude/2d-art-replace-3d-models-bbpme7`;
a clean copy also lives at `feat/2d-monsters-mod` for eventually PRing upstream.

**Fixed and confirmed live, 2026-09-29.** Three bugs, found in turn by live
testing on the user's Windows build: camera/projection setup ran after the size
calibration instead of before; a height floor (`HEIGHT_SMALLEST`) copied by
analogy from the 3D Monsters mod meant a different kind of quantity there
(a scale fraction, not a world-unit height) and pinned every cutout oversized;
and the cutout was sorted into the wrong ordering table (a 4-slot table meant
for something else) instead of the one the field's own card art and the 3D
Monsters mod both actually use, so draw order came down to chance rather than
real depth. User confirms it now looks right, with a capture. Full
investigation and the general lesson it left behind: `history.md`.

**Left to do:** record `duel-2d-monsters.json`'s `sha256`
(`python3 tools/pc/smoke.py --record`), then commit and cherry-pick the fix onto
`feat/2d-monsters-mod` for the eventual upstream PR. Then this item is done.

---

## Parked

- **Game > Restart** (dropped for now): `Platform_RestartGame()` already relaunches the
  game (used by the Mods window); a menu item would need to wait for a safe point like
  `TitleJump_Poll` (not while the memory card is written or the save menu is open).
  "Return to title" exists under Debug > Jump to > Title Screen.

- **Test scenes: boot straight into the duel** (user request 2026-09-29, later — not
  now): the **Test scenes mod** (`mods/test-scenes/`, "Measuring" above) already reaches
  its duel (Simon Muran, ten monster zones from `field.json`) from the title screen with
  L1 + Cross on Option, but that still means waiting through the title screen and
  whatever's in between. The ask: skip straight to the duel on boot — wait only for the
  game's own data load, no title screen, no intro animation, nothing to hold or press.
  Likely shaped like `MEMORIES_MODE_AT` (`progress.md`'s own "Reach a screen with no save
  needed" note under "How to test things") or `scene_measure.py`'s own boot-to-state
  flow, but triggered unconditionally at startup rather than needing a state load or a
  title-screen hotkey. Would speed up manual live-testing of test-scenes work (like this
  session's 2D Monsters mod checks) as well as automated runs.
