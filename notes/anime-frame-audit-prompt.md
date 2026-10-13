# Audit prompt: Anime Style card-frame logic (give this whole file to a strong LLM, plus the folders listed in section 3)

## 1. Your role
You are a senior engine/mod reviewer. Audit how the "Anime Style" mod (`mods/anime-art`) chooses, loads, stores and draws a card
frame in a native recompilation of Yu-Gi-Oh! Forbidden Memories (C, a PS1 GPU emulated in software, a texture-pack layer on top).
Find every inconsistency, race, stale-state bug and mismatch between what the JSON says, what the code decides and what is drawn.
Do not rewrite the mod; report findings, ranked, each with evidence (file:line, a concrete input, the wrong output).

## 2. What the system is supposed to do
- `mods/anime-art/mod.json` has `cards` (per-card `tags`, by id or name), `settings` (switches), and `card_layout` with
  `frame_styles` (name -> picture, hand colour), `frame_for` (ordered rules: first that applies wins; each rule may name a `class`,
  a `tag`, a `setting`), `default_style`.
- A card's frame style is a pure function of (card id, its class, its tags, the settings). The same card must wear the same frame in
  the hand, on the field, in the card viewer (Triangle) and in the attack animation, at Internal 1x, 2x and 4x.
- Frame pictures are big PNGs (1024x2048 or 1024x1024). At 1x the engine draws a 2x2 grid of 255x254-texel tiles from a palette copy
  held in a PS1 texture "bank" (bank 13); above 1x it samples the PNG itself through the texture pack (bank sprites).
  The quads are rasterised when the frame is presented, not when submitted, so every frame style on screen at once needs its own
  bank slot (FRAME_SLOTS = 3 slots, least-recently-used).

## 3. Where the code is (read all of it)
Repository root: this worktree (`...\Yu-Gi-Oh-Forbidden-Memories-Recompiled-anime`), branch `adhoc-anime-art-mod` (from the upstream v0.3.0 tag).
- `mods/anime-art/` : `mod.json`, `HOWTO.txt`, `anime_art.c`, `textures/`, `hd/` (texture pack), `examples/`
- `src/pc/cards/card_layout.c` and `.h` : style resolution (`resolve_style`, `rule_applies`, `CardLayout_SetCard`, `CardLayout_StyleOf`)
- `src/pc/cards/card_layout_art.c` and `.h` : frame image cache (`image_for`), bank slots (`slot_for`, `store`), `CardLayoutArt_FrameTile`, digits, `Prewarm`
- `src/pc/cards/cards.c` and `.h` : `Cards_HasTag`, `Cards_FrameOverride`, `Cards_Class`, the JSON `cards` loader (replace entries, tags, base inheritance, ~line 1380-1560)
- `src/pc/render/texture_pack.c` and `.h` : bank sprites (`TexturePack_AddBankSpriteCrop`, `bank_image`, `bank_trim`, `BANK_SPARE`, owners, `bank_cached`), mip chain (`bank_halve`)
- `src/pc/render/soft_gpu*.c` : the bank, when quads are rasterised
- `src/game/func_80028B08.c` (the card draw: `CardLayout_DrawFrame`, SetCard at the top, frame drawn last), `src/game/duel_effect_resource_setup.c` (attack/effect objects, SetCard), `src/game/func_800283F4.c`
- `src/pc/cards/duel_ui.c` (hand frames), `src/pc/mods/` (mod loading, settings, `Mods_Setting`, JSON)
- `tools/pc/anime_art_*.py`, `anime_frame_layout.py`, `anime_frame_patch.py`, `card_frame_window.py` (build/check scripts; `FRAME_TEXELS` must match `FRAME_W/FRAME_H`)
- `notes/anime-art-mod-plan.md` (history of every bug found so far), `notes/card-catalog.csv` (card ids)

## 4. Symptoms reported (all need an explanation)
1. A tester on a clean install of the official v0.3.0 release: "when it comes to the duel between the cards they return to normal color." Screenshot:
   the activated trap is drawn in the gold monster frame plaque with the trap icon and empty ATK/DEF (should be the pink trap frame).
2. In the attack animation a card tagged `slifer` (Zombie Warrior, id 30) showed the yellow plaque of the `ra` or gold frame instead of red.
3. The attack animation was ~10x slower (162 s against 17 s for the same scripted run, headless, Internal 1x) whenever a card with a tag-chosen
   non-default style (slifer, ra) attacked. FIXED just now (see 5): the frame-image cache held 8 images, the layout has 10 distinct pictures, and
   eviction took `images[0]` and cleared the bank slots of that image, so gold and slifer evicted each other every frame (a PNG decode and a
   median cut of 1024x2048 twice a frame, 150-765 ms each). Check that the fix is complete and that nothing else can thrash.
4. Earlier fixed: trap beside its attacker wore the attacker's frame for ~4 frames (one shared bank slot); ATK/DFD digits had a pale contour.
Open question: is symptom 1/2 fully explained by the thrash plus the single-slot bug in v0.3.0's engine (the fix lives in `memories-pc.exe`, a mod zip cannot carry it), or is there a logic error in style selection, slot assignment, or texture-pack sampling left?

## 5. Changes in the working tree you should review critically
- `card_layout_art.c`: `FRAME_CACHE` 8 -> 16, eviction is now least-recently-used (was `images[0]`), `used` is a clock. Verify: stale pointers (`const FrameImage *image` held across `image_for` calls), eviction while a slot still holds that path, `slots[i].path` cleanup, int/unsigned types.
- Logging added everywhere under `MEMORIES_TRACE=card_layout` (channel `LOG_CARD_LAYOUT`): per-rule decisions, SetCard, resolve_style, DrawFrame, FrameTile, image_for, slot_for, bank_read/bank_trim/bank_free/AddBankSpriteCrop (with ms timings via `clock()`), card tag assignment at load. Check the logs are correct and not themselves costly when the channel is off.

## 6. Specific things to examine (non-exhaustive: find more)
a. `CardLayout_SetCard` is global state (`current`). Every reader (`CardLayout_FramePath`, `CardLayout_Get`, `IsSpell`) depends on the call order inside `func_80028B08`, `duel_effect_resource_setup`, hand drawing, viewer. Find any path where the style is read after another card's SetCard (the frame is drawn LAST in the object; are the other reads before it consistent?). Is SetCard called for the right id (`field_30` of the record) for the trap/defender/attacker, face-down cards, equips, ritual spells?
b. `rule_applies` and rule order: `known_ritual`/`known_fusion` need a setting; own tags `fusion`/`ritual`/`slifer`/`ra`/`obelisk` do not. Two `cards` entries for one id (392, 364 in the test setup): which wins, does `tags = tag_masks[base]` inherit wrongly, are the mod's "replace" entries touching names, stats, effects, trap data, passwords, drops, `gDuel_adwCardStats` (look at what a `replace` with only `tags` really overwrites; any side effect on the duel?).
c. The mod uses `replace` on ids 356-722 (known rituals, fusions). For a mod that does not declare stats, does the loader keep the disc's stats/effects exactly? What if a card was renamed by the FM editor (names changed, ids kept)? What if a card's type was changed (class changes the default frame)?
d. Frame slot logic: LRU over `used` with empty slots (used 0, path ""); `slot_for` choosing slot 0 by default; slot clock vs the order tiles are requested (4 tiles per card, 2 cards, plus trap/spell shown during an attack, plus the viewer). Can three or more styles be needed within one presented frame (attack + trap + viewer + hand)? What is drawn if so? `FRAME_SLOTS` vs the limit of bank pages (bits 11-14 of the texture word, bit 15 = HD_TEXT_MARK).
e. Above 1x: `TexturePack_AddBankSpriteCrop` keyed by (owner, bank, page, depth, u, v, w, h): when a slot is reassigned to another style, is the old registration replaced correctly before the next present? `bank_cached = -1`, `bank_trim` with `BANK_SPARE = 6` freeing decoded PNGs (11 MB each with mips) that are re-read later: a latent hitch? `Prewarm` builds all 10 images at start: memory and time.
f. Palette: one 256-entry palette per slot at row 254, halfword 256*slot; `FRAME_CLUT_Y` vs tile height; the clut word `(FRAME_CLUT_Y<<6)|(slot*256/16)`. Quantisation (`CardArt_IndexedImage`, median cut) differences between styles (e.g. 255 vs 256 colours, transparent index).
g. Hand frames (small) use `hand_color` palette rows; the big frame and the hand must agree (`CardLayout_StyleOf` is the one source). Any case where they differ (ritual spell green setting, `purple` alias of `fusion`)?
h. `mod.json` itself: `frame_for` order (e.g. `ritual` tag -> `ritual_monster`, class `ritual_spell` -> blue or green by setting), styles with the same picture (`fusion` and `purple`), `hand_color` of `ra` is gold and of `obelisk` blue, unknown names (`note_once` fires once per layout only: is that hiding repeated errors?), settings defaults (`ritual_monsters` 0, `fusion_monsters` 0, `hd_assets` 1) vs HOWTO.txt text, `version` fields (1.2.2) vs the CREDITS/HOWTO.
i. HD mod interplay: users run Forbidden Memories HD together (`mod.forbidden-memories-hd`, `full_bleed`, `ritual_own_frame`, `card_frames`). Both own frame textures. Which one wins on the attack screen and on the trap card? Is there an ordering (`after`, `priority -1000`) problem?
j. Build/ship consistency: `tools/pc/anime_art_check.py`, `anime_art_textures.py` produce `textures/*.png` and `hd/`; sizes (1024x2048 vs 1024x1024: trap/magic are square) vs the 2x2 grid of 255x254 tiles (aspect, `FRAME_TEXELS`), `png_w/png_h` scaling in `FrameTile` (integer division, off-by-one at tile seams).
k. Release logic: the engine fix is in the exe, the mod zip is separate. List every behaviour that needs a new exe so a tester on the official v0.3.0 exe plus our mod zip does not get a half-working mod (and how the mod could detect an old engine and degrade gracefully).

## 7. How to reproduce (a deterministic, fast rig exists)
- Headless scripted attack (no window, about 17 s at Internal 1x): `tools/pc/yfm_control.py` `Game` driven by the shared rig `attack_rig.py`
  (`C:\Users\mdahh\.claude\shared\yfm-notes\rigs\`): `python -I attack_rig.py <my card id> <unused> <tag>` with `YFM_EXECUTABLE=<memories-pc.exe>`,
  `SCALE=1|2|4`, `SHOTS=n`, `STEP=8`, `ENV_MEMORIES_TRACE=card_layout` for the log (`<out>\game.log`), `ENV_MEMORIES_DUMP_PICTURE=1` for scaled frames.
  Cards: 100 Battle Warrior (plain), 30 Zombie Warrior (slifer in the test json), 150 Akihiron (ra), 392 Metalzoa (fusion), 364 Black Luster Soldier (ritual).
- By hand: build with `play.bat` (llvm-mingw on PATH), set `mod.test-scenes=1`, hold L1 and confirm Option on the title: ten monsters face up, `mods/test-scenes/field.json`.
- A running `memories-pc.exe` locks the file: close it before `play.bat`.

## 8. Deliverable
1. A ranked list of findings (critical / major / minor / nit), each: title, file:line, why it is wrong, a concrete reproducing input, the proposed fix (diff or pseudocode).
2. A one-page map: card id -> tags -> rule -> style -> image path -> bank slot -> tile page -> clut -> texture-pack sprite, for the cases: hand, viewer, attack (attacker + defender), trap activation, ritual spell.
3. A list of what you could NOT verify from the code alone and the exact log lines (from `MEMORIES_TRACE=card_layout`) that would settle it.
4. Say explicitly which of symptoms 1-3 are explained, and which remain open.
