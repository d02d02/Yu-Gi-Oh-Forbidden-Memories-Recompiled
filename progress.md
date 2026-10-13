# Progress

Current state, decisions, what's left. Finished work and write-ups: `history.md`. Cross-worktree lessons: `notes/worktree-lessons.md`. Shared recipes: `C:\Users\mdahh\.claude\shared\yfm-notes\INDEX.md`. Research files: `tmp/pc/todo-research/` (not committed). Compacted 2026-10-13; the full earlier text is in git history (commit c99c0dafb).

## Session start: sync first
Remotes: `origin` = fork `d02d02/...`, `upstream` = `Unchiga/...` (moves daily). Before work, *ask* before any pull/reset/rebase:
1. `git status` (uncommitted work: say so, never overwrite). 2. `git fetch origin`, `git fetch upstream`.
3. Per working branch: ahead/behind `origin/<branch>` and upstream/master commits missing.
4. Behind origin only -> `merge --ff-only`; origin force-pushed -> `reset --hard origin/<branch>` only if nothing unpushed; upstream moved -> rebase, rebuild, `--force-with-lease`.
5. After a rebuild, old save states may not load (item 6): redo `scene_measure.py state`.
Before a PR: `git log upstream/master -- <files>` (a fix of ours was upstream the same day once). Cherry-pick to a clean branch, never PR a working branch. `play.bat`/`play.sh` rebuild the checked-out branch each launch.
Everything needed to resume is pushed to `origin` except the disc (`game/*.bin`, gitignored). Work branches: `dev` (tools/docs), `feat/test-scenes`, PR branch `feat/precise-geometry-menu`.

## How to test
- Fresh-install check: `python tools/pc/reset_fresh_user.py --build game32dbg --launch` (or `game32master`); rebuilds `tmp/pc/<build>-fresh-user` each run (a saved `settings.txt` always beats a mod default, so used profiles hide shipped-default bugs). `--copy-memory-card` copies `saves/` only, never `states/`; `--link-mods` junctions `tmp/pc/shared-mods/<name>`.
- Debug build `tmp/pc/game32dbg`, user dir `tmp/pc/game32dbg-user`: `$env:MEMORIES_USER_DIR="tmp\pc\game32dbg-user"; tmp\pc\game32dbg\memories-pc.exe` (`MEMORIES_LOAD_STATE=N` starts from a state slot).
- Reach a screen with no save: options smoke input + `MEMORIES_MODE_AT=1000:<mode>` (`src/game/main_modes.h`: 4 Library, 7 Build Deck, 9 Name entry, 10 Password): `MEMORIES_INPUT="910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,1040:0040,1046:0000,1060:0040,1066:0000,1100:4000,1106:0000" MEMORIES_MODE_AT=1000:9`.
- Dump: `MEMORIES_DUMP_FRAME=1500 MEMORIES_DUMP_PICTURE=1 MEMORIES_DUMP_PATH=out.ppm` (+`MEMORIES_DUMP_VRAM=1`, drops bit 15). **GL-only effects (PGXP, HD text) need a real window**: with `MEMORIES_HEADLESS=1` no GL context exists and the dump is the software picture. Use `MEMORIES_DETERMINISTIC=1` for fast stepping with a window. Frame count is the run's own (a loaded state resumes near frame 30). PPM->PNG/crop: `python tmp/pc/hd-text-split/crop.py in.ppm out.png [x y w h zoom]`.
- **`MEMORIES_INPUT` hex = raw PSX SIO bits, not `input.h`'s `PAD_BUTTON_*`:** 0001 Select, 0002 L3, 0004 R3, 0008 Start, 0010 Up, 0020 Right, 0040 Down, 0080 Left, 0100 L2, 0200 R2, 0400 L1, 0800 R1, 1000 Triangle, 2000 Circle, 4000 Cross, 8000 Square. Format `frame:code`, `0000` releases. Campaign duel with a 3D model: replay `tests/pc/smoke/duel-3d-monsters.json` `input` (frame 6760, placement reticle; Cross places, Start ends turn); 2D Monsters: `duel-2d-monsters.json` with `mod.2d-monsters` on, `mod.3d-monsters` off (they conflict).
- A state from the user's `game32` build does not load in `game32dbg` (even with equal `buildid`). Build a state inside `game32dbg`: script input with `MEMORIES_SAVE_STATE="<frame>:<path>"`, reload with `MEMORIES_LOAD_STATE` (~60 frames), iterate cheaply.
- `MEMORIES_MOD_3D_MONSTERS_TEST=<id>` fills every zone (`id + zone*2 + side`); `CACHE 8` model slots < 10 zones thrash: one-frame dumps only.
- OneDrive + WSL resolve to the same files: Linux (ELF) and Windows (COFF) builds share `tmp/pc/game32/obj` and stomp each other (link errors, "string table does not end the file"). Delete `tmp/pc/game32/obj`, or build WSL into `tmp/pc/game32-wsl`.
- Headless build: `PATH="$PWD/tmp/pc/tools/llvm-mingw/llvm-mingw-20260922-ucrt-x86_64/bin:$PATH" python3 tools/pc/build_game32.py --target windows --build tmp/pc/game32dbg` (full path; a bare name makes a stray repo-root dir). `scene_measure.py capture(options, path, pgxp, scale, frame, input=...)` screenshots deterministically: run it before asking the user to test shared-engine-state changes (VRAM, ordering tables). Confirmed scripts (2026-09-29): bare field `""`; card view `"60:1000,66:0000"`; fusion Hitotsu-me Giant (3) + Baby Dragon (4) -> Koumori Dragon `"60:0020,66:0000,120:0020,126:0000,180:4000,186:0000,240:0020,246:0000,300:4000,306:0000,360:0020,366:0000,420:0020,426:0000,480:0020,486:0000,540:4000,546:0000"` (mid-animation ~frame 620). Reference captures: `tmp/pc/measure/2d-monsters-regression/` (gitignored).

## Status board
| # | Item | Status | Branch | Next |
|---|---|---|---|---|
| P | Precise geometry level 1 (Textures) | 3 fixes measured, Linux-confirmed; rebased on upstream, pushed, PR not opened | `feat/precise-geometry-menu` (PR), `feat/test-scenes` | User's visual check, open PR |
| P2 | Level 2 (positions) | Designed (`draw_id`); built once on deleted branches | `feat/pgxp-level2` (main checkout; notes in shared `pgxp-level2.md`) | After the PR |
| 1 | Name entry slot guard | merged upstream (#110) | - | identify cells by checksum |
| 2 | Duel results letters HD | plan ready | - | extend digit `Sheet` to letters |
| 3 | Lettering follow-ups (#107) | latent | - | word-width clamp; sibling redraw |
| 4 | HD text tests | none | - | smoke case: name entry at 4x |
| 5b | Trade browse Up/Down | pushed, not live-tested | `feat/card-viewer-browse-trade` | live session |
| 5c | Library browse | assessed (big) | - | "replay retail steps" |
| 5d | Pre-duel deck-edit browse | the real priority (2026-10-04), mode unknown | `fix/card-browse-pre-duel` | find the main mode, add `move_*_cursor` + `screens[]` in `card_browse.c` |
| 6 | Crash: title jump after cross-build state load | cause likely | - | verify `state_remap.c` remaps `D_800E9DC0` |
| 7c | HD model textures | blocked, tags lost | - | trace `model_texture_transfer.c` / `model_apply_texture_tint.c` |
| 7d | Field tile bright sliver | not PGXP, not started | - | more repros |
| 8 | 2D Monsters -> 3D Monsters "Card art" style | PR #201 open, awaiting Unchiga | `feat/2d-monsters` | wait |
| 9 | MIPS-interpreted subsystems | not started | - | pick one |
| 10 | Anime style mod | frame merged upstream (#294); standalone Anime Style 1.2.3 + frame-slots PR ready, see shared `anime-frame-release-status.md` | `adhoc-anime-art-mod`, `fix/frame-slots-cache` | user decisions there |
| 11 | `field_art` cropped/distorted art | alpha + shape fixed; clipping and HD-4x bugs open | `feat/field-art-shape` | see 11 |
| 12 | Duel Links 2D Arts (code mod) | v2.4 released 2026-10-13 | `feat/duel-links-mod` | Discord post; host UI features idea |
| 13 | Kuriboh ROM-hack port | working tree only in old `-kuriboh` folder; notes `notes/kuriboh-*.md`, tools `tools/pc/kuriboh/` | `feat/kuriboh-mod` (history lost) | see notes/kuriboh-mod.md "LATEST STATE" |
| - | Game > Restart | parked | - | - |
| - | Test scenes: boot straight to the duel | parked | - | - |

## P. Precise geometry (PGXP)
Goal: level 1 (perspective-correct textures) accepted upstream with checkable evidence, then level 2 (exact positions), measured the same way; the user's wider aim is HD model textures/higher-poly models (7c).
History: upstream #49 `pgxp`, #67, #71 (merged); #83 Unchiga disabled level 2 ("opened gaps in small monsters"); **#139** ours, closed: "visible distortion", his video shows the duel-field edge on RTX 4090 + XWayland. Our Intel machines never showed it. Full story `history.md`.

**PR branch `feat/precise-geometry-menu`** (rebased on upstream/master 2026-09-29, `5a269da67`; code only; 4 commits):
1. Video > Precise geometry Off/Textures (`SET_PGXP` max 1; greyed below 2x or without GL3; default Off).
2. `gte.c`: widen rtp's window by the truncation it allows (up to ~3.6 px): near camera 2437 rejected -> 0, mixed 927 -> 4.
3. `libgs.c`/`pgxp.c`: `GsSortPoly` hands on precise vertices it copies (3D duel cards were found only by value; `Pgxp_AddPrimMoved`): mixed 24 -> 0 (duel), 18 -> 0 (turned 90 deg), 4 -> 0 (near).
4. `pgxp.c`/`libgpu.c`: per-frame tables (this + last frame, 65536 slots, stamped by frame) and `DrawOTag` skips words outside +-2048 (old 32768-slot tables held ~32000 live entries with 10 monsters: 30 fps; found live by the user).
With Off the picture is upstream's (all behind `Pgxp_Active`; six smoke screenshots byte-identical). Tests `tests/pc/pgxp_test.c`; CTests not run on Windows (CI does). PR text: observed problem -> fix -> observed result, mark seen-by-eye vs measured; Unchiga-style names `Area: what the player sees`; avoid used branch names; ask him to retry at Textures and, if it still shows, send Off vs Textures of one frame + his internal resolution. **Left:** user's visual check of this exact rebased branch, then open the PR.

**Measuring** (`tools/pc/scene_measure.py` on `feat/test-scenes`; Test scenes mod: hold L1 + confirm Option on the title = duel with Simon Muran, zones from the mod's settings/`field.json`):
`state` (boot -> scene -> save state; redo after every rebuild), `controls` (must print "controls: pass"), `compare [--scales 2,4]`, `trace [--camera turn:<deg>|near|near-half] [--scales 2]` (needs fork-only `MEMORIES_PGXP_MEASURE`: texel shift M1, mixed triangles M2, vertex offset M4, `rejects.csv`, `misses.csv`, overlay), `bench --pgxp 0,1 --scale 4 --speed -1 --repeat 5 --build <label>` (a fixed benchmark turn; ms/frame, fps, state hash; rows to `bench.csv`).
Gotchas: scale is `MEMORIES_INTERNAL_SCALE` (not `MEMORIES_SCALE`); deterministic only uncapped (`MEMORIES_SPEED=-1`); time on mains power with `--out` outside OneDrive; end states always differ in sound RAM (~`0x801E1650`, SPU).

**Results (Intel Iris Xe, 4x):** level 1 shows on the floor, not monsters (2x: 8.06% pixels change, mostly floor edges; shifts up to 4.6 px at 2x, 15-25 px close; monsters median 0.01 px). Cost (game/draw ms per frame, Off -> Textures): before speed fix 2.59/1.04 -> 5.40/1.29 (+2.81/+0.25); with fixes 2.68/1.09 -> 3.35/1.26 (**+0.67/+0.17**); Linux (Mesa, 2026-09-29) +0.66/+0.18; both settings 59.94 fps capped. Extra cost split: rtp math 18%, `Pgxp_Project` 16%, `StoreAt/AddPrim` 25%, `FindAt/DrawOTag` 9%, GL `polygon` 19%, cache 13%. Behaviour unchanged: 0 bytes differ outside sound regions over 10 runs/build.
**Unchiga's distortion:** not reproduced; best match is fix 3; we lack his Nvidia proprietary driver 610.57.04 + KDE Wayland/XWayland. Our machines: Win11 24H2 and Kali (X11 XFCE), i5-1345U, Iris Xe (Intel 32.0.101.7088 / Mesa 26.1.6), SDL 3.4.16, clang 23.1.2 (llvm-mingw) / clang 19.1.7 + gcc 14.2.0. Linux 32-bit needs `dpkg --add-architecture i386` + `libgl1:i386 libgl1-mesa-dri:i386 libpulse0:i386`; card at `~/.local/share/YFM Re-Decomp/saves/slot01.sav`.

**Level 2:** `snap_seams` (`libgpu.c`) pairs vertices by rounded screen word, so unrelated vertices snap (the #83 gaps). Design: a `draw_id` per `GsSortUnit`, threaded through `PgxpVertex` and the tables; pair only same-draw vertices (built once, no gaps with ten small monsters; redo on current code). `PGXP_VERTEX_WORDS`: `gl_picture.c` records/replays `PgxpVertex` as a word count; growing the struct without updating both corrupted the arena. Optimise (decided): drop the by-value table (~10 of ~8737 words a frame, 0.13 ms, glues unrelated vertices) after an address path; direct index instead of GL binary search; **not** rtp in floats (rounding is the wobble level 2 removes). M4 bias: precise positions +0.77 px right/down of the floored pixel (2x: +1.52/+1.57): decide on pixel+0.5. Measure gaps before/after (M5) and a blind A/B pan for wobble (M6).
**Thresholds (fixed 2026-09-28; change only in writing here):** level 1 visibly changed at texture shift >= 1 px, clearly >= 2, invisible < 0.5; level 2 rounding noticeable at >= 1 px; a crack = any seam spread > 0; a scene "shows level 1" only if clearly visible pixels >= 1% or blind A/B picks it >= 8/10.
Next: PR; scenes `model`, `battle`, `small`, `control`; level 2, then runner for Unchiga (M7); reuse tools for 7c.

## 1-4. HD text
1. Name entry arrows/END pictures sit in unused Shift-JIS slots of the large font (merged #110). Left: other screens/fonts may hold other pictures there; identify by pixel checksum (like `PANEL_SUM`); check modes 9, 10, save names, dialogue.
2. Duel results "You"/"Simon"/"OFFENSE STATISTICS" are blocky: `{f8 04 01}` draws an 8x8 alphabet from page 704,0 palette 656,250 (v 80 A-P, 88 Q-Z, 96 a-p, 104 q-z, 112 digits = already HD, `sheets[1]` in `hd_text.c`); "You"/"Simon" are the port's swap for YOU/COM (`translation.c`). Plan: extend the digit `Sheet` to letters (measure baseline/caps/x-height as `measure_retail` does; `render_at`; only where the retail sheet matches by checksum).
3. Latent (#107 review): word width can overflow (`sx = sv` in `set_text`, clamp to what fits); siblings not redrawn when one member changes (remember the measurement drawn from).
4. No automated HD text check: add a smoke case (`tests/pc/smoke/*.json`) at 4x on the name entry (reachable with `MODE_AT`).

## 5. Browse cards (Up/Down)
Build Deck merged (#111): setting `card_browse`, `src/pc/cards/card_browse.c` `screens[]` per main mode; stops at ends, skips empty rows. Trade needs a live session with an owned deck (route: escape Simon's duel to the shop, save, Circle to title, Trade); deprioritized 2026-09-27; headless `MODE_AT` leaves inventories empty. Library has its own state machine (`library_runtime.c`, `func_8002ACA4`): card flies out, panel slides, grid fades, model loads (`Model_LoadMonsterMerge`), fly-back to its cell. Approach 1 (recommended): Up/Down triggers the normal close, then moves the grid cursor and reopens (~1-2 s per card; all retail code). Approach 2: swap in place (needs the 3D model view understood). Check after: chest/deck panes, empty rows, sorted lists, first/last card, duel card view unchanged.

## 6. Crash: title jump after a cross-build state load
Load a state from another build ("N code addresses moved") then Debug > Jump to > Title: access violation in `Main_Init` (+0x144/+0x166), also in the play.bat build (not ours). Likely: `TitleJump_Execute` (`src/pc/overrides/title_jump.c`) longjmps to `D_800E9DC0` saved at boot; `state_remap.c` (~190 addresses) probably does not remap it. Repro: `MEMORIES_LOAD_STATE=<foreign state> MEMORIES_TITLE_AT=120` with the other build's `symbols/`.

## 7. Model looks
**7c HD model textures (blocked):** the pack matches by provenance tag (disc byte offset per VRAM upload, `texture_dump.c`) + palette. With `MEMORIES_DUMP_TEXTURES` on the `duel-3d-monsters` smoke: 623 tagged from `WA_MRG.MRG`, 32 `SU.MRG`, **0 from `MODEL.MRG`** (351 MB; `notes/image-remaster.md` lists it "Not done"). Leads: `model_texture_transfer.c` copies through work buffers (`D_801DD000`) dropping tags; `model_apply_texture_tint.c` computes palettes the pack can never match. Then `extract_images.py`/`upscale_pack.py` apply; pilot a few monsters; do perspective-correct mapping (7b) first (HD detail makes affine warp worse). Route to a state with cards: after Simon's duel to the shop, save, Circle to title, Library, click a card, Right; L1/R1 in battle rotates the camera.
**7d (2026-09-27):** thin bright yellow-white diagonal sliver across a tile corner next to the field-card slot, intermittent with small camera moves; not PGXP (toggle changed little, present before `draw_id`). Likely seam/z-fight between tile and slot decal. Need more repros (PGXP Off).

## 8. 2D Monsters mod (`mods/2d-monsters/`)
Camera-facing cutout of a card's art instead of a model; folded into 3D Monsters as "Card art" (PR #201). Sizing and depth-sort fixed (three wrong assumptions borrowed from 3D Monsters). An HD-pack attempt broke opponent art, a fusion animation and the card title and was reverted. Validated HD design (unbuilt): `LoadImage` art to scratch VRAM, wait one frame (`TexturePack_EntryFor` resolves on the next service tick), `TexturePack_EntryImage` pulls the HD image (e.g. 408x384 `card-001.png`), bake into the private bank, then restore the scratch VRAM; needs a two-frame pending state per cache slot and RGBA->bank resampling. Decided: ship without HD (3D Monsters has the same limit); HD support deserves its own PR. Clean branch `feat/2d-monsters-mod` (4 commits on upstream/master 2026-09-29). Left: user tests Windows then Linux, then PR.

## 9. MIPS-interpreted subsystems (run via `src/pc/guest/mips.c`, correct, not native C)
(1) shared duel effects bank `0x80146000` (entry `0x801462B0`; fusion, damage, destruction, magic/trap/ritual/terrain/field up to id 23; `MEMORIES_DUEL_EFFECTS=native` = old bring-up); (2) credits module (`Main_RunCredits` phase 2, `func_800507D0`, loads MIPS at `0x80180000`); (3) monster attack choreographies, the big one: MODEL.MRG 621 records, 1,181 distinct variant modules (`MEMORIES_MODEL_MODULES=native` = spark burst). Not started; a 2026-09-21 scan found only instructions the interpreter handles (no GTE opcodes): translation volume only, independent pieces. Detail `notes/pc-build.md`; end state "no reachable MIPS fallback" in `notes/pc-port-plan.md`.

## 10. Anime style mod
Design and ranked engine candidates: `notes/anime-style-mod-plan.md`. Frame shipped upstream (#294, in Forbidden Memories HD). Standalone Anime Style (mod id `anime-art`, branch `adhoc-anime-art-mod`, 1.2.3) and the frame-slots/cache engine PR (`fix/frame-slots-cache`, PR not opened): status and decisions in shared `anime-frame-release-status.md`. Doc fixes owed upstream: stale "Known limitation" paragraph in `notes/modding.md` (~line 993); `modapi.h` lists API up to 9, code is 10.

## 11. `field_art` (3D Monsters "Card art") cropped/distorted mod art
Fixed on `feat/field-art-shape` (real asset `artes_duel_links_fm/5_Ryukishin.png`): fixed 102x96 crop (`CardArt_FieldArtFit` sizes to the PNG's ratio, cap 256); colour fringe (premultiply before the box filter, undo after); alpha cutoff (Bayer dither was wrong: reads as static; flat cutoff 32, down from 128). Open: (a) wings' left/right/bottom hard-clipped at 1x (`clippedwings2.png`; suspect `CardArt_FieldArtFit` width or `field_art.c` `draw_one` `width_px`); (b) HD pack path at `MEMORIES_INTERNAL_SCALE=4` renders broken (blank background, dotted wing, garbled card): repro with `MEMORIES_WINDOW_SHOT`, not `MEMORIES_DUMP_PATH`. Single branch now (`fix/field-art-alpha-fringe`, `feat/field-art-fit` deleted as subsets); debug `say()` WIP commit to drop; base ~153 commits behind upstream: rebase after the clipping fix, then one PR. Order: (1) clipping, (2) HD/4x, (3) rebase, (4) PR.

## 12-13. Duel Links 2D Arts, Kuriboh
See `notes/worktree-lessons.md` (+ shared `duel-links-mod.md`; Kuriboh: `notes/kuriboh-*.md`).

## Parked
- **3D Monsters `pixels`/`scale` need a restart and Card art inherited that** (2026-09-30): shared `pixels` key carries `"restart": true`. `fit()` (`field_models.c`) only re-measures resident geometry (no disc/VRAM), so live would be cheap (track last-seen values, refit cached monsters; unverified: packet buffer size vs rescale). User: not worth touching `fit()`/`acquire()`. Alternative: Card art's own height key (small duplication, zero risk).
- **Per-card glow colour** (2026-09-30): only colour, via `cards.c` table `glow_colors[CARD_TABLE_ID_END]`, `cards` key `"glow_color"`, getter `Cards_GlowColor`, read in `draw_glow` before settings; after the field_art and 3D-merge work.
- **Custom 3D models** (2026-09-30): `"model"` only borrows disc models; read upstream `feat/model-replace` first.
- **Game > Restart:** `Platform_RestartGame()` exists (Mods window); a menu item must wait for a safe point like `TitleJump_Poll`.
- **Test scenes: boot straight to the duel** (2026-09-29): skip the title, shaped like `MEMORIES_MODE_AT`/`scene_measure.py`'s boot flow, triggered at startup.
