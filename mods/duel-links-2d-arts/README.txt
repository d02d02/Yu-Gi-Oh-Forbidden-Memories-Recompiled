Duel Links 2D Arts (v2.2)

High-resolution Duel Links style artwork for the monsters on the duel field, always facing
the camera, with an optional glow. Needs release v0.3.0 or later of YFM Re-Decomp. Does not
need 3D Monsters, and never changes a card's name.

IMPORTANT: turn 3D Monsters OFF to use this mod (Mods window). Both draw a monster on the
field and would double up, so the game will not start this mod while 3D Monsters is on.

INSTALL
Extract this zip so the "duel-links-2d-arts" folder sits inside the game's "mods" folder
(next to "3d-monsters"). Start the game, open Mods and turn on "Duel Links 2D Arts".

SETTINGS (Mods window)
  Art size (40), Height above the card (16), Glow (off), Glow colour (a list: Yellow, Gold,
  White, Red, Orange, Green, Cyan, Blue, Purple, Pink), Glow size (50), Glow pulse length (90).
  (Bob height and Bob length are there for a coming update and are off.)

CHANGING A CARD'S FIELD ART (no JSON, no tools)
1. Find the card's id: it is the number at the start of its file in artes_duel_links_fm,
   e.g. 22_SummonedSkull.tex is card 22.
2. Save your picture as a PNG with a transparent background, named after the id, in this
   mod's "art" folder:  art/22.png
3. Restart the game. Delete the file to go back to the shipped art.
Your file wins over the shipped art. Works for any card, including cards added by other
mods (ids after 722). A PNG is cropped to the card's shape by the game; for the best
quality make a .tex with prepare_art.py (art/22.tex wins over art/22.png).

CHANGING WHAT A CARD IS (spell <-> monster <-> trap, new cards)
Open this mod's mod.json and put entries in the "cards" list (it ships empty: "cards": []).
Restart the game after editing. Every key is in the game's notes/more-cards.md.

  Spell or trap -> monster (replace card 332 "Mountain"; "model" gives it a 3D model to fight with):
    { "replace": 332, "name": "Mountain Dragon", "type": "Dragon", "attribute": "Earth",
      "level": 4, "attack": 1500, "defense": 1200, "model": "Kuriboh" }

  Monster -> spell (card 12; "effect" names the disc card whose effect it takes):
    { "replace": 12, "name": "Swamp Raigeki", "type": "Magic", "effect": "Raigeki" }

  Monster -> trap (card 30):
    { "replace": 30, "name": "Swamp Bear Trap", "type": "Trap", "effect": "Bear Trap" }

  A new card, a copy of Kuriboh:
    { "copy": "Kuriboh", "name": "Test Kuriboh", "attack": 1000, "defense": 1000 }

Keep "name" in every "replace" entry, or the card's name goes back to the disc's. A new card's
id is the next free one after 722; its field art is art/<that id>.png. A monster made a
spell or trap does nothing when played without "effect"; a spell or trap made a monster has
no 3D model without "model". Nothing of this goes in your save: remove the entries (or the mod) and restart to go back.

Art by WillliTo & d02d02. The shipped pictures were prepared (trimmed, fitted to the card
art's shape, shrunk, sharpened and defringed) with prepare_art.py from the original PNGs,
into the mod's own texture files (artes_duel_links_fm/*.tex).
