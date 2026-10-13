# Anime Style Mod: design plan (2026-10-07; compacted 2026-10-13)

Goal: one mod (`mods/anime-style-mod/`; the shipped standalone is `anime-art` on branch `adhoc-anime-art-mod`, see shared `anime-frame-release-status.md`) re-skinning FM in the anime's look and sound: card frames, title/menu art, music, voice/jingle clips, later card art. Script, rules, stats, fusions, drops stay byte-identical: presentation only.

## Precedent
- `card_layout`, `title`, `menu`, `audio`, `cards` are generic no-code manifest keys (`notes/modding.md`).
- Upstream review `1710f3851` (fold 2D Monsters into 3D Monsters as a style): sibling presentation variants = one mod with a style/bool setting, not conflicting mods. One folder, one manifest, a toggle per piece.
- Frame merged: PR #294 (`card_layout` engine `src/pc/cards/card_layout*.c`, frames `tools/pc/hd_recipes/anime_frame_{monster,magic,trap,orange}.png`, an HD-mod option); this mod reuses them without the HD mod. PR #293 (yamyi): named-asset catalog (non-frame UI skin = no code).
- `notes/image-remaster.md`: a full AI-upscaled pack was shelved as too ugly: read it before touching art (upscalers smear UI/fonts; card art "filtered, not redrawn").

## Scope
Locked: one mod id/dir; no rules changes (other mods' job; keeps stacking with AI Hard Mode, 3D/2D Monsters, packs). Video/FMV out of scope: `MASTER.XA`/`MOVIE.STR` interleave sound with picture and cannot be data-replaced (`notes/modding.md`); needs code + engine support.

| Setting | Reskins | Manifest key | Source | Phase |
|---|---|---|---|---|
| `card_frame` | full-bleed frame per kind | `card_layout` | the four anime frames; `ritual` borrows `monster` | 1 |
| `title_skin` | title + menus | `title`, `menu` | anime key art | 2 |
| `music` | title/menu/duel/campaign songs | `audio.music` | OST as Ogg | 3 |
| `voice_jingles` | XA stings | `audio.xa` | clips as Ogg, matched to original length ("Finding the ids" in `notes/modding.md`) | 3 |
| `sfx` | menu blips etc. | `audio.sfx` | anime SFX | 3 |
| `card_art` (stretch) | card art | `cards[].art` or `textures` | per-card art, the biggest item | 4 |
| `fmv` (stretch, code) | intro/cutscenes | none | new engine work | 5 |
Phases 1-3 are pure data and apply live; only `card_art`/`fmv` might need `restart: true` or code.

## Open (user's call)
1. Where OST/video/key art comes from (rip, remaster, hand-painted, AI stills) and the quality bar. 2. Redistribution: ship assets outright (personal use) or ship a tool that builds them from the player's own source files (pattern of `upscale_pack.py`); bundling ripped anime audio/video is more sensitive than the game's own textures.

## Candidate engine issues (code-verified on upstream/master `ee0f8d836`)
Sizes S < 1 day, M few days, L a week+.
What the code supports: title/menu skin (`title`/`menu`, `title_config.c`, `title_images.c`) yes; music/XA/SFX by id (`audio/replace.c`) yes; card art, frames, UI, duel HUD, Build Deck images via `assets` (`docs/asset-catalog.json`, 2777 names: card_frames 340, build_deck 95, duel 32, UI 30...) yes; portraits, scenes, terrains, map, menu sheets only via disc-extracted `textures` packs (`tools/pc/extract_images.py`, `upscale_pack.py`); settings UI types `int/bool/choice/key` only (`mods_window.c`, `manager.c:258-269`), per-mod Restore defaults, named profiles, no grouping/colour/conditional rows; `setting` gating works on `textures`/`assets` (bool, `texture_pack.c:1265`) and rule tables/`text`/`font` (`value` for choice, `mods.c:1546`) but NOT on `audio`, `title`, `menu`, `card_layout`; events exist (`mod_types.h:10-50`) but `modapi.h` has no play-sound entry (`AudioReplace_Sfx(id, vol, pan)`, `replace.h:87`, is an unstable port symbol); overlays (`MemoriesMod.overlay`, `modapi.h:68`) draw text and rectangles only; no `models` key (`mods.c:1216`; `3d-monsters` is 1933 lines reading records itself); FMV refused (`mods.c:805`, software MDEC `libpress.c`); no in-game zip install (only "Open mods folder", `mods_window.c:619`); audio decodes to ~10 MB/min.
Ranked:
1. Setting-gated `audio`/`title`/`menu`/`card_layout` (S-M): extend `setting` (+`value`) via the same `entry_used` helper; multi-theme mods switch live.
2. Event-triggered audio (S then M): `host->play_sound(kind, id)` (API 11), then `audio.events`; audio runs on the VBlank thread, so only post a request.
3. Image blit in overlays (S-M): `host->draw_image` (PNG, position, scale, alpha); declarative `effects` later (L).
4. Settings UI sections and `visible_if` (M): `group` heading, `visible_if`, theme `choice` with preview text; Mods window only (also the Duel Links 2D Arts wish list: groups, show_if, colour swatch).
5. Catalog coverage for portraits/scenes/terrains/map (M): map extractor families to names (`tools/pc/asset_catalog.py`).
6. Mod install from a zip (M): safe unzip with size/path checks.
7. 3D model/animation replacement (L, high risk): `models` key + format + importer first.
8. Movie replacement (L, high risk): `movies` key, host decoder, XA interleave.
9. `card_layout` follow-ups (S-M, low).
Corrections to earlier statements: a `choice` cannot switch audio/title sets today; overlays cannot draw images; `assets` lacks portraits/scenes; API version is 10 (`mod_types.h:3`) while `modapi.h`'s header lists up to 9.

### Flaws in the merged `card_layout` (read from `card_layout.c`, `card_layout_art.c`, `func_80028B08.c`; not measured)
- Frame cache held one kind at a time (one `made_path` slot, one `FRAME_BANK`): kinds re-decoded on each switch, two on screen thrash. (Since fixed downstream: 3 slots, cache 64 + LRU, `fix/frame-slots-cache`.)
- Frame flattened to 177x254 (`FRAME_W/H`, u8 UV limit of POLY_GT4; ~27x area loss for 919x1319): inherent; a higher-resolution path above 1x exists for card art/title images, unverified for the frame quad.
- `full_bleed` read by name via `full_bleed_of()` -> `Mods_Setting(id, "full_bleed", 0)`: fallback must match the manifest default. Last mod with the key wins (`find_source()`, by design; ~9 calls per card draw with path joins, negligible). `CardLayout_FullBleed()` branches at 5 sites in `func_80028B08.c` (351, 361, 389, 485, 540) + `duel_effect_resource_setup.c`. Spell/trap icon rect has no image (retail elemental texture drawn). Positions: retail offsets (`0x61`, `0x9D`) are fallbacks only; full-bleed uses plain viewer pixels, origin undocumented (doc fix). Duel-viewer depth bug fixed; stale "Known limitation" paragraph in `notes/modding.md` remains (doc fix).

## Phasing
1 frame + `assets` UI skin; 2 title/menu; 3 music/jingles/SFX; 4 engine: setting-gated keys (1) and event audio (2); 5 portraits/scenes/card art via `textures` (largest; needs `image-remaster.md` lessons + sourcing answer); 6 engine as wanted (overlay images, settings sections, zip install); 7 stretch (3D animations, FMV, declarative effects).
Status: candidate list written; the issue scope is the user's decision.
