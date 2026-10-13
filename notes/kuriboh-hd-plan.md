# Kuriboh and the HD mod: keep the ids, or move the mod's cards past 722?

Written 2026-10-10 before any HD work. The question (user): some Kuriboh cards have no HD equivalent, some vanilla cards were
changed into something else and so carry an HD picture of the wrong card. Should the mod keep the 722 vanilla cards as they are
and introduce its own cards as new cards past id 722? This file holds the measurements, the options, a recommendation and the set-up
to do before the HD pass. **The decision is the user's; nothing has been changed for it.**

## What the data says (measured on the base Kuriboh disc against retail and `assets-hd`)

- `assets-hd` has an HD picture AND thumbnail for **all 722** retail cards. So "a card without an HD equivalent" only means a card whose
  *picture is not the retail one*.
- Kuriboh changes **38** of the 722 slots. In 4 groups:
  1. **18 slots are genuinely different cards** (new name, new picture, new stats): Multiply (338, was Mooyan Curry), Kuriboh Multiplied
     (343, Sparks), Berserk Dragon (393, Zone Eater), Dragon Master Knight (394, Steel Scorpion), Red-Eyes B. Metal Dragon (402, Monster
     Eye), Ryu-Ran (484, Ameba), Five-Headed Dragon (499, Kattapillar), Dragon Revival Ritual (666), Barrel Dragon (674), Dark Sage (676),
     Toon World (677), Mirror Force (681, was House of Adhesive Tape), Manga Ryu-Ran (682, Eatgaboon), Toon Summoned Skull (683, Bear Trap),
     Blue-Eyes Toon Dragon (684, Invisible Wire), Exodia Necross (693, Contruct of Mask), Contract with Exodia (695), A Deal with Dark Ruler
     (699). The HD picture of the retail slot is the WRONG card for all of these (it is the card that used to be there).
  2. **16 slots are the same card with a changed type** (the ritual spells became "equip" cards so that they fuse; same name, same picture,
     redrawn name plate, a blue frame kept by a `frame` entry): their HD picture is correct.
  3. **3 slots only have a redrawn name plate** (Sanga of the Thunder, Kazejin, Suijin): HD picture correct.
  4. **1 slot is a text artifact** (Kuwagata alpha written as `a`): nothing to do.
- Everything else in the 722 is retail's card, with retail's art and HD art.

## Option A: keep the ids (what is built now) plus a layered HD pack

The 38 slots keep their ids. HD is two layers: `assets-hd` for the 722 retail slots, and a small `kuriboh-hd` mod, loaded after it, whose
textures cover only what is not the retail picture (the 18 slots' pictures and thumbnails, their name plates, 4 portraits).
- Why this is the cleaner fit for *this* mod: every table that names a card (the 2664 fusions, pools, extra duelists' decks, unique drops,
  terrain lists, passwords, equip rules, the dialogue and the AI scripts in the opponent records) already uses those ids, and so does the
  save file: **a save made on the original Kuriboh disc (your memory card) has its chest by these ids**, so keeping them keeps the port and
  the disc interchangeable. The engine also has rules by id (the six attack traps are ids 681-686: Mirror Force and the three monsters in
  682-684 sit in them).
- Costs: the retail cards that were replaced no longer exist in this mod (as on the disc), and an HD pack that is loaded after `assets-hd`
  has to win for those slots (to verify: how two texture packs with the same keys resolve; `notes/modding.md` on load order).

## Option B: vanilla slots stay vanilla, the mod's 18 become cards 723 and up

- Needs: a remap old id -> new id applied to EVERY id-bearing table the importer writes (fusions, equips and the magic equip rules, pools,
  decks, drops, `unique_drops`, `card_copies`, terrain `cards`, passwords, starter decks, the dialogue's card ops, the opponents' AI
  scripts inside the archive records); the retail slot's own rows (Zone Eater, Bear Trap...) must then be hidden from pools, fusions and
  passwords or they would be playable alongside; the attack traps are fixed to ids 681-686 in the engine, so Mirror Force would need a
  `trap_thresholds` entry for a card past 722 (not supported today); saves from the original disc would not match.
- Gains: the 704 other cards keep their retail meaning, HD art and 3D models without a second pack to win a priority race; new cards carry
  their own `model`, `art` and HD art by the editor's normal "a card the mod adds" path.
- The port already supports added cards as copies of a base (`notes/more-cards.md`); that path is meant for additions, not for a disc that
  was edited in place.

## Recommendation

**Option A.** The mod is an in-place edit by construction (its tables, saves and scripts are keyed on the slots), only 18 slots carry a
different card, and a second small HD mod fixes exactly those. Option B is the right shape for a *new* mod built on the port, not for
reproducing this one exactly; it costs a full id remap and breaks save compatibility for 18 cards. If the user prefers B for the sake of
a vanilla-clean card list, do it as an importer step (remap, hide the replaced slots) and keep A as the exact mode.

## Set up before starting the HD pass (whichever option)

1. **Verify the texture priority**: in a headless duel with `assets-hd` and `kuriboh` both on, does the card picture of slot 393 come from
   `kuriboh` (its low-res art) or `assets-hd` (Zone Eater in HD)? Read `notes/modding.md` (load order, `priority`, `after`) and settle with
   a screenshot (`yfm_control.Game.shot`). The `kuriboh` mod should declare `"after": ["assets-hd"]` (or the HD mod `requires` it).
2. **Make the HD picture of each of the 18 slots**: the source is the mod's 102x96 picture the importer already extracted
   (`tmp/kuriboh/port/textures/cards/*.png`). Upscale or redraw per `tools/pc/hd_assets_pack.py`, `tools/pc/hd_recipes/` and the FM editor's
   Art tab (a picture bigger than 102x96, up to 4x, is stored as is; `art.py`, `normalize`); the thumbnail is made from the picture.
3. **Decide the frame**: `assets-hd` carries the anime frame layout (`card_layout`) with frames per card kind; the 19 ritual-like cards
   changed kind to "equip" and keep a blue `frame` colour: check `card_layout`'s `frame_for` rules do not draw them as equips.
4. **3D Monsters**: its models are keyed by the retail card; for slots 393, 394, 402, 484, 499, 674, 676, 682, 683, 684, 693 decide which
   model each new monster should wear (a card's `model` key, `notes/more-cards.md`), else it wears the old card's model.
5. **Portraits**: 4 disc duelists' faces are the mod's (Yami Bakura, Kaiba, Heishin 2nd, Duel Master K); `assets-hd` has HD portraits for the
   retail faces, so the same priority question applies and the four need HD versions.
6. **Name plates** (96x14, 4 bits): the 37 changed plates are drawn subtractively over the frame; HD name plates are not part of the picture
   packs; check how `assets-hd` treats them before redrawing.
7. Keep `python tools/pc/fm_editor import <disc>` the only producer: the HD mod is built from the import's extracted pictures and the
   user's own disc, and nothing of the ROM hack is committed.

## Decision and progress (2026-10-10, late)

**Decided with the user: option A (keep the ids) plus a second HD mod, automatic upscale first.** Done and checked:
- Texture priority: two packs that name the same image (same offset, size, depth, palette) resolve by load order. With `assets-hd` and
  `kuriboh` both on, the hand shows the mod's cards (Berserk Dragon...), not retail's (Zone Eater...); with `assets-hd` alone, retail's.
  The imported mod now also carries `"after": ["assets-hd"]` so it does not depend on the default order.
- `tools/pc/kuriboh/make_hd.py` builds `kuriboh-hd` (requires `kuriboh`, after `assets-hd` and `kuriboh`): the same 36 pack entries
  (18 pictures, 18 thumbnails) with 4x images (Lanczos + a light unsharp mask) and, with `--portraits`, the four portraits enlarged in place.
  Both packs load (log: 36 + 36 images, 72). A real window shot at Internal 2x (`MEMORIES_WINDOW_SHOT` at a frame found in a first run)
  shows the card picture smooth with `kuriboh-hd` and pixelated without it.
- `tools/pc/kuriboh/build_kuriboh.py <disc> --game <retail> --install` does import + HD layer + install into the game's user mods folder
  (it asks `disc.user_dir()`, so a OneDrive-redirected Documents is right).

Name plates: nothing to build. With HD text on (`hd_text=1`, the default in the user's settings) the port sets every card's plate anew from
its name at the console's resolution (`hd_text.c` HdText_Title, `CardArt_TitlePicture`), so the mod's 37 imported 96x14 plates are
redrawn crisp at Internal 4x (checked 2026-10-10: Berserk Dragon, card 393). Not done: an HD portrait check at Internal 4x in a real
window (the user tests it by hand). 3D Monsters models are out of scope for this branch.

## Better pictures than an enlargement (2026-10-10)

How `assets-hd` got its quality (`notes/image-remaster.md`): **not by an algorithm**. A blanket AI upscale (Upscayl high-fidelity) of the
card art was judged "filtered rather than redrawn" and not published; the card pictures of the HD mod are a set of *redrawn HD images*, one a
card, placed by `tools/pc/hd_assets_pack.py` (`cards/<n>.png`, the thumbnail cut from it where the game cuts its own,
`tools/pc/hd_recipes/thumb_crops.json`). Only the Build Deck screen used a model (Real-ESRGAN x4plus mixed 60 % with Lanczos and
back-projected so each 4x4 block keeps the game's colors; few-color UI through xBR), and that needs `ffmpeg` and Upscayl/`realesrgan-ncnn-vulkan`,
neither installed here.
So the equivalent for Kuriboh's 18 cards is: **a good picture per card, fitted to the frame**. `make_hd.py --sources <folder>` does the
fitting (crop to 102:96 from the middle, a little high; 408x384; thumbnail from the game's crop for that slot); a card without a file there
keeps the Lanczos enlargement. The folder is `tmp/kuriboh/hd-source/` (README there lists the 18 slots); `build_kuriboh.py ... --sources <folder> --install`
rebuilds and installs. The pictures are the user's own files (an official artwork found online, or the mod's art), never committed.

## Artwork fetched (2026-10-10)

`python tools/pc/kuriboh/fetch_artwork.py tmp/kuriboh/hd-source` asks Yugipedia's API for the 512x512 Master Duel artwork
(`<Card>-MADU-EN-VG-artwork.png`) of each real card among the 18 slots and saves it as `<slot>.png` (not committed; Konami's art for the user's
own use). **16 of the 18 found**; the two with no real card keep the enlargement: 343 Kuriboh Multiplied and 666 Dragon Revival Ritual.
`build_kuriboh.py <disc> --game <retail> --sources tmp/kuriboh/hd-source --install` builds and installs them (checked at Internal 2x: Mirror Force's
picture is the crisp artwork, the mod's own art pixelated without the layer). The user's call on 343 and 666 (and on any card whose artwork they
prefer to change: drop their own `<slot>.png` in the folder).

## AI candidates, side by side, for the user to choose (2026-10-10, night)

Tool installed: **realesrgan-ncnn-vulkan** (Real-ESRGAN 20220424, Windows) in `tmp/pc/tools/realesrgan/` (that folder is the dev worktree's
`tmp/pc/tools`, shared by a junction; git-ignored); it runs on this machine's Intel Iris Xe through Vulkan, about 1.5 s a picture. Its path needs
absolute Windows paths and `-m <models dir>`.
- `tools/pc/kuriboh/ai_upscale.py <imported mod> <out>`: for each of the 18 changed pictures writes `raw/` (realesrgan-x4plus-anime alone),
  `mix/` (60 % model + Lanczos, back-projected) and `project/` = **the HD mod's own method** (`tools/pc/hd_screen_pack.py`: realesrgan-x4plus on the
  picture padded by a mirrored border, 60 % model, 40 % Lanczos, 6 rounds of back-projection). The net artwork also went through the anime model
  (`net_ai/`, fitted to the frame at 2x the game's size, enlarged 4x, reduced to 408x384).
- `tools/pc/kuriboh/compare_art.py <mod> <ai> <net sources> <out>` makes `compare_1..3.png` (six cards each): mod art, plain enlargement, HD-mod
  method, anime model, real artwork, real artwork + AI. Under `tmp/kuriboh/compare/`. **The user chooses per card**; whichever folder they pick
  (`ai-candidates/project`, `raw`, `net_ai`, or `hd-source` = the real artwork) is passed as `make_hd.py --sources <folder>` / `build_kuriboh.py --sources`;
  they can also mix by copying chosen files into one folder named `<card id>.png`.
- Observations: the anime model alone gives the cleanest line work but changes colors; the HD-mod method keeps the mod's colors; the real
  artwork has its own (truer) colors and a slightly different framing on some cards.

## Chosen and built (2026-10-10, night): net artwork + AI where there is one, the anime model otherwise

The user chose: real artwork through the AI model when there is real artwork (16 cards: `ai-candidates/net_ai/`), the anime model on the mod's own art for
343 and 666 (`ai-candidates/raw/`); both are collected in `tmp/kuriboh/hd-chosen/` and built with
`build_kuriboh.py <disc> --game <retail> --sources tmp/kuriboh/hd-chosen --install`.

**Mod id trap (found while checking the anime frame):** the folder `mods/assets-hd` in the user's Documents holds the mod whose id is
**`forbidden-memories-hd`** ("Forbidden Memories HD"). Settings and `after`/`requires` use the id, not the folder name:
`mod.forbidden-memories-hd.full_bleed=1` is the anime frame; `kuriboh` and `kuriboh-hd` now declare `after: ["forbidden-memories-hd", ...]`.
(My earlier `mod.assets-hd...` settings and `after: ["assets-hd"]` named nothing; the priority test had passed on the default order.)
Checked at Internal 2x with the anime frame on: a new monster (Berserk Dragon) gets a gold anime frame with the layer's smoother picture and its
ATK/DFD; a new spell (Multiply) and the ritual-like cards (type equip) get the green frame; the layer applies inside the anime layout too.

## Questions for the user

- A or B? (Recommendation: A.)
- Is a save from the original Kuriboh disc something you want to load in the port? (It argues for A.)
- For the 18 new cards' HD art: an automatic upscale of the mod's pictures is enough, or do you want redrawn art?
