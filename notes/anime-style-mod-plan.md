# Anime Style Mod: design plan

Plan written 2026-10-07, branch `anime-style-mod` (forked from
`upstream/master`, now at `ee0f8d836`). Goal: **one mod, `mods/anime-style-mod/`,
that re-skins Forbidden Memories in the look and sound of the Yu-Gi-Oh!
anime** -- card frames, title/menu art, music and voice/jingle clips, and
later card art -- while the campaign script, duel rules, card stats,
fusions and drops stay byte-identical to retail. This is a presentation
skin, not a gameplay or story mod: the form changes, the story does not.

## Precedent this follows

- `card_layout`, `title`, `menu`, `audio` and `cards` are already generic,
  no-code manifest keys (`notes/modding.md`): nothing new needs inventing
  in the engine for most of this, only a well-made manifest and assets.
- Upstream review precedent, `1710f3851` ("Fold 2D Monsters into 3D
  Monsters as its Card art style, per review"): sibling presentation
  variants that share a theme belong in **one mod with a style/bool
  setting**, not several mods that then have to declare conflicts with
  each other (`mods/3d-monsters/mod.json`'s `style` choice is the shipped
  example). `anime-style-mod` follows that: one folder, one manifest, each
  piece its own toggle, not a family of mods.
- The card-frame piece is **merged**: PR #294 put the `card_layout` engine
  (`src/pc/cards/card_layout*.c`) and the per-kind frames
  (`tools/pc/hd_recipes/anime_frame_{monster,magic,trap,orange}.png`) in
  `upstream/master`, as an option of Forbidden Memories HD. This mod reuses
  those pixels and the `card_layout` block, and does not depend on the HD mod.
- PR #293 (yamyi) also merged: a named-asset catalog (below). It makes the
  non-frame UI skinning a no-code job.
- `notes/image-remaster.md` is the record of a full AI-upscaled HD pack
  that was built and shelved as **too ugly to ship**. Any art touched here
  -- especially card art and portraits -- reads that first: generic
  upscalers smear UI/fonts and leave card art "filtered, not redrawn."

## Scope locked so far

- One mod id and directory: `anime-style-mod`, under `mods/`.
- Campaign script, duel rules, card stats, fusions, drops, guardian star
  matchups: untouched. A rules change is a different mod's job, and mixing
  the two risks fighting whatever gameplay mod a player already runs
  (that's exactly what the manifest's conflict/overlap warnings exist for).
- **Video/FMV is out of scope for now.** `MASTER.XA`/`MOVIE.STR` cannot be
  replaced or patched by a data mod -- their sectors interleave sound with
  the picture, and a data override writes a plain data sector's worth of
  bytes into a format that needs more (`notes/modding.md`, "The streamed
  files ... cannot be replaced"). Swapping video needs a code mod and new
  engine support neither of which exists yet; parked as a stretch goal,
  revisited only once the no-code skin is solid.

## Pieces, each its own setting in one `mod.json`

| Setting key | What it reskins | Manifest key(s) | Source material | Phase |
|---|---|---|---|---|
| `card_frame` | full-bleed anime card frame, per kind | `card_layout` | reuse `anime_frame_{monster,magic,trap,orange}.png` as-is; `ritual` still borrows `monster`'s, per the existing fallback rule | 1 |
| `title_skin` | title screen + both menus: background, logo, PUSH START, copyright, button art | `title`, `menu` | anime key art / logo treatment | 2 |
| `music` | title, menu, duel and campaign songs | `audio.music` | anime OST tracks, as Ogg | 3 |
| `voice_jingles` | XA stings/fanfares (duel start, victory, chest, etc.) | `audio.xa` | anime voice/jingle clips, as Ogg, matched to each clip's original length (see "Finding the ids" in `notes/modding.md`) | 3 |
| `sfx` | menu blips, card select and similar (lower priority, nice-to-have) | `audio.sfx` | anime SFX | 3 |
| `card_art` (stretch) | monster/spell/trap art repainted anime-style | `cards[].art` (`replace` entries) or a `textures` pack | per-card art, the biggest line item by far | 4 |
| `fmv` (stretch, needs code) | intro / cutscene replacement | none today | new engine work | 5 |

Everything through phase 3 is a pure data mod (`notes/modding.md`'s "Data
mods: no code at all" / "Texture packs" / "Audio" sections) and every
setting there applies live, no restart, exactly like Forbidden Memories
HD's own part-settings. `card_art` and `fmv` are the only pieces that might
ever need `restart: true` or actual code.

## Why not fold in guardian stars, rules, or the FM Editor's tables

"Form, not story" is the line: renaming guardian stars, reweighting
fusions, retuning AI, or reskinning drops are rules changes, not a visual
skin, and belong in a separate mod a player opts into on top of this one if
they want both. Keeping `anime-style-mod` presentation-only is also what
lets it stack cleanly with AI Hard Mode, 3D/2D Monsters, card packs, and
anything else already in `mods/`.

## Open questions -- asset sourcing, not engine design

These are the user's call, not something to guess at:

1. **Where the OST/video/key-art actually comes from**, and at what
   quality -- ripped from the show, a fan remaster, hand-painted, or
   AI-upscaled stills. Whatever is picked needs the same care
   `image-remaster.md` had to learn the hard way (right tool per asset
   family, never a blanket upscale, hand-touch fonts/UI).
2. **Redistribution.** Reusing the game's own extracted textures is
   already handled carefully elsewhere in this repo ("the images are the
   game's, so a pack ships painted images or a way to make them from the
   player's own disc, never the originals" -- `notes/modding.md`).
   Bundling ripped copyrighted anime audio/video in a published mod is a
   different and more sensitive question than that. Worth deciding up
   front whether this mod ships the assets outright (personal/local use)
   or ships a tool that builds them from source material the player
   supplies themselves (the same pattern `upscale_pack.py` already uses).

## Candidate issues (code-verified, 2026-10-07)

Judged by reading the code on `upstream/master` (`ee0f8d836`), not the docs
or PR history. Standalone mod: nothing here assumes the HD pack. Sizes: S
under a day, M a few days, L a week or more. Each gap is framed as a general
engine feature.

### What the code supports today

| Layer | Verdict | Evidence |
|---|---|---|
| Title and menu skin | Supported | `title`/`menu` keys, `src/pc/platform/title_config.c`, `title_images.c` |
| Music, XA, SFX replacement by id | Supported | `src/pc/audio/replace.c`, `replace.h` (`AudioReplace_Load`) |
| Card art, frames, UI, duel HUD, Build Deck images | Supported | `assets` key, `docs/asset-catalog.json` (2777 names: card_art, nameplate, thumbnails, card_frames 340, build_deck 95, attributes, duel 32, UI 30, monster_type, star_guardians) |
| Portraits, story scenes, terrains, map, menu sheets | Partial | not in the catalog; only via `textures` packs made from the player's disc (`tools/pc/extract_images.py`, `upscale_pack.py`) |
| Settings UI | Partial | `src/pc/platform/mods_window.c`, `manager.c:258-269`: types `int`, `bool`, `choice`, `key` only; per-mod "Restore defaults" (`mods_window.c:594`), named profiles across all mods (`manager.c:292-351`). No grouping, colour input, or conditional visibility |
| Theme switching with no code | Partial | `setting` gating works on `textures`/`assets` entries (bool, non-zero only, `texture_pack.c:1265`) and on rule tables/`text`/`font` (with `value` for a `choice`, `mods.c:1546`). It does **not** reach `audio`, `title`, `menu` or `card_layout` (no `setting` in `replace.c`, `title_config.c`, `card_layout.c`) |
| Event-triggered audio | Partial | Events exist (`mod_types.h:10-50`: DAMAGE, REWARD, FUSION, EFFECT, SCENE, MONSTER...). `modapi.h` has **no play-sound entry**. A code mod could call the port's `AudioReplace_Sfx(id, vol, pan)` (`replace.h:87`) only through an unstable port symbol |
| 2D cut-ins and overlays | Partial | `MemoriesMod.overlay` (`modapi.h:68`) draws **text and filled rectangles only** (`draw_text`, `fill`); no image blit, no declarative form |
| 3D models and animations | Partial | no `models` manifest key (`mods.c:1216`). `MODEL.MRG` can be replaced as a whole file but buffers and record layouts are fixed; `3d-monsters` is 1933 lines of code that reads records itself (`field_models.c`) |
| FMV | Missing | `MASTER.XA` and `MOVIE.STR` refused (`mods.c:805`); the movie path is the game's own reader plus a software MDEC (`src/pc/sdk/libpress.c`) |
| Distribution when the player supplies the source | Partial | no in-game install: only "Open mods folder" (`mods_window.c:619`), no zip handling in `src/pc`; `upscale_pack.py --zip` builds a zip. No tool turns player-owned audio/video into a mod folder. Audio is decoded to memory at ~10 MB per minute (`notes/modding.md`) |

### Ranked candidate issues

1. **Setting-gated `audio`, `title`, `menu` and `card_layout`** (S to M).
   Pitch: `setting` (and `value` for `choice`) already switches `textures`,
   `assets` and rule tables; extend it to these four keys so one mod can ship
   several themes and switch them live. General use: any multi-variant mod.
   Risk: low; same helper (`entry_used`).
2. **Event-triggered audio** (S, then M).
   Pitch: add `host->play_sound(kind, id)` for code mods (API 11), then an
   `audio.events` map from event (MONSTER summon/destroyed, DAMAGE, REWARD,
   FUSION, SCENE) to a clip, optionally per card. Risk: audio runs on the
   VBlank thread (`replace.h` rules), so the call must only post a request.
3. **Image blit in overlays** (S to M).
   Pitch: add `host->draw_image` (PNG from the mod, position, scale, alpha)
   to the overlay API so code mods can show cut-ins and banners; a later
   declarative form (`effects`: image/sprite sheet on an event) needs no C.
   Risk: low for code mods; the declarative layer is L.
4. **Settings UI: sections and conditional rows** (M).
   Pitch: optional `group` heading and `visible_if` on a setting, plus a
   theme-style `choice` with preview text, so a large mod (30+ options) stays
   usable. Risk: low; Mods window only.
5. **Catalog coverage: portraits, scenes, terrains, map** (M).
   Pitch: give these the `assets` names `card_art` already has, so a theme can
   replace them without disc-extracted pack manifests. Risk: needs the
   extractor's families mapped to names (`tools/pc/asset_catalog.py`).
6. **Mod install from a zip** (M).
   Pitch: let the Mods window unpack a zip into the user mods folder, with a
   size and path check. General use: every mod. Risk: needs a safe unzip.
7. **3D model/animation replacement** (L, needs scoping).
   Pitch: a `models` key mapping a model id to a file in a documented format,
   with the loader reading it where it reads `MODEL.MRG`. Risk: high; buffer
   sizes, a format and an importer are all needed first.
8. **Movie replacement** (L, high risk).
   Pitch: a `movies` key replacing a streamed movie with a mod file, keeping
   the game's skip and timing logic. Needs a decoder on the host side
   (MDEC strips or a video library) and a way around the XA interleave.
9. **Card layout follow-up** (S to M, low priority): the table below.

### Where the code contradicted earlier statements

- A `choice` theme cannot switch audio or title sets today (earlier plan
  assumed it could); candidate 1 fixes that.
- The overlay API cannot draw images (earlier notes said "overlay for
  drawing" as if it could).
- `assets` does not cover portraits or scenes; those still need `textures`.
- API version is 10 (`mod_types.h:3`) but `modapi.h`'s header comment lists
  up to 9 (the MONSTER event is API 10): a doc nit.

### Remaining flaws in the merged `card_layout`, checked against the code (2026-10-07)

Read `card_layout.c`, `card_layout_art.c` and the call sites in
`func_80028B08.c`. Not measured at runtime.

| Claim | Verdict | Evidence |
|---|---|---|
| Frame cache holds one kind at a time | **Real, new finding** | `card_layout_art.c`: one `made_path` slot and one `FRAME_BANK`; a different kind means a different path, so `made=0` and the PNG is decoded and quantised again. Browsing mixed card kinds re-decodes on each switch; two kinds on screen in one frame would thrash (unverified). Fix: a bank slot per kind. |
| Frame flattened to 177x254 | **Real, inherent** | Fixed `FRAME_W/H` (u8 UV limit of POLY_GT4); ~27x area loss for a 919x1319 source. Cards' own art and `title` images have a higher-resolution path above 1x; whether the projected frame quad can use it is unverified. |
| `full_bleed` read by name | **Real, mild** | `full_bleed_of()` calls `Mods_Setting(id, "full_bleed", 0)`. The fallback `0` must be kept in sync with the manifest default (the code comment says so). A mod with another setting name gets nothing. |
| Last mod wins, no merge | **Real, by design** | `find_source()` keeps the last active mod with the key. Same rule as other singular keys; a limitation, not a bug. |
| Call-site special cases | **Real, moderate** | `CardLayout_FullBleed()` branches at 5 sites in `func_80028B08.c` (351, 361, 389, 485, 540) plus `duel_effect_resource_setup.c`. Placements themselves are read once per draw (221-227). |
| Spell/trap icon has nowhere to draw | **Real, a missing feature** | `spell.icon` rect gets no image; retail's elemental texture is drawn. |
| `find_source()` re-walk per call | **Overstated** | Real (about 9 calls per card draw, each with a path join), but a handful of mods; negligible. Only worth fixing alongside other changes. |
| Positions as retail offsets | **Overstated** | Retail values (`0x61`, `0x9D`...) are only the fallbacks for keys a mod omits. In full-bleed the manifest gives plain viewer pixels. The coordinate origin is just not documented. Doc fix. |
| Duel-viewer depth bug | **Fixed** | Only the stale "Known limitation" paragraph in `notes/modding.md` remains. Doc fix. |

Net: a follow-up PR is justified by the per-kind frame cache and, if
feasible, the frame resolution. The rest is documentation or minor.

## Phasing

Data work can start now; engine pieces ship as their own small PRs (see
"Ranked candidate issues").

1. **Frame** (`card_frame` bool, `card_layout` block) and **UI skin via
   `assets`** (frames, attributes, stars, type icons, Build Deck, duel HUD):
   no engine work.
2. **Title/menu skin** (no engine work; needs art).
3. **Music, jingles, SFX** (no engine work; needs source files and id map).
4. **Engine: setting-gated audio/title/menu/card_layout** (candidate 1), so
   the above can ship as switchable themes; **event audio** (candidate 2).
5. **Portraits, scenes, card art** via `textures` packs (largest data task;
   gated on `image-remaster.md` lessons and the sourcing question).
6. **Engine, as wanted:** overlay images, settings sections, zip install.
7. **Stretch:** 3D animations, FMV, declarative effects layer.

## Status

Branch `anime-style-mod`, at `upstream/master` (`ee0f8d836`), own worktree.
Code-verified candidate list written; nothing committed. Next: pick what the
upstream issue covers.
