# Lessons from the other worktrees (2026-10-13)

Terse digest; details in the named notes/branches. Shared testing recipes: `C:\Users\mdahh\.claude\shared\yfm-notes\` (`INDEX.md`).

## Git/worktree safety
- Worktree registrations (`.git/worktrees/*`) and local branches vanished once; objects survived, `origin` branches fine. Branches never pushed (kuriboh) lost their history: **push every branch early**.
- Re-link a folder whose `.git` points at a lost registration: `git worktree add --no-checkout ../wt-tmp <branch>`; move `wt-tmp/.git` into the folder; `git worktree repair <folder>`; `git reset` (mixed). Check `git status`: the folder's files may be older than HEAD, so never `add -A` blindly.
- No global git identity: `git -c user.name=d02d02 -c user.email=334354742+d02d02@users.noreply.github.com commit`. No `gh`: release via API with a token from `git credential fill`.
- The auto-mode classifier blocks `rm` of untracked files, force pushes, moving `.git`, new-branch plumbing: ask the user. `Remove-Item` on top-level `C:\` folders: use `cmd /c rd /s /q`.
- NB: `origin/master` on the fork is stale; use `upstream/master`. Upstream docs (`notes/modding.md` etc.) are upstream's: do not rewrite them here (merge pain).

## Testing traps
- A running `memories-pc.exe` locks the link ("Permission denied" in play.bat); test timeouts leave orphan exes: kill them. PowerShell: `$null = $p.Handle` before `WaitForExit`; `"$Set:"` parses as a scope, use `${Set}`.
- Never run `fm_editor/__main__.py` (GUI) or `test_gui` (hangs headless). Editor suite: `cd tools/pc; python -m unittest discover -s fm_editor/tests -t .` in the background to a file (minutes; 492 tests).
- `tools/pc/test_*.py` mostly need prebuilt guest tools / macOS arm64: do not expect them on Windows.
- Windowed `Game` hangs (virtual clock); headless Internal 4x hung for minutes. Real-window shots: `MEMORIES_WINDOW_SHOT`; `MEMORIES_DUMP_PATH` misses the GL path. `shot()` without `MEMORIES_DUMP_PICTURE=1` is the 320x240 VRAM.
- Mod settings in a run: `MEMORIES_MOD_<ID>_<KEY>=n` (a fresh profile's bool reads 0, not the manifest default). Own profile: `MEMORIES_USER_DIR`. A mod's `.o` must be rebuilt after source changes (build recipe: `mods/duel-links-2d-arts` notes below).
- Mod .o build (Windows): llvm-mingw `bin` on PATH via `cygpath -u` (a `C:/` path in bash PATH breaks), `MEMORIES_MOD_CC=clang.exe`, `python tools/pc/build_mod.py <stage dir> --target i386 --target x86_64-windows`. Zip with Python `zipfile` (forward slashes), not Compress-Archive.
- Scene rigs: hold L1 + confirm Option on the title = test-scenes duel (`mods/test-scenes`: settings p1-p5/o1-o5, `sets/`, `run-set.ps1`). Every card in the scene must be a monster or it falls back to Options.

## Anime frame / card_layout (branch adhoc-anime-art-mod, fix/frame-slots-cache)
- v0.3.0 bug: one bank slot for the frame texture, two styles on screen share a frame (trap beside its attacker); fix = 3 slots, grid 3x3 -> 2x2. Slowdown: FRAME_CACHE 8 < 10 frame PNGs, eviction cleared slots, PNG decode twice a frame (Slifer attack 150 s vs 24 s): cache 64 + LRU. PR branch `fix/frame-slots-cache` (not opened).
- 2x/4x invisible frame: `bank_halve` rounded mips up; GL needs floor(w/2^n) so non-power-of-two PNGs got incomplete mip chains (`debug/v0.3.0-frame`, `fix/anime-frame-4x-mips`); frames also shipped as POT PNGs (`asset/anime-frame-pot`).
- Pixelated HD art in anime layout: shader picked texels nearest; blend 4 texels where a pixel spans < 0.85 texel (`fix/hd-art-bilinear`).
- "Submitted but not drawn" recipe: `MEMORIES_TRACE=card_layout,mods`, `MEMORIES_LOG=<file>`, `LOG_SAMPLED`; log every stage (layout -> DrawFrame -> FrameTile -> AddBankSpriteCrop -> GL lookup -> bind).
- Frame PNGs were contrast-boosted dark (4654ebb9b); light originals at ff79f7dd0. Card rotation checked, no bug.

## HD overhaul (feat/hd-overhaul)
`hd_auto_pack.py` enlarges all static assets; sprite-built UI shows seams, fixed by `hd_sprite_pack.py` (compose, enlarge once, cut back); `hd_shot.py` = headless A/B at 4x in 25 s. User's rules: small increments, one screen, an A/B picture each step, minimal verbosity, no long runs before a proof.

## Kuriboh mod (notes/kuriboh-*.md, tools/pc/kuriboh/)
Reproduces the Kuriboh ROM hack from the player's own ISO via the editor importer (`python tools/pc/fm_editor import <iso> --game game\ygofm-orig-usa.bin --id kuriboh`); outputs under `tmp/kuriboh/` (ignored), nothing of the ROM hack committed. Engine pieces are generic: `equips` `any_card`, `terrain_bonus` `cards`, `limits.card_copies`, `unique_drops`. Extra duelists (ids 40-55, mode = id-39) start from dialogue scripts, not menus. Open: models for new monsters, Duel Master K deck roll, harder discs. Branch `feat/kuriboh-mod` history is lost (never pushed); the working tree is only in the old `-kuriboh` folder.

## 3D Monsters / field_art (feat/field-art-shape)
Fixed: premultiplied alpha, shape fit, lower cutoff. Open: wings hard-clipped at 1x (`CardArt_FieldArtFit` width or `draw_one` `width_px`), HD pack path broken at Internal 4x. Branch is ~150 commits behind upstream: rebase after the clipping fix.

## Duel Links 2D Arts (feat/duel-links-mod, released v2.4)
Code mod, no engine change. Engine's field_art loader crops/squeezes/cuts alpha at 128: bypassed with own 256x241 255-colour `.tex`. A `cards` `replace` without `name` wipes names (never use it for art). Outline = the art redrawn 8x offset behind it in a white CLUT tinted per ring; halos add/subtract in two blend modes; float = whole pixels move the quad, the fraction slides UVs. Host settings UI is flat (int/bool/choice/key): groups via "GROUP | Name" labels; wanted upstream: groups, `show_if`, colour swatch.
